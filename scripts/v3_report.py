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
    ap.add_argument("--quality-weight", type=float, default=0.7,
                    help="Overall = quality_weight*Quality + (1-quality_weight)*Efficiency (default 0.7)")
    ap.add_argument("--cost-split", type=float, default=0.5,
                    help="within Efficiency, weight of cost vs speed (default 0.5)")
    a = ap.parse_args()
    want = set(a.tasks.split(",")) if a.tasks else None

    rows = []
    failed_runs = []
    for rj in sorted(glob.glob(f"{a.results}/*/result.json")):
        md = Path(rj).parent
        r = json.loads(Path(rj).read_text())
        tasks = [t for t in r["tasks"] if (want is None or any(t["task"].startswith(w) for w in want))]
        if not tasks:
            continue
        # Exclude runs with harness/auth failures — their "scores" are ungraded starter
        # files, not model attempts. Report them separately as incomplete.
        if any(t.get("run_failed") for t in tasks):
            failed_runs.append(r.get("label") or r["slug"])
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

    # ----- separate scores + a combined Overall -----
    # Quality: mean correctness (0-100, absolute).
    # Efficiency (0-100, RELATIVE to the cohort's best): the cheapest model scores 100
    #   on cost, the fastest scores 100 on speed; Efficiency blends the two.
    # Overall = quality_weight*Quality + (1-quality_weight)*Efficiency.
    costs = [x["cost"] for x in rows if x["cost"] is not None]
    times = [x["time"] for x in rows if x["time"] is not None]
    min_cost = min(costs) if costs else None
    min_time = min(times) if times else None
    cw = a.cost_split  # weight of cost within Efficiency (rest = speed)
    for x in rows:
        cost_eff = (100.0 * min_cost / x["cost"]) if (x["cost"] and min_cost) else None
        speed_eff = (100.0 * min_time / x["time"]) if (x["time"] and min_time) else None
        if cost_eff is not None and speed_eff is not None:
            x["efficiency"] = round(cw * cost_eff + (1 - cw) * speed_eff, 1)
        else:
            x["efficiency"] = cost_eff if cost_eff is not None else speed_eff
        if x["efficiency"] is not None:
            x["overall"] = round(a.quality_weight * x["quality"]
                                 + (1 - a.quality_weight) * x["efficiency"], 1)
        else:
            x["overall"] = x["quality"]

    rows.sort(key=lambda x: -x["overall"])

    print(f"{'model':34} {'Quality':>8} {'cost$':>7} {'time(s)':>8} {'Effic.':>7} {'OVERALL':>8}")
    print("-" * 76)
    for x in rows:
        eff_s = f"{x['efficiency']:.1f}" if x["efficiency"] is not None else "-"
        cost_s = f"{x['cost']:.2f}" if x["cost"] is not None else "-"
        time_s = f"{x['time']:.0f}" if x["time"] is not None else "-"
        print(f"{x['label'][:34]:34} {x['quality']:>8.1f} {cost_s:>7} {time_s:>8} "
              f"{eff_s:>7} {x['overall']:>8.1f}")
    print(f"\nQuality = mean correctness (absolute 0-100).")
    print(f"Efficiency = relative to cohort best: {int(cw*100)}% cost (cheapest=100) + "
          f"{int((1-cw)*100)}% speed (fastest=100).")
    print(f"OVERALL = {a.quality_weight:.0%} Quality + {1-a.quality_weight:.0%} Efficiency "
          f"(tune with --quality-weight / --cost-split).")
    if failed_runs:
        print(f"\nEXCLUDED (harness/auth failure, needs re-run): {', '.join(failed_runs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
