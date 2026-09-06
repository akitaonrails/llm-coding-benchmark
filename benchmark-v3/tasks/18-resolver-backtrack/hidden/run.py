#!/usr/bin/env python3
"""Hidden runner for 18-resolver-backtrack. Continuous score (0-100).

Grounded, observation-heavy: dependency resolution (what npm/pip/bundler do). Greedy
"pick newest" is a natural but WRONG approach; correct resolution needs backtracking.
Each instance is labeled SAT/UNSAT by an INDEPENDENT brute-force oracle, and the
candidate's output is VALIDATED against every transitive constraint (for SAT it must
return a valid assignment; for UNSAT it must return None). Backtracking-required and
conflict instances are weighted highest.

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error).
"""
import importlib.util
import itertools
import json
import sys


def load(path):
    spec = importlib.util.spec_from_file_location("cand_resolver", path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _parse(v):
    return tuple(int(x) for x in v.split("."))


def _sat(version, spec):
    spec = spec.strip()
    if spec in ("*", ""):
        return True
    v = _parse(version)
    if spec.startswith(">="):
        return v >= _parse(spec[2:].strip())
    if spec.startswith("^"):
        lo = _parse(spec[1:].strip())
        if v < lo:
            return False
        if lo[0] > 0:
            return v[0] == lo[0]
        if lo[1] > 0:
            return v[0] == 0 and v[1] == lo[1]
        return v[0] == 0 and v[1] == 0 and v[2] == lo[2]
    return v == _parse(spec)


def valid(registry, root, assign):
    """True iff `assign` (dict name->version) satisfies the entire root closure."""
    if not isinstance(assign, dict):
        return False
    pending = [tuple(r) for r in root]
    seen = set()
    while pending:
        name, spec = pending.pop()
        if name not in assign:
            return False
        v = assign[name]
        if v not in registry.get(name, {}):
            return False
        if not _sat(v, spec):
            return False
        if name in seen:
            continue
        seen.add(name)
        for d, s in registry[name][v]:
            pending.append((d, s))
    return True


def oracle_sat(registry, root):
    names = list(registry)
    vers = [list(registry[n]) for n in names]
    for combo in itertools.product(*vers):
        if valid(registry, root, dict(zip(names, combo))):
            return True
    return False


def R(**pkgs):
    # R(A={"1.0.0":[], "2.0.0":[["B","^2.0.0"]]}, ...)
    return dict(pkgs)


# ---- instances: (name, registry, root, weight) ----
INSTANCES = []


def inst(tag, weight, registry, root):
    INSTANCES.append((tag, weight, registry, root))


# simple SAT (greedy works)
inst("simple", 1, R(A={"1.0.0": [], "1.1.0": []}), [["A", "^1.0.0"]])
inst("simple", 1, R(A={"1.0.0": [["B", "^1.0.0"]]}, B={"1.0.0": [], "1.2.0": []}), [["A", "1.0.0"]])

# diamond SAT (A->B,C ; B->D^1 ; C->D^1)
inst("diamond", 2, R(
    A={"1.0.0": [["B", "*"], ["C", "*"]]},
    B={"1.0.0": [["D", "^1.0.0"]]},
    C={"1.0.0": [["D", "^1.0.0"]]},
    D={"1.0.0": [], "1.5.0": []},
), [["A", "*"]])

# BACKTRACKING-REQUIRED SAT: newest A (2.0.0) needs B^2 which needs D^2, but root also
# needs C which needs D^1 -> newest A is a dead end; A 1.0.0 works. Greedy picks A 2.0.0.
inst("backtrack", 3, R(
    A={"1.0.0": [["D", "^1.0.0"]], "2.0.0": [["D", "^2.0.0"]]},
    C={"1.0.0": [["D", "^1.0.0"]]},
    D={"1.0.0": [], "2.0.0": []},
), [["A", "*"], ["C", "*"]])

# BACKTRACKING via shared dep newest-first trap
inst("backtrack", 3, R(
    A={"1.0.0": [["X", "^1.0.0"]], "1.1.0": [["X", "^2.0.0"]]},
    B={"1.0.0": [["X", "^1.0.0"]]},
    X={"1.0.0": [], "2.0.0": []},
), [["A", "*"], ["B", "*"]])

# deep backtracking (newest of two independently-newest choices conflict)
inst("backtrack", 3, R(
    A={"1.0.0": [["Z", "1.0.0"]], "2.0.0": [["Z", "2.0.0"]]},
    B={"1.0.0": [["Z", "1.0.0"]], "2.0.0": [["Z", "3.0.0"]]},
    Z={"1.0.0": [], "2.0.0": [], "3.0.0": []},
), [["A", "*"], ["B", "*"]])

# UNSAT: diamond conflict, no D satisfies both ^1 and ^2
inst("unsat", 3, R(
    A={"1.0.0": [["B", "*"], ["C", "*"]]},
    B={"1.0.0": [["D", "^1.0.0"]]},
    C={"1.0.0": [["D", "^2.0.0"]]},
    D={"1.0.0": [], "2.0.0": []},
), [["A", "*"]])

# UNSAT: required version doesn't exist
inst("unsat", 2, R(A={"1.0.0": []}), [["A", ">=2.0.0"]])

# UNSAT: transitive dead end (only version of A needs B^3, no such B)
inst("unsat", 2, R(A={"1.0.0": [["B", "^3.0.0"]]}, B={"1.0.0": [], "2.0.0": []}), [["A", "*"]])

# SAT requiring an older pick of a transitive dep
inst("backtrack", 3, R(
    A={"1.0.0": [["B", "*"]]},
    B={"1.0.0": [["C", "^1.0.0"]], "2.0.0": [["C", "^9.0.0"]]},
    C={"1.0.0": [], "2.0.0": []},
), [["A", "*"]])


def main():
    m = load(sys.argv[1])
    by = {}
    passW = totW = 0.0
    for tag, w, registry, root in INSTANCES:
        totW += w
        d = by.setdefault(tag, [0, 0])
        d[1] += w
        want_sat = oracle_sat(registry, root)
        ok = False
        try:
            out = m.resolve({k: {vv: [list(x) for x in deps] for vv, deps in v.items()}
                             for k, v in registry.items()},
                            [list(r) for r in root])
            if want_sat:
                ok = valid(registry, root, out)      # must return a VALID assignment
            else:
                ok = out is None                      # must correctly report UNSAT
        except Exception:
            ok = False
        if ok:
            passW += w
            d[0] += w
    score = round(100.0 * passW / totW, 1) if totW else 0.0
    print(json.dumps({"score": score, "breakdown": {k: f"{v[0]}/{v[1]}" for k, v in by.items()}}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"load_error": f"runner crashed: {e}", "score": None}))
