#!/usr/bin/env python3
"""Rank v3 model runs. Quality first; when quality ties (the frontier case), cost and
speed are the differentiators.

Reads results-v3/<slug>/result.json for per-task correctness, and backfills cost /
elapsed / tokens from each task's per-phase <task>.result.json (present even for runs
recorded before result.json carried cost).

Usage: v3_report.py [--tasks 10,11,12,13] [--results results-v3]
"""
from __future__ import annotations
import argparse, glob, json
from pathlib import Path


def per_task_metrics(model_dir: Path, task: str) -> dict:
    p = model_dir / task / f"{task}.result.json"
    if p.exists():
        d = json.loads(p.read_text())
        return {"cost": d.get("cost_usd"), "elapsed": d.get("elapsed_seconds"),
                "tokens": (d.get("tokens") or {}).get("total")}
    return {"cost": None, "elapsed": None, "tokens": None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results-v3")
    ap.add_argument("--tasks", default="", help="comma list to restrict (default: all in each result.json)")
    a = ap.parse_args()
    want = set(a.tasks.split(",")) if a.tasks else None

    rows = []
    for rj in sorted(glob.glob(f"{a.results}/*/result.json")):
        md = Path(rj).parent
        r = json.loads(Path(rj).read_text())
        tasks = [t for t in r["tasks"] if (want is None or any(t["task"].startswith(w) for w in want))]
        if not tasks:
            continue
        qual = sum((t["correctness"] or 0) for t in tasks) / len(tasks)
        cost = tot_t = 0.0
        cost_known = time_known = True
        for t in tasks:
            m = per_task_metrics(md, t["task"])
            c = m["cost"] if m["cost"] is not None else t.get("cost_usd")
            e = m["elapsed"] if m["elapsed"] is not None else t.get("elapsed_seconds")
            if c is None:
                cost_known = False
            else:
                cost += c
            if e is None:
                time_known = False
            else:
                tot_t += e
        rows.append({
            "label": r.get("label") or r["slug"], "harness": r.get("harness"),
            "quality": round(qual, 1), "n": len(tasks),
            "cost": round(cost, 4) if cost_known else None,
            "time": round(tot_t, 1) if time_known else None,
        })

    # rank: quality desc, then cost asc (None last), then time asc
    rows.sort(key=lambda x: (-x["quality"], x["cost"] if x["cost"] is not None else 9e9,
                             x["time"] if x["time"] is not None else 9e9))

    print(f"{'model':40} {'qual':>6} {'cost$':>9} {'time(s)':>9} {'q/$':>8} {'q/min':>7}")
    print("-" * 84)
    for x in rows:
        qpd = f"{x['quality']/x['cost']:.0f}" if x["cost"] else "  -"
        qpm = f"{x['quality']/(x['time']/60):.1f}" if x["time"] else "  -"
        print(f"{x['label'][:40]:40} {x['quality']:>6} "
              f"{('%.2f'%x['cost']) if x['cost'] is not None else '   -':>9} "
              f"{(x['time'] if x['time'] is not None else '-'):>9} {qpd:>8} {qpm:>7}")
    print("\nTie-break order: quality desc -> cost asc -> time asc. "
          "q/$ and q/min are value ratios (higher = more quality per dollar / per minute).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
