#!/usr/bin/env python3
"""Hidden runner for 09-sabotage-recover. Continuous score (0-100).

The candidate inherited a tampered `store.py`. Several subtle defects were injected
across correctness / security / performance / state classes; the visible smoke test
still passes. Score = weighted fraction of adversarial checks passed. Defect checks
are weighted heavily; regression checks (behaviour that was already fine) guard
against a model that "fixes" things by rewriting and breaking them.

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error).
"""
import importlib.util
import json
import signal
import sys
from time import perf_counter


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Timeout(Exception):
    pass


def main():
    m = load(sys.argv[1], "cand_store")

    # (tag, weight, thunk->bool). Defect checks weight 2; the perf defect 4;
    # regression/"still works" checks weight 1.
    checks = []

    def chk(tag, weight, fn):
        checks.append((tag, weight, fn))

    # --- pagination: off-by-one (page is 1-indexed) ---
    chk("pag", 2, lambda: m.paginate(list(range(10)), 1, 5) == [0, 1, 2, 3, 4])
    chk("pag", 2, lambda: m.paginate(list(range(10)), 2, 5) == [5, 6, 7, 8, 9])
    chk("pag", 2, lambda: m.paginate(list(range(7)), 3, 3) == [6])
    chk("pag", 1, lambda: m.paginate(list("abcdef"), 1, 2) == ["a", "b"])  # regression-ish

    # --- security: open redirect (must be EXACT host, not substring/suffix) ---
    chk("sec", 2, lambda: m.host_allowed("https://evil.com/?next=good.com", {"good.com"}) is False)
    chk("sec", 2, lambda: m.host_allowed("https://good.com.evil.com/x", {"good.com"}) is False)
    chk("sec", 2, lambda: m.host_allowed("https://notgood.com/", {"good.com"}) is False)
    chk("sec", 2, lambda: m.host_allowed("https://sub.good.com/", {"good.com"}) is False)
    chk("sec", 1, lambda: m.host_allowed("https://good.com/path", {"good.com", "cdn.net"}) is True)
    chk("sec", 1, lambda: m.host_allowed("http://GOOD.COM/x", {"good.com"}) is True)  # case

    # --- performance: dedupe must not be quadratic (budget on large input) ---
    def perf_ok():
        big = [i % 20000 for i in range(400000)]
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(_Timeout()))
        signal.setitimer(signal.ITIMER_REAL, 2.5)
        try:
            t0 = perf_counter()
            r = m.dedupe(big)
            dt = perf_counter() - t0
        except _Timeout:
            return False
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        return r == list(range(20000)) and dt < 2.5
    chk("perf", 4, perf_ok)
    chk("perf", 1, lambda: m.dedupe([3, 1, 3, 2, 1]) == [3, 1, 2])  # correctness/regression

    # --- merge_intervals: touching intervals must merge ---
    chk("merge", 2, lambda: m.merge_intervals([(1, 2), (2, 3)]) == [(1, 3)])
    chk("merge", 2, lambda: m.merge_intervals([(1, 4), (4, 5), (5, 9)]) == [(1, 9)])
    chk("merge", 1, lambda: m.merge_intervals([(1, 5), (2, 3)]) == [(1, 5)])   # nested (regression)
    chk("merge", 1, lambda: m.merge_intervals([(1, 2), (3, 4)]) == [(1, 2), (3, 4)])  # disjoint

    # --- parse_amount: half-up, no binary-float truncation ---
    chk("amount", 2, lambda: m.parse_amount("0.29") == 29)
    chk("amount", 2, lambda: m.parse_amount("1.005") == 101)
    chk("amount", 2, lambda: m.parse_amount("8.70") == 870)
    chk("amount", 1, lambda: m.parse_amount("12.34") == 1234)  # regression

    # --- record_event: mutable-default state leak across calls ---
    def mutdef_ok():
        a = m.record_event("x")
        b = m.record_event("y")
        return a == ["x"] and b == ["y"]
    chk("mutdef", 3, mutdef_ok)
    chk("mutdef", 1, lambda: m.record_event("z", []) == ["z"])  # explicit list (regression)

    by = {}
    passW = totW = 0.0
    for tag, w, fn in checks:
        totW += w
        d = by.setdefault(tag, [0, 0])
        d[1] += w
        ok = False
        try:
            ok = bool(fn())
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            passW += w
            d[0] += w
    score = round(100.0 * passW / totW, 1) if totW else 0.0
    print(json.dumps({
        "score": score,
        "breakdown": {k: f"{v[0]}/{v[1]}" for k, v in by.items()},
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"load_error": f"runner crashed: {e}", "score": None}))
