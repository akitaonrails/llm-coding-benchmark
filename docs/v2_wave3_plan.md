# v2 Wave 3 Plan — Remaining Tiers (B/C/D) + Local Fleets

> **SCOPE CUT (2026-07-28, user decision)**: local fleets (Groups 3-4 — AMD Strix Halo and RTX 5090) are dropped from v2. Wave 3 ends with the cloud groups (subscription/OpenRouter models). Rationale: sub-Tier-A cloud models are already failing the v2 workload outright (M3 24, Qwen3.7 22); local models — which scored lower than those in v1 — would burn days of wall time to demonstrate the same DNF floor. The runner work described below for local backends is therefore not needed for v2.

**Status: planned 2026-07-27, execution starts after wave 2 completes.** User directive: after wave 2, run the remaining tiers under v2, with careful attention to the local models — RTX 5090 workstation (this machine, llama-swap at `localhost`) and the AMD Strix Halo homeserver (remote, `192.168.0.90`).

v1 (`success_report.md`) stays frozen as the official ranking for these models; wave-3 v2 runs are *stretch data* — they measure how far below the Tier A production-hardening bar each tier sits, and validate that v2's difficulty ordering agrees with v1's.

## Cohort

### Group 1 — Cloud, v1 Tier B (run first: cheap, fast, most likely to produce interesting scores)
| Model | v1 | Harness | Notes |
|---|---:|---|---|
| Gemini 3.1 Pro | 79 | opencode/OpenRouter | |
| Sakana Fugu Ultra | 79 | opencode (Sakana sub) | subscription path per doctrine |
| Claude Sonnet 4.6 | 78 | Claude Code (Max sub) | native harness per doctrine |
| DeepSeek V4 Flash | 78 | opencode/OpenRouter | |
| MiniMax M3 | 78 | opencode/OpenRouter | v1 phase-2 DNF — watch timeouts |
| Qwen3.7 Max | 78 | opencode/OpenRouter | |
| Grok 4.3 | 72 | opencode/OpenRouter | |
| Qwen 3.6 Plus | 71 | opencode/OpenRouter | |
| DeepSeek V4 Pro | 69 | **Claude Code deepclaude env-swap** | opencode multi-turn is broken for this model (reasoning_content bug) — the deepclaude pattern is mandatory |
| Kimi K2.5 | 69 | opencode/OpenRouter | K2.5 not exposed by Kimi subscription |
| Step 3.7 Flash | 69 | opencode/OpenRouter | |
| Xiaomi MiMo V2.5 Pro | 67 | opencode/OpenRouter | |
| GLM 5 | 64 | opencode/OpenRouter | superseded line; candidate to prune if budget matters |

### Group 2 — Cloud, v1 Tier C/D
| Model | v1 | Notes |
|---|---:|---|
| Claude Sonnet 5 | 58 | Claude Code (Max sub); v1 hallucinated RubyLLM — does the v2 goal contract fix that? Key experiment |
| Step 3.5 Flash | 56 | |
| GLM 5.1 (Z.ai) | 46 | Z.ai coding plan via opencode |
| DeepSeek V3.2 | 43 | |
| Qwen 3.5 397B (base) | 42 | |
| MiniMax M2.7 | 41 | |
| Grok 4.20 | 25 | expected floor calibration |

### Group 3 — Local, AMD Strix Halo homeserver (remote llama-swap)
v1-scored local roster: Qwen 3.5 35B (55), GLM 4.7 Flash bf16 (52), Qwen 3.5 122B (37), Qwen 3 Coder Next (32), GPT OSS 20B (11), plus the runnable non-scored entries in `config/models.json` (Gemma 4 31B, Qwen3.5-27B-claude distill, etc.). **Llama 4 Scout stays excluded** (no pythonic tool parser in llama.cpp).

### Group 4 — Local, NVIDIA RTX 5090 workstation (this machine)
The `config/models.nvidia.json` subset with its reduced `benchmark_context_override` values (32 GB VRAM budget). Runs last: phase-2 validation (ports, docker, compose) shares this machine with the harness, so nothing else may run concurrently.

## Runner work required (before Group 3/4 can start)

1. **Local-backend path in `run_benchmark_v2.py`**: reuse `benchmark/backends.py` preflight (unload → preload → health check) before each phase; llama-swap needs no `num_ctx` (server-side config), Ollama path needs context wiring. Add `--local-backend` / `--local-api-base` / `--config` / `--results-dir` passthroughs mirroring v1's runner.
2. **Per-model phase timeouts**: `PHASE_TIMEOUT` is 5400s; local models need ~3h phase 1 / ~2h phases 2-3 (v2 brief is ~3-4× the v1 workload; v1 local phase 1 alone ran 16-60 min at lower difficulty). Add `phase_timeout_override` to models_v2 local configs.
3. **Context reality check**: v2's 3-phase agentic flow needs bigger contexts than v1. Re-run warmups (`warmup_llama_swap.py`) on both boxes first; models whose verified max context is <64k are flagged **expected-DNF (context)** in advance rather than discovered mid-run.
4. **Known llama.cpp flags** (from v1): Gemma 4 needs build b8665+; GLM and Qwen 3.5 need `--reasoning-format none`; kill stale opencode processes + check the opencode SQLite lock before each run (existing auto-kill pattern).
5. **Results layout mirrors v1**: cloud + AMD-server runs → `results-v2/`, NVIDIA runs → `results-v2-nvidia/`; report sections appended to `success_report.v2.md` with a separate local-fleet section (efficiency axis: wall time + tokens; cost = $0 marked "local", tok/s reported from warmup).

## Sequencing

1. Wave 2 finishes (GLM 5.2 → K2.6 → Grok 4.5 → Nex-N2-Pro → Gemini Flash high).
2. Group 1 cloud B-tier, one at a time (same audit cadence: run suite, chase self-review claims, normalize shared deductions).
3. Group 2 cloud C/D.
4. AMD warmup sweep → Group 3 (remote server serves tokens; harness + docker validation stay local).
5. NVIDIA warmup sweep → Group 4 (this machine fully dedicated).

## Expectations (recorded now, checked later)

- Tier B cloud should land ~55-80 on v2; the v2 hard gates (TRUE streaming, exactly-once payload test, WEB_CONCURRENCY=2, tools, schema) are precisely the seams where v1 Tier B models cracked.
- Tier C/D cloud and most locals will fail multiple hard gates or DNF phase 1 — that is data, not noise: it fixes each tier's distance from the production-hardening bar.
- Interesting single experiments embedded in the wave: Sonnet 5's v1 hallucination vs the v2 explicit goal contract; DeepSeek V4 Pro through deepclaude on a 3-phase brief; whether any local model can pass even one v2 hard gate.
