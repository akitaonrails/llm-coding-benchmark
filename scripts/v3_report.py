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
    ap.add_argument("--baseline", default="v2_claude_opus_4_6",
                    help="slug pinned as the index baseline (=100). Index has NO ceiling: "
                         "better models score >100, regressions <100.")
    ap.add_argument("--baseline-index", type=float, default=100.0,
                    help="index value assigned to the baseline model (default 100)")
    ap.add_argument("--index-quality-weight", type=float, default=0.6,
                    help="Index = qw*QualityIdx + (1-qw)*EfficiencyIdx (default 0.6)")
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
            "slug": r["slug"], "label": r.get("label") or r["slug"], "harness": r.get("harness"),
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

    # ---------- baseline-relative INDEX (no ceiling) ----------
    base = next((x for x in rows if x["slug"] == a.baseline), None)
    if base is None:
        # fall back to the FROZEN baseline file so future single-model runs get an index
        # without re-running the baseline model.
        bf = Path(__file__).resolve().parent.parent / "benchmark-v3" / "baseline.json"
        if bf.exists():
            fb = json.loads(bf.read_text())
            agg = fb["aggregate"]
            base = {"slug": fb["baseline_slug"],
                    "label": (fb.get("baseline_label") or fb["baseline_slug"]) + " [frozen]",
                    "quality": agg["quality"], "cost": agg["cost_usd"], "time": agg["time_s"]}
            print(f"\n[index] using FROZEN baseline from {bf.name} "
                  f"({base['label']}, frozen {fb.get('frozen_on')}).")
        else:
            print(f"\n[index] baseline '{a.baseline}' not among scored runs and no frozen "
                  f"baseline.json — index skipped (run the baseline, or freeze it).")
            return 0
    B = a.baseline_index
    bq, bc, bt = base["quality"], base["cost"], base["time"]
    iqw = a.index_quality_weight
    for x in rows:
        # each sub-index: 100 = baseline; >100 = better than baseline.
        x["qi"] = (B * x["quality"] / bq) if bq else None
        x["ci"] = (B * bc / x["cost"]) if (x["cost"] and bc) else None
        x["si"] = (B * bt / x["time"]) if (x["time"] and bt) else None
        if x["ci"] is not None and x["si"] is not None:
            eff_i = cw * x["ci"] + (1 - cw) * x["si"]
        else:
            eff_i = x["ci"] if x["ci"] is not None else x["si"]
        if x["qi"] is not None and eff_i is not None:
            x["index"] = round(iqw * x["qi"] + (1 - iqw) * eff_i, 1)
        else:
            x["index"] = round(x["qi"], 1) if x["qi"] is not None else None
    ranked = sorted((x for x in rows if x["index"] is not None), key=lambda x: -x["index"])
    print(f"\n===== BASELINE-RELATIVE INDEX (baseline: {base['label']} = {B:.0f}) =====")
    print(f"{'model':34} {'QualIdx':>8} {'CostIdx':>8} {'SpeedIdx':>9} {'INDEX':>7} {'vs base':>8}")
    print("-" * 78)
    def fmt(v):
        return f"{v:.0f}" if v is not None else "-"
    for x in ranked:
        d = (x["index"] - B) / B * 100.0
        print(f"{x['label'][:34]:34} {fmt(x['qi']):>8} {fmt(x['ci']):>8} "
              f"{fmt(x['si']):>9} {x['index']:>7.1f} {d:>+7.1f}%")
    print(f"\nINDEX = {iqw:.0%} QualityIdx + {1-iqw:.0%} EfficiencyIdx, all RELATIVE to baseline "
          f"({B:.0f}=baseline). >100 beats baseline, <100 trails it. No ceiling.")
    print(f"Compare two models: pct diff = (A-B)/B. E.g. GPT-6 vs GPT-5.6 = their INDEX delta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
