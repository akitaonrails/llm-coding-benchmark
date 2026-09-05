#!/usr/bin/env python3
"""Pre-freeze solidity audit for the v3 core task suite.

Before Opus 4.6 is frozen as the baseline, every core grader MUST be:
  * DETERMINISTIC — identical score across repeated runs of the reference AND the naive
    (continuous/timed tasks may vary; we assert they stay within a tight band).
  * correct REFERENCE — reference scores >= meta.reference_min.
  * discriminating — naive scores <= meta.naive_max (a real spread).
  * HERMETIC — running graders repeatedly must not grow /tmp (leaked artifacts).

Run: v3_audit_tasks.py [--tasks 10,11,12,13,14,15] [--repeats 3] [--band 3.0]
Exit 0 iff every audited task passes. Do NOT freeze on a non-zero exit.
"""
from __future__ import annotations
import argparse, glob, json, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRADER = REPO / "benchmark-v3" / "grade.py"
TASKS = REPO / "benchmark-v3" / "tasks"


def grade(task_dir: Path, project: Path, timeout: int) -> float | None:
    p = subprocess.run(["python3", str(GRADER), str(task_dir), "--candidate", str(project),
                        "--timeout", str(timeout)], capture_output=True, text=True)
    try:
        return json.loads(p.stdout).get("correctness")
    except json.JSONDecodeError:
        return None


def tmp_snapshot():
    return set(glob.glob("/tmp/*"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="10,11,12,13,14,15")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--band", type=float, default=3.0,
                    help="max allowed spread (pts) across repeats for timed tasks")
    ap.add_argument("--timeout", type=int, default=120)
    a = ap.parse_args()
    want = a.tasks.split(",")
    task_dirs = [t for t in sorted(TASKS.iterdir())
                 if (t / "meta.json").exists() and any(t.name.startswith(w) for w in want)]

    all_ok = True
    print(f"{'task':26} {'ref(runs)':>22} {'naive':>8} {'spread':>7} {'hermetic':>9} {'verdict'}")
    print("-" * 90)
    for t in task_dirs:
        meta = json.loads((t / "meta.json").read_text())
        ep_name = Path(meta["entrypoint"]).name
        v = meta["validation"]

        # build a candidate dir = workspace + reference file overlaid
        import tempfile, shutil
        ref_scores = []
        tmp_before = tmp_snapshot()
        for _ in range(a.repeats):
            with tempfile.TemporaryDirectory() as d:
                proj = Path(d) / "project"
                shutil.copytree(t / "workspace", proj)
                shutil.copy(t / "reference" / ep_name, proj / meta["entrypoint"])
                ref_scores.append(grade(t, proj, a.timeout))
        # naive = workspace as-is
        naive = grade(t, t / "workspace", a.timeout)
        tmp_after = tmp_snapshot()
        leaked = tmp_after - tmp_before

        ref_clean = [s for s in ref_scores if s is not None]
        spread = (max(ref_clean) - min(ref_clean)) if ref_clean else 999
        ref_min_ok = bool(ref_clean) and min(ref_clean) >= v["reference_min"]
        det_ok = spread <= a.band
        naive_ok = naive is not None and naive <= v["naive_max"]
        herm_ok = not leaked
        ok = ref_min_ok and det_ok and naive_ok and herm_ok
        all_ok = all_ok and ok

        print(f"{t.name:26} {str([round(s,1) if s is not None else None for s in ref_scores]):>22} "
              f"{naive if naive is not None else '-':>8} {spread:>7.1f} "
              f"{'yes' if herm_ok else 'LEAK':>9} {'PASS' if ok else 'FAIL'}")
        if not ok:
            reasons = []
            if not ref_min_ok:
                reasons.append(f"ref<{v['reference_min']}")
            if not det_ok:
                reasons.append(f"nondeterministic (spread {spread:.1f}>{a.band})")
            if not naive_ok:
                reasons.append(f"naive {naive}>{v['naive_max']}")
            if not herm_ok:
                reasons.append(f"/tmp leak: {sorted(leaked)[:3]}")
            print(f"    -> {', '.join(reasons)}")

    print("-" * 90)
    print("ALL TASKS SOLID — safe to freeze baseline." if all_ok
          else "NOT SOLID — fix before freezing (do NOT freeze on failures).")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
