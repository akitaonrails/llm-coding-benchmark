#!/usr/bin/env python3
"""Hidden runner for 15-observation-median. Continuous score (0-100).

Correctness is a GATE (small random inputs checked against a brute-force oracle + the
big input against the reference). The spectrum is SPEED: an O(n^2) solution is correct
but capped by a wall-clock budget and scores near 0; the O(n log n) observation scores
~100. A wrong median transform fails correctness outright.

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error).
"""
import importlib.util
import json
import random
import signal
import sys
from pathlib import Path
from time import perf_counter

K = 1.4
BUDGET = 15.0
BIG_N = 120000


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def brute(a, k):
    n = len(a); c = 0
    for i in range(n):
        for j in range(i, n):
            sub = sorted(a[i:j + 1])
            if sub[(len(sub) - 1) // 2] >= k:
                c += 1
    return c


class _T(Exception):
    pass


def main():
    cand = load(sys.argv[1], "cand_median")
    ref = load(str(Path(__file__).resolve().parent.parent / "reference" / "median.py"), "ref_median")
    rng = random.Random(20260905)

    # ---- correctness gate: small random vs brute force ----
    small_total = small_pass = 0
    cases = []
    for _ in range(40):
        n = rng.randint(1, 40)
        a = [rng.randint(-5, 5) for _ in range(n)]
        k = rng.randint(-6, 6)
        cases.append((a, k))
    cases += [([5], 5), ([1, 2, 3, 4, 5], 3), ([5, 5, 5], 5), ([-3, -3], 0),
              ([1] * 10, 1), ([1] * 10, 2)]
    for a, k in cases:
        small_total += 1
        try:
            if cand.count_subarrays_median_at_least(list(a), k) == brute(a, k):
                small_pass += 1
        except Exception:
            pass
    correct_small = small_pass == small_total

    # ---- big input: correctness vs reference + timed perf ----
    big = [rng.randint(-1000, 1000) for _ in range(BIG_N)]
    kbig = 0
    ref_ans = None
    ref_time = float("inf")
    for _ in range(3):
        t0 = perf_counter()
        ref_ans = ref.count_subarrays_median_at_least(list(big), kbig)
        ref_time = min(ref_time, perf_counter() - t0)

    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(_T()))
    signal.setitimer(signal.ITIMER_REAL, BUDGET)
    timed_out = False
    cand_ans = None
    t0 = perf_counter()
    try:
        cand_ans = cand.count_subarrays_median_at_least(list(big), kbig)
        cand_time = perf_counter() - t0
    except _T:
        cand_time = BUDGET
        timed_out = True
    except Exception as e:  # noqa: BLE001
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps({"load_error": f"candidate raised on big input: {e}", "score": None}))
        return
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

    big_correct = (not timed_out) and (cand_ans == ref_ans)
    ratio = (ref_time * K) / cand_time if cand_time > 0 else 0.0
    perf = round(100.0 * max(0.0, min(1.0, ratio)), 1)

    if not correct_small or (not timed_out and not big_correct):
        # wrong answer: capped low, proportional to small correctness
        score = round(25.0 * small_pass / small_total, 1)
    else:
        score = perf   # correct; graded on speed (timed_out -> ~0)

    print(json.dumps({
        "score": score,
        "breakdown": {
            "small": f"{small_pass}/{small_total}",
            "big_correct": (None if timed_out else big_correct),
            "timed_out": timed_out,
            "ref_time_s": round(ref_time, 4),
            "cand_time_s": round(cand_time, 4),
            "perf": perf,
        },
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"load_error": f"runner crashed: {e}", "score": None}))
