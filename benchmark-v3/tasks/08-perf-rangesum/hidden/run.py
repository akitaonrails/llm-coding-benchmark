#!/usr/bin/env python3
"""Hidden runner for 08-perf-rangesum. Continuous score (0-100).

Correctness is a GATE (checked on small random inputs + a big input); the spectrum
is SPEED, measured by timing the candidate against the reference ON THIS MACHINE in
THIS run (so the score is hardware-independent). A correct-but-O(N*Q) solution is
capped by a hard wall-clock budget and lands near 0; matching the reference's
efficiency scores ~100; something in between lands in between.

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error on import failure).
"""
import importlib.util
import json
import random
import signal
import sys
from pathlib import Path
from time import perf_counter

K = 1.4           # candidate within 1/K of reference speed => full marks
BUDGET = 20.0     # hard wall-clock cap for the big perf call (seconds)
BIG_N = 120000    # sized so the reference runs ~0.15s (stable timing, low jitter)
BIG_Q = 120000


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def brute(events, queries):
    return [sum(v for ts, v in events if lo <= ts <= hi) for lo, hi in queries]


class _Timeout(Exception):
    pass


def main():
    cand_path = sys.argv[1]
    ref_path = Path(__file__).resolve().parent.parent / "reference" / "rangesum.py"
    try:
        cand = load(cand_path, "cand_rangesum")
        ref = load(str(ref_path), "ref_rangesum")
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"load_error": f"import failed: {e}", "score": None}))
        return

    rng = random.Random(20260904)

    # ---- correctness on small random + edge inputs (the gate) ----
    small_total = small_pass = 0
    cases = []
    for _ in range(24):
        n = rng.randint(0, 200)
        ev = [(rng.randint(-50, 50), rng.randint(-1000, 1000)) for _ in range(n)]
        qs = [tuple(sorted((rng.randint(-60, 60), rng.randint(-60, 60)))) for _ in range(rng.randint(1, 40))]
        cases.append((ev, qs))
    cases.append(([], [(0, 10), (5, 5)]))                       # empty events
    cases.append(([(5, 3), (5, 7), (5, -2)], [(5, 5), (4, 6)]))  # duplicate ts
    cases.append(([(1, 10), (2, 20)], [(2, 1)]))                # hi < lo -> 0
    cases.append(([(-3, 100)], [(-5, -1), (-3, -3), (0, 9)]))    # negatives
    for ev, qs in cases:
        small_total += 1
        try:
            if cand.solve([tuple(x) for x in ev], [tuple(q) for q in qs]) == brute(ev, qs):
                small_pass += 1
        except Exception:  # noqa: BLE001
            pass

    # ---- big input: correctness + timed perf ----
    events = [(rng.randint(0, 10 ** 9), rng.randint(-1000, 1000)) for _ in range(BIG_N)]
    queries = []
    for _ in range(BIG_Q):
        a, b = rng.randint(0, 10 ** 9), rng.randint(0, 10 ** 9)
        queries.append((min(a, b), max(a, b)))

    # reference time: best of 3 (trusted, fast)
    ref_out = None
    ref_time = float("inf")
    for _ in range(3):
        t0 = perf_counter()
        ref_out = ref.solve(list(events), list(queries))
        ref_time = min(ref_time, perf_counter() - t0)

    # candidate time: hard-capped by SIGALRM; best-of-3 when it's fast (kills jitter)
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(_Timeout()))

    def timed_call():
        signal.setitimer(signal.ITIMER_REAL, BUDGET)
        t0 = perf_counter()
        try:
            out = cand.solve(list(events), list(queries))
            return out, perf_counter() - t0, False
        except _Timeout:
            return None, BUDGET, True
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    try:
        cand_out, cand_time, timed_out = timed_call()
        if not timed_out and cand_time < 3.0:      # fast enough to repeat cheaply
            for _ in range(2):
                _, t, _to = timed_call()
                if not _to:
                    cand_time = min(cand_time, t)
    except Exception as e:  # noqa: BLE001
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps({"load_error": f"candidate raised on big input: {e}", "score": None}))
        return

    big_wrong = (not timed_out) and (cand_out != ref_out)
    ratio = (ref_time * K) / cand_time if cand_time > 0 else 0.0
    perf = round(100.0 * max(0.0, min(1.0, ratio)), 1)

    if small_pass < small_total or big_wrong:
        frac = (small_pass / small_total) * (0.4 if big_wrong else 1.0)
        score = round(30.0 * frac, 1)
    else:
        score = perf

    print(json.dumps({
        "score": score,
        "breakdown": {
            "small": f"{small_pass}/{small_total}",
            "big_correct": (None if timed_out else (not big_wrong)),
            "timed_out": timed_out,
            "ref_time_s": round(ref_time, 4),
            "cand_time_s": round(cand_time, 4),
            "speed_ratio_ref_over_cand": round((ref_time / cand_time) if cand_time else 0, 3),
            "perf": perf,
        },
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"load_error": f"runner crashed: {e}", "score": None}))
