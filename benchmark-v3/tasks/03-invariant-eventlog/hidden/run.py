#!/usr/bin/env python3
"""Hidden grader for task 03. NEVER shipped to the model workspace.
Usage: run.py /path/to/candidate/projection.py  -> standard JSON contract."""
import importlib.util, json, os, random, sys


def load(path):
    spec = importlib.util.spec_from_file_location("candidate_projection", path)
    assert spec and spec.loader, f"cannot import {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Projection


def canonical(delivered):
    """Balance from the longest contiguous distinct prefix of `delivered` (arrival order)."""
    by_seq = {}
    for e in delivered:
        by_seq.setdefault(e["seq"], e)
    bal, s = 0, 0
    while s in by_seq:
        e = by_seq[s]
        if e["type"] == "open":
            bal = 0
        elif e["type"] == "deposit":
            bal += e["amount"]
        elif e["type"] == "withdraw" and bal >= e["amount"]:
            bal -= e["amount"]
        s += 1
    return bal


def ev(seq, t, amt=0):
    return {"seq": seq, "type": t, "amount": amt}


def run_case(Projection, log, schedule):
    """Deliver events (by seq index into `log`, with possible dups) in order;
    after each delivery, candidate.balance() must equal the canonical prefix balance."""
    p = Projection()
    delivered = []
    for seq in schedule:
        e = log[seq]
        p.apply(dict(e))  # copy so candidate can't be graded via aliasing
        delivered.append(e)
        want = canonical(delivered)
        got = p.balance()
        if got != want:
            return False, f"after delivering seqs {[x['seq'] for x in delivered]}: want {want} got {got}"
    return True, "ok"


LOG_A = [ev(0, "open"), ev(1, "deposit", 100), ev(2, "withdraw", 70), ev(3, "withdraw", 50)]
# order matters: withdraw before its funding deposit in seq order -> rejected
LOG_B = [ev(0, "open"), ev(1, "withdraw", 50), ev(2, "deposit", 100), ev(3, "withdraw", 30)]

cases = [
    ("in_order", "base", LOG_A, [0, 1, 2, 3]),
    ("single_open", "base", LOG_A, [0]),
    ("reversed", "edge", LOG_A, [3, 2, 1, 0]),
    ("shuffled", "edge", LOG_A, [2, 0, 3, 1]),
    ("duplicates", "edge", LOG_A, [0, 0, 1, 1, 2, 3, 2]),
    ("gap_then_fill", "edge", LOG_A, [0, 1, 3, 2]),
    ("gap_query_before_fill", "edge", LOG_A, [0, 3, 1]),
    ("overdraw_order_matters", "edge", LOG_B, [0, 2, 1, 3]),
    ("overdraw_reversed", "edge", LOG_B, [3, 2, 1, 0]),
    ("dup_after_applied", "edge", LOG_A, [0, 1, 2, 3, 1, 0]),
]

# variant: replay + large shuffled with dups + multi-gap interleave
big = [ev(0, "open")]
bal = 0
for s in range(1, 400):
    if s % 3 == 0 and bal >= 5:
        big.append(ev(s, "withdraw", 5)); bal -= 5
    else:
        big.append(ev(s, "deposit", 10)); bal += 10
rng = random.Random(1234)
sched = []
for s in range(400):
    sched.append(s)
    if rng.random() < 0.3:
        sched.append(rng.randint(0, s))  # duplicate an already/again seq
rng.shuffle(sched)
cases.append(("large_shuffled_dups", "variant", big, sched))
cases.append(("replay_twice", "variant", LOG_A, [2, 0, 3, 1, 2, 0, 3, 1]))
cases.append(("multi_gap_interleave", "variant", LOG_B, [3, 1, 0, 3, 2]))

try:
    Projection = load(os.path.abspath(sys.argv[1]))
except Exception as e:  # noqa: BLE001
    print(json.dumps({"load_error": f"{type(e).__name__}: {e}", "results": []}))
    sys.exit(0)

results = []
for name, tag, log, schedule in cases:
    try:
        ok, detail = run_case(Projection, log, schedule)
    except Exception as e:  # noqa: BLE001
        ok, detail = False, f"{type(e).__name__}: {e}"
    results.append({"name": name, "tag": tag, "pass": ok, "detail": detail})

print(json.dumps({"load_error": None, "results": results}))
