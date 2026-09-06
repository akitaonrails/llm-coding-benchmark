#!/usr/bin/env python3
"""Ecosystem report for the v3 campaign (tasks 17+18).

Quality is the PRIMARY ranking (absolute mean correctness). Cost/speed is shown for
context, and a value index is computed ONLY among the frontier band (quality >= BAR),
because cost/speed efficiency is meaningful only between models of comparable quality —
a cheap, fast FAILURE is not "efficient". Robust to near-zero / unmetered cost.
"""
from __future__ import annotations
import argparse, glob, json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def per_task(md: Path, task: str):
    p = md / task / f"{task}.result.json"
    if p.exists():
        d = json.loads(p.read_text())
        return d.get("cost_usd"), d.get("elapsed_seconds")
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(REPO / "results-v3"))
    ap.add_argument("--tasks", default="17,18")
    ap.add_argument("--bar", type=float, default=95.0, help="frontier quality bar for the value table")
    a = ap.parse_args()
    want = a.tasks.split(",")

    rows = []
    for rj in sorted(glob.glob(f"{a.results}/*/result.json")):
        md = Path(rj).parent
        r = json.loads(rj and Path(rj).read_text())
        ts = [t for t in r["tasks"] if any(t["task"].startswith(w) for w in want)]
        if len(ts) < len(want):
            continue  # only models that have ALL v3 tasks
        if any(t.get("run_failed") for t in ts) or any(t.get("correctness") is None for t in ts):
            continue
        q = sum(t["correctness"] for t in ts) / len(ts)
        cost = tm = 0.0
        cok = tok = True
        for t in ts:
            c, e = per_task(md, t["task"])
            c = c if c is not None else t.get("cost_usd")
            e = e if e is not None else t.get("elapsed_seconds")
            if c is None:
                cok = False
            else:
                cost += c
            if e is None:
                tok = False
            else:
                tm += e
        rows.append({"label": r.get("label") or r["slug"], "q": round(q, 1),
                     "cost": round(cost, 4) if cok else None, "time": round(tm) if tok else None})

    rows.sort(key=lambda x: -x["q"])
    print("=" * 74)
    print("v3 ECOSYSTEM — QUALITY RANKING (tasks 17 app-sim + 18 resolver)")
    print("=" * 74)
    print(f"{'#':>2} {'model':40} {'Quality':>7} {'cost$':>7} {'time(s)':>7}")
    print("-" * 74)
    for i, x in enumerate(rows, 1):
        cs = f"{x['cost']:.2f}" if x['cost'] is not None else "-"
        ts_ = f"{x['time']}" if x['time'] is not None else "-"
        print(f"{i:>2} {x['label'][:40]:40} {x['q']:>7.1f} {cs:>7} {ts_:>7}")

    # ---- value table: frontier band only (quality >= bar), robust cost/speed ----
    band = [x for x in rows if x["q"] >= a.bar and x["cost"] and x["cost"] > 0.02 and x["time"]]
    print()
    print("=" * 74)
    print(f"FRONTIER VALUE (quality >= {a.bar:.0f} only — where cost/speed is the real differentiator)")
    print("  cheapest & fastest in the band = 100; higher q/$ and q/min = better value")
    print("=" * 74)
    if band:
        mc = min(x["cost"] for x in band)
        mt = min(x["time"] for x in band)
        for x in band:
            x["qpd"] = x["q"] / x["cost"]
            x["qpm"] = x["q"] / (x["time"] / 60)
            x["value"] = round(0.5 * (100 * mc / x["cost"]) + 0.5 * (100 * mt / x["time"]), 1)
        band.sort(key=lambda x: -x["value"])
        print(f"{'#':>2} {'model':40} {'Qual':>5} {'cost$':>6} {'time':>6} {'q/$':>5} {'q/min':>6} {'VALUE':>6}")
        print("-" * 82)
        for i, x in enumerate(band, 1):
            print(f"{i:>2} {x['label'][:40]:40} {x['q']:>5.1f} {x['cost']:>6.2f} {x['time']:>6} "
                  f"{x['qpd']:>5.0f} {x['qpm']:>6.1f} {x['value']:>6.1f}")
    print(f"\n(quality-primary; value gated to the >= {a.bar:.0f} band so a cheap fast FAILURE "
          f"never ranks as 'efficient'. near-zero-cost / unmetered runs excluded from value.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
