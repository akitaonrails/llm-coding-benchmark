#!/usr/bin/env python3
"""Hidden runner for task 04 (Rust). Builds the candidate main.rs with rustc -O,
runs adversarial cases (with a hard wall-time gate on the large perf case), and
prints the standard JSON contract. Invoked as: harness.py <candidate main.rs>."""
import bisect, json, os, random, subprocess, sys, tempfile


def emit(load_error, results=None):
    print(json.dumps({"load_error": load_error, "results": results or []}))
    sys.exit(0)


def expected(sessions, queries):
    starts = sorted(s for s, _ in sessions)
    ends = sorted(e for _, e in sessions)
    out = []
    for t in queries:
        out.append(bisect.bisect_right(starts, t) - bisect.bisect_left(ends, t))
    return out


def make_input(sessions, queries):
    parts = [str(len(sessions))]
    parts += [f"{s} {e}" for s, e in sessions]
    parts.append(str(len(queries)))
    parts += [str(t) for t in queries]
    return "\n".join(parts) + "\n"


def cases():
    yield ("example", "base", [(1, 5), (2, 8), (10, 12)], [0, 2, 8, 11], 5.0)
    yield ("empty_sessions", "base", [], [0, -5, 100], 5.0)
    yield ("no_queries", "base", [(1, 2), (3, 4)], [], 5.0)
    yield ("single", "base", [(5, 10)], [4, 5, 7, 10, 11], 5.0)
    yield ("point_interval", "edge", [(5, 5)], [4, 5, 6], 5.0)
    yield ("boundaries", "edge", [(0, 10), (10, 20)], [0, 10, 20, 21, -1], 5.0)
    yield ("duplicates", "edge", [(1, 100)] * 50, [50, 0, 100], 5.0)
    yield ("negatives_large", "edge",
           [(-10**12, 10**12), (-5, -5)], [-10**12, -5, 0, 10**12, 10**12 + 1], 5.0)
    yield ("adjacent_and_nested", "edge",
           [(1, 10), (2, 3), (3, 4), (5, 5)], [3, 4, 5, 11], 5.0)
    r = random.Random(7)
    ses = [(a, a + r.randint(0, 50)) for a in (r.randint(-1000, 1000) for _ in range(500))]
    qs = [r.randint(-1100, 1100) for _ in range(500)]
    yield ("random_medium", "edge", ses, qs, 5.0)
    # --- performance gate: N=Q=200000, hard 3s wall-time (O(N*Q) cannot make it) ---
    r2 = random.Random(20260905)
    N = 200_000
    big_ses = []
    for _ in range(N):
        a = r2.randint(-10**9, 10**9)
        big_ses.append((a, a + r2.randint(0, 10**6)))
    big_q = [r2.randint(-10**9 - 10**6, 10**9 + 10**6) for _ in range(N)]
    yield ("perf_200k", "perf", big_ses, big_q, 3.0)


def main():
    if len(sys.argv) < 2:
        emit("usage: harness.py <candidate main.rs>")
    candidate = os.path.abspath(sys.argv[1])
    if not os.path.isfile(candidate):
        emit(f"candidate not found: {candidate}")
    with tempfile.TemporaryDirectory() as d:
        binpath = os.path.join(d, "sol")
        try:
            b = subprocess.run(["rustc", "-O", "-o", binpath, candidate],
                               capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            emit("rustc build timed out"); return
        except FileNotFoundError:
            emit("rustc not found"); return
        if b.returncode != 0:
            emit(f"candidate does not compile: {b.stderr[-600:]}")

        results = []
        for name, tag, sessions, queries, tmo in cases():
            inp = make_input(sessions, queries)
            want = expected(sessions, queries)
            try:
                p = subprocess.run([binpath], input=inp, capture_output=True,
                                   text=True, timeout=tmo)
                if p.returncode != 0:
                    ok, detail = False, f"nonzero exit; stderr {p.stderr[-120:]}"
                else:
                    got = [int(x) for x in p.stdout.split()]
                    ok = got == want
                    detail = "ok" if ok else f"want {want[:6]}...({len(want)}) got {got[:6]}...({len(got)})"
            except subprocess.TimeoutExpired:
                ok, detail = False, f"TIMEOUT > {tmo}s (too slow — wrong complexity?)"
            except Exception as e:  # noqa: BLE001
                ok, detail = False, f"{type(e).__name__}: {e}"
            results.append({"name": name, "tag": tag, "pass": ok, "detail": detail})
        print(json.dumps({"load_error": None, "results": results}))


if __name__ == "__main__":
    main()
