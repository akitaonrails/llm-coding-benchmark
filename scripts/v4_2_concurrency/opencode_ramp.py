#!/usr/bin/env python3
"""v4.2 mode (a): realistic agentic concurrency.

Spawns N concurrent opencode "users", each running v4 sprints 1-3 sequentially in its
OWN throwaway workspace against a shared vLLM endpoint (the provider wired in the isolated
opencode config). Measures the practical, duty-cycle-inclusive per-user effective tok/s and
end-to-end wall-time through the real path (incl. the cloudflared tunnel when the endpoint is
the pod). NOT shielded — we measure throughput, not vigilance. Stdlib only.

    python3 opencode_ramp.py --model-id deepseek_v4_1_flash_b300/deepseek \
        --concurrency 8 --out results-v4.2/concurrency/deepseek/opencode_c8

Run `scrape_metrics.py` on the pod in parallel for aggregate-token/KV truth.
Keep N modest here (<=16); use run_bench_ramp.sh for high-N saturation.
"""
import argparse, json, os, subprocess, tempfile, threading, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROMPTS = REPO / "benchmark-v4" / "prompts"
DEFAULT_SPRINTS = ["01_foundation", "02_multiuser", "03_admin"]


def sprint_prompt(name: str) -> str:
    return (PROMPTS / f"sprint{name}.txt").read_text()


def opencode_env(config_path: Path) -> dict:
    env = dict(os.environ)
    env["OPENCODE_CONFIG"] = str(config_path.resolve())          # MUST be absolute
    env["XDG_CONFIG_HOME"] = str((REPO / "config" / "opencode.xdg-isolated").resolve())
    return env


def sum_output_tokens(ndjson_path: Path) -> int:
    """Best-effort: sum generation/output tokens across ALL step_finish events (per the
    extract_metrics fix — each step_finish carries only its own step's usage)."""
    total = 0
    try:
        for line in ndjson_path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line or '"step' not in line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            # dig for a usage/tokens object on step-finish-ish events
            if "step" not in (ev.get("type", "") + ev.get("event", "")):
                continue
            u = ev.get("usage") or ev.get("tokens") or {}
            for k in ("output", "completion", "completion_tokens", "output_tokens", "generated"):
                v = u.get(k) if isinstance(u, dict) else None
                if isinstance(v, (int, float)):
                    total += int(v)
                    break
    except FileNotFoundError:
        pass
    return total


def run_user(uid: int, model_id: str, config_path: Path, sprints, out_dir: Path, results: dict):
    ws = Path(tempfile.mkdtemp(prefix=f"v42_user{uid}_"))
    env = opencode_env(config_path)
    user_rec = {"uid": uid, "workspace": str(ws), "sprints": []}
    t0 = time.time()
    for name in sprints:
        nd = out_dir / f"user{uid}_sprint{name}.ndjson"
        st = time.time()
        with open(nd, "wb") as fout, open(os.devnull, "rb") as fin:
            p = subprocess.run(
                ["opencode", "run", "--agent", "build", "--format", "json",
                 "--dir", str(ws), "-m", model_id, sprint_prompt(name)],
                stdin=fin, stdout=fout, stderr=subprocess.STDOUT, env=env,
            )
        el = time.time() - st
        toks = sum_output_tokens(nd)
        user_rec["sprints"].append({
            "sprint": name, "exit": p.returncode, "elapsed_s": round(el, 1),
            "output_tokens": toks, "eff_tok_s": round(toks / el, 2) if el > 0 else 0,
            "ndjson": str(nd),
        })
    user_rec["total_elapsed_s"] = round(time.time() - t0, 1)
    user_rec["total_output_tokens"] = sum(s["output_tokens"] for s in user_rec["sprints"])
    user_rec["overall_eff_tok_s"] = (
        round(user_rec["total_output_tokens"] / user_rec["total_elapsed_s"], 2)
        if user_rec["total_elapsed_s"] > 0 else 0)
    results[uid] = user_rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-id", required=True, help="opencode provider/model, e.g. deepseek_v4_1_flash_b300/deepseek")
    ap.add_argument("--config", default=str(REPO / "config" / "opencode.benchmark.json"))
    ap.add_argument("--concurrency", type=int, required=True)
    ap.add_argument("--sprints", nargs="*", default=DEFAULT_SPRINTS)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    config_path = Path(a.config)

    results: dict = {}
    threads = []
    t0 = time.time()
    for uid in range(a.concurrency):
        th = threading.Thread(target=run_user,
                              args=(uid, a.model_id, config_path, a.sprints, out_dir, results))
        th.start()
        threads.append(th)
    for th in threads:
        th.join()
    wall = time.time() - t0

    users = [results[u] for u in sorted(results)]
    per_user = [u["overall_eff_tok_s"] for u in users]
    per_user.sort()
    n = len(per_user)
    summary = {
        "mode": "a_opencode_agentic",
        "model_id": a.model_id,
        "concurrency": a.concurrency,
        "sprints": a.sprints,
        "wall_s": round(wall, 1),
        "users": users,
        "per_user_eff_tok_s_median": per_user[n // 2] if n else 0,
        "per_user_eff_tok_s_min": per_user[0] if n else 0,
        "aggregate_output_tokens": sum(u["total_output_tokens"] for u in users),
        "aggregate_eff_tok_s": round(sum(u["total_output_tokens"] for u in users) / wall, 2) if wall else 0,
        "all_exit0": all(s["exit"] == 0 for u in users for s in u["sprints"]),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in
                      ("concurrency", "wall_s", "per_user_eff_tok_s_median",
                       "per_user_eff_tok_s_min", "aggregate_eff_tok_s", "all_exit0")}, indent=2))


if __name__ == "__main__":
    main()
