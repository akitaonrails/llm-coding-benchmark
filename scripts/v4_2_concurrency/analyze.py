#!/usr/bin/env python3
"""v4.2: aggregate the concurrency ramp into capacity@SLO + curves + cost/user.

    python3 analyze.py --dir results-v4.2/concurrency/deepseek --label "DeepSeek V4.1 Flash" \
        --vram-gb 510 [--pod-cost-hr 9.09] [--ttft-ms 2000 --tpot-ms 20]
    # head-to-head:
    python3 analyze.py --compare results-v4.2/concurrency/deepseek results-v4.2/concurrency/glm_flash

Reads `vllm bench serve` result JSONs (bench_c<N>.json) from mode (b); optionally a mode (a)
opencode summary.json and a metrics_timeline.jsonl (for KV-cache util at each level). Field
names across vLLM versions vary — parsed defensively. Stdlib only.
"""
import argparse, glob, json, os, re
from pathlib import Path


def g(d, *names, default=None):
    for n in names:
        if n in d and d[n] is not None:
            return d[n]
    return default


def load_bench_level(path):
    d = json.load(open(path))
    N = g(d, "max_concurrency", "concurrency", default=None)
    if N is None:
        m = re.search(r"_c(\d+)\.json$", os.path.basename(path))
        N = int(m.group(1)) if m else -1
    median_tpot = g(d, "median_tpot_ms", "p50_tpot_ms", default=0.0)
    median_ttft = g(d, "median_ttft_ms", "p50_ttft_ms", default=0.0)
    p99_ttft = g(d, "p99_ttft_ms", default=0.0)
    out_tput = g(d, "output_throughput", "output_throughput_tok_s", default=0.0)
    # per-stream decode tok/s from TPOT (ms/token) -> tok/s
    per_stream = round(1000.0 / median_tpot, 1) if median_tpot else 0.0
    return {
        "N": int(N),
        "median_ttft_ms": round(median_ttft, 1),
        "p99_ttft_ms": round(p99_ttft, 1),
        "median_tpot_ms": round(median_tpot, 2),
        "per_stream_tok_s": per_stream,
        "aggregate_tok_s": round(out_tput, 1),
        "goodput_req_s": g(d, "request_goodput", "goodput", default=None),
        "completed": g(d, "completed", default=None),
    }


def analyze_dir(d, label, vram_gb, ttft_ms, tpot_ms, pod_cost_hr):
    levels = sorted((load_bench_level(p) for p in glob.glob(os.path.join(d, "bench_c*.json"))),
                    key=lambda x: x["N"])
    # capacity@SLO = max N where median TTFT and median TPOT both within SLO
    comfortable = 0
    for L in levels:
        ok = (L["median_ttft_ms"] <= ttft_ms) and (L["median_tpot_ms"] <= tpot_ms)
        L["within_slo"] = ok
        if ok:
            comfortable = max(comfortable, L["N"])
    # saturation knee = last N where aggregate still rises >5% over previous
    knee = levels[0]["N"] if levels else 0
    for i in range(1, len(levels)):
        if levels[i]["aggregate_tok_s"] > levels[i - 1]["aggregate_tok_s"] * 1.05:
            knee = levels[i]["N"]
    cost_per_user = round(pod_cost_hr / comfortable, 4) if comfortable else None
    out = {
        "label": label, "vram_gb": vram_gb, "slo": {"ttft_ms": ttft_ms, "tpot_ms": tpot_ms},
        "comfortable_concurrent_users": comfortable,
        "saturation_knee_N": knee,
        "cost_per_comfortable_user_hr": cost_per_user,
        "pod_cost_hr": pod_cost_hr,
        "levels": levels,
    }
    # fold mode (a) if present
    oc = glob.glob(os.path.join(d, "opencode_c*", "summary.json"))
    if oc:
        out["mode_a_opencode"] = [json.load(open(p)) for p in sorted(oc)]
    return out


def md_table(levels):
    rows = ["| N | med TTFT ms | med TPOT ms | per-stream tok/s | aggregate tok/s | goodput req/s | SLO |",
            "|---|---|---|---|---|---|---|"]
    for L in levels:
        rows.append("| {N} | {median_ttft_ms} | {median_tpot_ms} | {per_stream_tok_s} | "
                    "{aggregate_tok_s} | {gp} | {slo} |".format(
                        gp=L.get("goodput_req_s", "-"),
                        slo="OK" if L.get("within_slo") else "—", **L))
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir")
    ap.add_argument("--label", default="")
    ap.add_argument("--vram-gb", type=float, default=0)
    ap.add_argument("--compare", nargs=2, metavar=("DIR_HEAVY", "DIR_LIGHT"))
    ap.add_argument("--ttft-ms", type=float, default=2000)
    ap.add_argument("--tpot-ms", type=float, default=20)
    ap.add_argument("--pod-cost-hr", type=float, default=9.09)
    a = ap.parse_args()

    if a.compare:
        res = []
        for d in a.compare:
            lbl = json.load(open(os.path.join(d, "label.json")))["label"] if os.path.exists(
                os.path.join(d, "label.json")) else os.path.basename(d.rstrip("/"))
            res.append(analyze_dir(d, lbl, 0, a.ttft_ms, a.tpot_ms, a.pod_cost_hr))
        heavy, light = res
        ratio = (round(light["comfortable_concurrent_users"] / heavy["comfortable_concurrent_users"], 2)
                 if heavy["comfortable_concurrent_users"] else None)
        report = ["# v4.2 concurrency — head-to-head (equal quality, VRAM varied)",
                  f"SLO: TTFT ≤ {a.ttft_ms} ms, TPOT ≤ {a.tpot_ms} ms (≥ {round(1000/a.tpot_ms)} tok/s/stream)\n"]
        for r in res:
            report += [f"## {r['label']}",
                       f"- comfortable concurrent users: **{r['comfortable_concurrent_users']}**",
                       f"- saturation knee: N={r['saturation_knee_N']}",
                       f"- cost/comfortable-user: ${r['cost_per_comfortable_user_hr']}/hr",
                       md_table(r["levels"]), ""]
        report.append(f"**Head-to-head:** the LIGHT model serves ~{ratio}× the comfortable "
                      f"concurrent coders of the HEAVY one at equal 92.5 quality.")
        Path("v4.2_headtohead.md").write_text("\n".join(report))
        print("\n".join(report))
        return

    if not a.dir:
        ap.error("need --dir or --compare")
    r = analyze_dir(a.dir, a.label, a.vram_gb, a.ttft_ms, a.tpot_ms, a.pod_cost_hr)
    Path(os.path.join(a.dir, "analysis.json")).write_text(json.dumps(r, indent=2))
    report = [f"# v4.2 concurrency — {a.label} (~{a.vram_gb} GB VRAM)",
              f"SLO: TTFT ≤ {a.ttft_ms} ms, TPOT ≤ {a.tpot_ms} ms",
              f"- **comfortable concurrent users: {r['comfortable_concurrent_users']}**",
              f"- saturation knee: N={r['saturation_knee_N']}",
              f"- cost/comfortable-user: ${r['cost_per_comfortable_user_hr']}/hr", "",
              md_table(r["levels"])]
    Path(os.path.join(a.dir, "report.md")).write_text("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main()
