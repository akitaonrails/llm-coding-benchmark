#!/usr/bin/env python3
"""Re-grade existing v3 model runs against the CURRENT graders and rewrite each
result.json's correctness/by_tag in place (cost/elapsed/tokens preserved). Use after
fixing a grader so stored scores and reports reflect the fix — no model spend.

Usage: v3_regrade.py [--results results-v3] [--tasks 10,11,12,13]
"""
from __future__ import annotations
import argparse, glob, json, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRADER = REPO / "benchmark-v3" / "grade.py"
TASKS = REPO / "benchmark-v3" / "tasks"


def grade(task_dir: Path, project: Path) -> dict:
    p = subprocess.run(["python3", str(GRADER), str(task_dir), "--candidate", str(project),
                        "--timeout", "120"], capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"correctness": 0.0, "load_error": f"grader error: {p.stdout[-200:]} {p.stderr[-200:]}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results-v3")
    ap.add_argument("--tasks", default="")
    a = ap.parse_args()
    want = set(a.tasks.split(",")) if a.tasks else None

    for rj in sorted(glob.glob(f"{a.results}/*/result.json")):
        md = Path(rj).parent
        r = json.loads(Path(rj).read_text())
        changed = False
        for t in r["tasks"]:
            if want and not any(t["task"].startswith(w) for w in want):
                continue
            proj = md / t["task"] / "project"
            td = TASKS / t["task"]
            if not proj.is_dir() or not (td / "meta.json").exists():
                continue
            g = grade(td, proj)
            old = t.get("correctness")
            t["correctness"] = g.get("correctness")
            t["by_tag"] = g.get("by_tag")
            t["capped_by"] = g.get("capped_by")
            t["load_error"] = g.get("load_error")
            if old != t["correctness"]:
                changed = True
                print(f"  {md.name:26} {t['task']:24} {old} -> {t['correctness']}")
        scored = [t["correctness"] for t in r["tasks"] if t.get("correctness") is not None]
        r["v3_score"] = round(sum(scored) / len(scored), 1) if scored else None
        Path(rj).write_text(json.dumps(r, indent=2))
        if changed:
            print(f"  {md.name}: v3_score -> {r['v3_score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
