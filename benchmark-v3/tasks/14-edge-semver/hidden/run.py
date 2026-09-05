#!/usr/bin/env python3
"""Hidden runner for 14-edge-semver. Continuous score (0-100).

Curated golden cases spanning comparators, caret/tilde, x-ranges, hyphen ranges,
OR/AND, prerelease PRECEDENCE, and npm's prerelease MATCH rule (a prerelease version
only satisfies a range if a comparator names the same [maj,minor,patch] AND has a
prerelease). The last two are where implementations — and frontier models — go wrong.

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error).
"""
import importlib.util
import json
import sys

# (version, range, expected, tag, weight)
CASES = [
    ("1.2.3", "1.2.3", True, "basic", 1), ("1.2.4", "1.2.3", False, "basic", 1),
    ("1.2.3", ">=1.2.0", True, "basic", 1), ("1.1.9", ">=1.2.0", False, "basic", 1),
    ("1.2.3", ">1.2.3", False, "basic", 1), ("2.0.0", "<2.0.0", False, "basic", 1),
    ("1.9.9", "<2.0.0", True, "basic", 1),

    ("1.5.0", "^1.2.3", True, "caret", 1), ("2.0.0", "^1.2.3", False, "caret", 1),
    ("1.2.2", "^1.2.3", False, "caret", 1), ("0.2.5", "^0.2.3", True, "caret", 1),
    ("0.3.0", "^0.2.3", False, "caret", 1), ("0.0.3", "^0.0.3", True, "caret", 1),
    ("0.0.4", "^0.0.3", False, "caret", 1),

    ("1.2.9", "~1.2.3", True, "tilde", 1), ("1.3.0", "~1.2.3", False, "tilde", 1),
    ("1.2.5", "~1.2", True, "tilde", 1), ("1.5.0", "~1", True, "tilde", 1),
    ("2.0.0", "~1", False, "tilde", 1),

    ("1.2.9", "1.2.x", True, "xrange", 1), ("1.3.0", "1.2.x", False, "xrange", 1),
    ("1.9.9", "1.x", True, "xrange", 1), ("2.0.0", "1.x", False, "xrange", 1),
    ("5.5.5", "*", True, "xrange", 1),

    ("1.5.0", "1.2.3 - 2.3.4", True, "hyphen", 1), ("2.3.5", "1.2.3 - 2.3.4", False, "hyphen", 1),
    ("1.2.3", "1.2.3 - 2.3.4", True, "hyphen", 1), ("2.3.4", "1.2.3 - 2.3.4", True, "hyphen", 1),

    ("2.5.0", "^1.0.0 || ^2.0.0", True, "or", 1), ("3.0.0", "^1.0.0 || ^2.0.0", False, "or", 1),
    ("1.5.0", ">=1.2.0 <1.6.0", True, "and", 1), ("1.6.0", ">=1.2.0 <1.6.0", False, "and", 1),

    # prerelease PRECEDENCE (range carries a prerelease at the same core -> match-rule ok)
    ("1.0.0-alpha", ">=1.0.0-alpha", True, "pre_prec", 2),
    ("1.0.0-alpha.1", ">1.0.0-alpha", True, "pre_prec", 2),
    ("1.0.0-alpha.beta", ">1.0.0-alpha.1", True, "pre_prec", 2),
    ("1.0.0-beta.2", ">1.0.0-beta", True, "pre_prec", 2),
    ("1.0.0-beta.11", ">1.0.0-beta.2", True, "pre_prec", 2),
    ("1.0.0-rc.1", ">1.0.0-beta.11", True, "pre_prec", 2),
    ("1.0.0-alpha.1", ">1.0.0-alpha.beta", False, "pre_prec", 2),  # numeric < alphanumeric

    # prerelease MATCH rule (npm) — the hardest
    ("1.0.0-alpha", "<1.0.0", False, "pre_match", 3),       # range has no pre at that core
    ("1.2.4-alpha", "^1.2.3", False, "pre_match", 3),       # no pre at 1.2.4 in range
    ("3.0.0-alpha", "^1.2.3", False, "pre_match", 3),       # different core + out of range
    ("1.2.3-beta.2", ">=1.2.3-beta.1 <1.2.4", True, "pre_match", 3),  # comparator has pre at core
    ("1.2.3", "^1.2.3", True, "pre_match", 2),              # plain release always fine
    ("1.2.3-rc.1", ">=1.2.3-rc.1", True, "pre_match", 3),
]


def load(path):
    spec = importlib.util.spec_from_file_location("cand_semver", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    m = load(sys.argv[1])
    by = {}
    passW = totW = 0.0
    for ver, rng, exp, tag, w in CASES:
        totW += w
        d = by.setdefault(tag, [0, 0])
        d[1] += w
        ok = False
        try:
            ok = bool(m.satisfies(ver, rng)) == exp
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
