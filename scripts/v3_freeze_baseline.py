#!/usr/bin/env python3
"""Freeze a model's v3 run as the permanent baseline (default: Opus 4.6).

Writes benchmark-v3/baseline.json with, per core task: the baseline's quality, cost,
and elapsed time, plus a MANIFEST HASH of every task's grader+reference+meta so we can
later detect if a "frozen" task was changed (which would invalidate the baseline).

Once frozen, the tasks and this file must not change. Future models compute their index
against this file WITHOUT re-running the baseline (see v3_report.py --use-baseline-file).

Run: v3_freeze_baseline.py [--slug v2_claude_opus_4_6] [--tasks 10,11,12,13,14,15]
     v3_freeze_baseline.py --verify     # re-hash tasks; confirm nothing drifted
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASKS = REPO / "benchmark-v3" / "tasks"
BASELINE = REPO / "benchmark-v3" / "baseline.json"


def task_hash(task_dir: Path) -> str:
    """Hash the grader + reference + meta + TASK.md (the parts that define scoring)."""
    h = hashlib.sha256()
    parts = []
    for rel in ["meta.json", "TASK.md"]:
        p = task_dir / rel
        if p.exists():
            parts.append((rel, p.read_bytes()))
    for sub in ["hidden", "reference"]:
        for p in sorted((task_dir / sub).rglob("*")) if (task_dir / sub).exists() else []:
            if p.is_file():
                parts.append((str(p.relative_to(task_dir)), p.read_bytes()))
    for name, data in sorted(parts):
        h.update(name.encode()); h.update(b"\0"); h.update(data); h.update(b"\0")
    return h.hexdigest()


def per_task_metrics(model_dir: Path, task: str) -> dict:
    p = model_dir / task / f"{task}.result.json"
    if p.exists():
        d = json.loads(p.read_text())
        return {"cost": d.get("cost_usd"), "time": d.get("elapsed_seconds"),
                "tokens": (d.get("tokens") or {}).get("total")}
    return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="v2_claude_opus_4_6")
    ap.add_argument("--tasks", default="10,11,12,13,14,15")
    ap.add_argument("--results", default=str(REPO / "results-v3"))
    ap.add_argument("--verify", action="store_true", help="re-hash tasks vs frozen manifest")
    a = ap.parse_args()
    want = a.tasks.split(",")
    task_dirs = [t for t in sorted(TASKS.iterdir())
                 if (t / "meta.json").exists() and any(t.name.startswith(w) for w in want)]

    if a.verify:
        if not BASELINE.exists():
            print("no baseline.json to verify"); return 1
        frozen = json.loads(BASELINE.read_text())
        drift = []
        for t in task_dirs:
            cur = task_hash(t)
            old = frozen["tasks"].get(t.name, {}).get("manifest_hash")
            if old != cur:
                drift.append(t.name)
        if drift:
            print(f"BASELINE DRIFT — these frozen tasks changed since freeze: {drift}")
            print("The baseline is INVALID for comparison until reverted or re-frozen.")
            return 1
        print(f"baseline intact — all {len(task_dirs)} task manifests match the freeze.")
        return 0

    md = Path(a.results) / a.slug
    rj = md / "result.json"
    if not rj.exists():
        print(f"no run to freeze at {rj}"); return 1
    run = json.loads(rj.read_text())
    scored = {t["task"]: t for t in run["tasks"]}
    if any(scored.get(t.name, {}).get("run_failed") for t in task_dirs):
        print("refusing to freeze: baseline run has a harness/auth-failed task."); return 1

    out = {"baseline_slug": a.slug, "baseline_label": run.get("label"),
           "frozen_on": date.today().isoformat(), "harness": run.get("harness"),
           "tasks": {}}
    q_sum = c_sum = t_sum = 0.0
    n = 0
    for t in task_dirs:
        s = scored.get(t.name)
        if not s:
            print(f"refusing to freeze: baseline missing task {t.name}"); return 1
        m = per_task_metrics(md, t.name)
        out["tasks"][t.name] = {
            "quality": s["correctness"],
            "cost_usd": m.get("cost"), "time_s": m.get("time"),
            "manifest_hash": task_hash(t),
        }
        q_sum += s["correctness"] or 0
        c_sum += m.get("cost") or 0
        t_sum += m.get("time") or 0
        n += 1
    out["aggregate"] = {"quality": round(q_sum / n, 2), "cost_usd": round(c_sum, 4),
                        "time_s": round(t_sum, 1), "n_tasks": n}
    BASELINE.write_text(json.dumps(out, indent=2))
    print(f"FROZEN baseline: {a.slug} over {n} tasks -> {BASELINE}")
    print(f"  aggregate: quality={out['aggregate']['quality']}  "
          f"cost=${out['aggregate']['cost_usd']}  time={out['aggregate']['time_s']}s")
    print("  Tasks + this file are now LOCKED. Re-freeze only for an explicit new benchmark version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
