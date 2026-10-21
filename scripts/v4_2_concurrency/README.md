# v4.2 — Concurrency / Capacity Test (runbook)

**Question:** how many concurrent coding users can the 4×B300 comfortably serve, and how does model VRAM footprint trade against capacity *at equal quality*?

**Status:** PREPARED, run AFTER Muse Spark v4 finishes (pod stays up). User-commissioned 2026-10-21.

## Models (quality fixed = 92.5, VRAM the only variable)
| role | model | quant | ~VRAM | single-stream tok/s (prior) | serve script |
|------|-------|-------|-------|------|------|
| HEAVY | DeepSeek V4.1 Flash | FP8 | ~510 GB | 174.8 | scratchpad `serve_minimax_m3.sh`-style / DeepSeek TP4 (re-stage) |
| LIGHT | GLM 5.3 Flash | NVFP4 | ~198 GB | 141.6 | scratchpad `serve_glm.sh` (adapt: Flash not full) |

Both already proven on this pod (TP=4). Weights likely need re-download (current pod disk holds other models). Both scored exactly 92.5 → concurrency deltas isolate to KV-cache headroom.

## Metric model
PRIMARY = **SLO-based capacity via goodput**. Default coding SLO (user can retune before run):
- TTFT < **2000 ms**
- TPOT < **20 ms/token**  ⇒ ≥ 50 tok/s per stream
- `vllm bench serve --goodput ttft:2000 tpot:20`
- **Comfortable concurrent users** = max concurrency N where goodput ≥ 95%.

SUPPORTING curves swept over N = 1,2,4,8,16,24,32,48 (extend until goodput collapses):
- per-stream decode tok/s (median+p95) — per-user slowdown
- aggregate throughput (total tok/s) — **saturation knee**
- TTFT (median+p95) — interactivity
- vLLM `/metrics`: running vs waiting seqs, **gpu_cache_usage_perc** (KV util), preemptions — the *mechanism* (heavy model's KV saturates at low N; light has headroom)

## Two measurement modes (run BOTH per model)
- **(b) Synthetic saturation — AUTHORITATIVE server capacity.** `run_bench_ramp.sh` wraps `vllm bench serve` at each `--max-concurrency`, coding-shaped lengths. **Run ON the pod against `http://localhost:8000`** so the cloudflared quick-tunnel is NOT the bottleneck (it would cap concurrency far below the GPU). Emits per-N JSON.
- **(a) Realistic agentic — practical "users via the tunnel".** `opencode_ramp.py` spawns N concurrent opencode runs (v4 sprints 1–3) from the WORKSTATION against the public endpoint. Captures tool/think duty-cycle (a server hosts more "users" than always-on streams) AND the real tunnel path. NO benchmark shield (we measure throughput, not vigilance). Heavier to orchestrate → keep N ≤ ~16 here; lean on mode (b) for high N.

Report BOTH; the gap (duty-cycle + tunnel) is itself the finding.

## Pre-flight (verify at run time — versions drift)
1. `./rx.sh 'VENV=/root/<serving-venv>; $VENV/bin/vllm bench serve --help 2>&1 | head -40'` — confirm flags: `--max-concurrency`, `--num-prompts`, `--request-rate`, `--goodput`, `--dataset-name random --random-input-len/--random-output-len/--random-range-ratio`, `--save-result`, `--metric-percentiles`.
2. Confirm `/metrics` reachable on the pod: `curl -s localhost:8000/metrics | grep -E 'gpu_cache_usage|num_requests_(running|waiting)'`.
3. Key handling: read `VLLM_API_KEY="$(cat /root/.llmkey)"` into ENV on the pod; pass to bench via env/`--api-key` WITHOUT echoing. NEVER `pgrep -af`/`ps` that dumps argv with the key (the /root/.llmkey leak lesson).

## Execution sequence (post-Muse)
1. Stop Muse server (free GPUs) — or run the test on Muse too if wanted (3rd data point, the biggest/heaviest).
2. Serve HEAVY (DeepSeek V4.1 Flash) TP=4 → wait healthy → warm → `run_bench_ramp.sh deepseek_v4_1_flash` (on pod) → `opencode_ramp.py` (workstation, N≤16) → `scrape_metrics.py` in background during both.
3. Stop; serve LIGHT (GLM 5.3 Flash) TP=4 → repeat.
4. `analyze.py` over both result dirs → v4.2 report: per-model comfortable-N@SLO, saturation knee, 4 curves + KV-util-vs-N, head-to-head, and **cost-per-comfortable-user** ($/hr ÷ N; pod ≈ $9.09/hr ledger / ~$36/hr wall).

## Outputs
`results-v4.2/concurrency/<model>/bench_c<N>.json`, `opencode_c<N>/`, `metrics_timeline.jsonl`, and `analysis.json` + `report.md`.

## Caveats (state in report)
Per-model + per-serving-config (max_num_seqs, max_num_batched_tokens, gpu-mem-util FIXED + logged; only the model varies). Comfort SLO is a choice. Long v4 context stresses KV far more than chat → conservative *coding* capacity. Tunnel bounds mode (a); localhost mode (b) is the true server ceiling.
