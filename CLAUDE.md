# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM coding benchmark harness that runs autonomous coding sessions against a fixed Rails application brief. Compares local models (Ollama or llama-swap) and cloud models (via OpenRouter) under the same prompt, using `opencode run --agent build --format json` as the runner. Uses a two-phase flow: phase 1 builds the Rails app, phase 2 validates boot/Docker/Compose.

## Key Commands

```bash
# Run benchmark (default set: models not marked skip_by_default)
python scripts/run_benchmark.py

# Run specific model(s)
python scripts/run_benchmark.py --model claude_opus_4_6 --model kimi_k2_5

# Force re-run even if result.json exists
python scripts/run_benchmark.py --model gemma4_31b --force

# Rebuild report from existing results without running models
python scripts/run_benchmark.py --report-only

# Refresh local opencode benchmark config without running
python scripts/run_benchmark.py --sync-ollama-contexts-only

# Use llama-swap instead of Ollama for local models
python scripts/run_benchmark.py --local-backend llama-swap --local-api-base http://192.168.0.90:8080

# Warmup local Ollama models (probes context sizes)
python scripts/warmup_ollama_models.py
python scripts/warmup_ollama_models.py --api-base http://192.168.0.90:11434

# Runtime validation of generated projects (local boot, Docker, browser)
python scripts/analyze_results_runtime.py
```

## Architecture

### Package layout (`scripts/benchmark/`)

The benchmark logic lives in a Python package under `scripts/benchmark/`:

- `util.py` — shared helpers: JSON I/O, timestamps, formatting, HTTP requests
- `backends.py` — `LocalModelBackend` ABC with `OllamaBackend` and `LlamaSwapBackend` implementations. Handles preflight (unload, preload, health check) for local model servers.
- `config.py` — `BenchmarkConfig` dataclass, opencode config generation, project summarization, model selection helpers
- `runner.py` — `StreamResult` dataclass, process management (`stream_process_output`), phase execution (`run_opencode_phase`, `run_model`)
- `report.py` — report generation (`build_report`, `load_results`)

### Entry points

- `scripts/run_benchmark.py` — thin CLI that parses args, creates `BenchmarkConfig`, and delegates to the package
- `scripts/warmup_ollama_models.py` — probes Ollama models at candidate context sizes
- `scripts/analyze_results_runtime.py` — post-run validator (local boot, Docker build, Docker Compose, headless browser)
- `scripts/browser_probe.mjs` — Chromium CDP helper for runtime validation

### Config layer

- `config/models.json` — model registry with slugs, provider IDs, per-model overrides (`skip_by_default`, `benchmark_context_override`, `enable_followup`), and runner command definition
- `config/opencode.benchmark.json` — auto-generated local opencode config for benchmark isolation (never edit manually)
- `config/warmup_known.json` — seed data for warmup results (models already probed manually)

### Prompt layer

- `prompts/benchmark_prompt.txt` — phase 1 implementation prompt
- `prompts/benchmark_followup_prompt.txt` — phase 2 validation prompt

### Output per model (`results/<slug>/`)

- `project/` — generated workspace
- `result.json` — normalized metadata (status, elapsed, tokens, phases)
- `opencode-output.ndjson` / `opencode-stderr.log` — raw phase 1 output
- `followup-*` — phase 2 continuation output
- `session-export.json` — opencode session snapshot (when available)

### Reports

Auto-generated (rebuilt every benchmark run):
- `docs/report.md` — AMD server / cloud profile consolidated table
- `docs/report.nvidia.md` — NVIDIA RTX 5090 workstation profile consolidated table
- `docs/ollama_warmup.md` — Ollama warmup preflight tok/s
- `docs/llama_swap_warmup.nvidia.md` — NVIDIA llama-swap preflight tok/s

Hand-written deep code review (the actual interpretive analysis):
- `docs/success_report.md` — AMD/cloud profile per-model code audit, Tier 1/2/3 runtime viability, failure analysis (including Gemma 4 Ollama Cloud 504 timeout investigation), pricing/time/test comparison tables
- `docs/success_report.nvidia.md` — NVIDIA workstation profile audit + headline finding that Claude reasoning distillation does NOT transfer library API knowledge
- `docs/success_report.multi_model.md` — 7 multi-agent variants (3 Claude Code, 2 opencode, 2 Codex). Headline findings: zero delegations happened across all 7 runs; Claude Code's harness context made Opus 4.7 hallucinate `chat.complete` (Tier 3) vs opencode's Tier 1 on identical model+prompt

Local infra docs:
- `docs/llama-swap.md` — full guide to the NVIDIA llama-swap Docker setup (CUDA 12.8 + sm_120 build, model sourcing via Ollama symlinks vs HF GGUFs, VRAM budget reasoning, common pitfalls)
- `docs/codex-integration.md` — Codex CLI integration for GPT 5.4 (hurdles: shell wrapper needs `bash -lc`, relative paths need `.resolve()`, sandbox flags, reasoning effort via `-c`, different JSONL event format)

## Model Slug Convention

Model slugs in `config/models.json` are used as directory names under `results/` and as `--model` CLI arguments. Use the slug (e.g. `claude_opus_4_6`, `qwen3_5_35b`) not the full provider ID.

## Secrets Handling

**NEVER print, echo, or otherwise expose API keys, tokens, passwords, or other secrets in tool output.** This conversation transcript is preserved and any leaked secret needs to be rotated.

- Do not run `env`, `printenv`, `cat .env`, or `grep ENV_VAR_NAME` patterns that would dump secret values into the visible output.
- When checking if an env var is set, redact the value: `python3 -c "import os; print('set' if os.environ.get('FOO') else 'unset')"` instead of `echo $FOO`.
- When testing API endpoints, never echo back the request body containing the key. Pipe through `python3` to extract just the status/response field.
- If you must reference a secret value (e.g. for debugging a bad key), show only a prefix and length: `${KEY:0:6}…(${#KEY} chars)`.
- If a secret accidentally appears in tool output, immediately tell the user it was leaked and recommend rotating it.

## Important Patterns

- The benchmark generates a **local opencode config** (`config/opencode.benchmark.json`) from the user's home config at `~/.config/opencode/opencode.json`. Benchmark subprocesses run with `OPENCODE_CONFIG=<absolute path>` (the path must be absolute — relative paths cause silent fallback to the home config).
- Ollama context window selection priority: `benchmark_context_override` > warmup verified max > home config value.
- **Local backend selection:** `--local-backend ollama` (default) or `--local-backend llama-swap`. The backend handles preflight differently — Ollama uses `/api/generate` with `num_ctx`, llama-swap uses `/v1/chat/completions` (context is server-side config).
- **Two local hardware profiles:** AMD Strix Halo server (`config/models.json`, `results/`, `docs/report.md`, host `192.168.0.90:11435`) and NVIDIA RTX 5090 workstation (`config/models.nvidia.json`, `results-nvidia/`, `docs/report.nvidia.md`, host `localhost:11435`). The NVIDIA profile is a strict subset with smaller `benchmark_context_override` values to fit in 32 GB VRAM. Use `scripts/warmup_llama_swap.py` (works for both) and pass the right `--config` / `--results-dir` / `--report` / `--local-api-base` flags. The Docker setup for the NVIDIA box lives in a separate `~/Projects/llama-swap-docker` repo (builds llama.cpp from source against CUDA 12.8 with `CMAKE_CUDA_ARCHITECTURES=120`).
- **Phase 2 follow-up** is controlled per-model via `enable_followup` in `config/models.json`. Defaults to enabled for cloud providers, disabled for local (ollama). Set `"enable_followup": true` on a local model to opt it in.
- Result statuses: `completed`, `completed_with_errors`, `failed`, `timeout`, `not_run`.
- Before retrying stuck benchmarks, kill stale `run_benchmark.py` and `opencode` processes — they can keep models resident on the server and hold the opencode SQLite DB lock (`~/.local/share/opencode/opencode.db`), causing new opencode instances to hang silently. The runner now auto-kills stale opencode processes before each model run.
- **llama.cpp tool calling:** Gemma 4 requires build b8665+ (PR #21418). Llama 4 Scout is incompatible (no pythonic parser). GLM and Qwen 3.5 need `--reasoning-format none` on the llama-server to avoid `reasoning_content` tokens.
- **Z.ai provider has two distinct endpoints**: `/api/paas/v4` (general PaaS, pay-per-token, restricts latest models by tier) vs `/api/coding/paas/v4` (coding plan, flat-rate Lite/Pro/Max subscription, includes GLM 5.1 for all tiers). Same `ZAI_API_KEY` works for both, but each enforces different model permissions. The benchmark wires the coding endpoint via the `zai` provider in the home opencode config.
- **Codex CLI runner:** Models with `"runner_type": "codex"` in models.json use `codex exec` instead of `opencode run`. Currently used for GPT 5.4 (no tool calling via OpenRouter). Key pitfalls: the `codex` binary is a bash wrapper for `npx` (needs `bash -lc` to activate mise/node), paths passed to `-C` must be absolute (`.resolve()`), and JSONL events are a different format (see `docs/codex-integration.md`). Auth via `OPENAI_API_KEY` env var. Reasoning effort set via `codex_reasoning_effort` field in models.json (`-c model_reasoning_effort=xhigh`).
- **Claude Code runner with `env_overrides` (deepclaude pattern):** Variants in `config/claude_code_models.json` can declare an `env_overrides` dict to swap the API target. Used to route Claude Code's tool loop through OpenRouter's Anthropic-compatible endpoint to non-Anthropic models (e.g. DeepSeek V4 Pro via `https://openrouter.ai/api`). Values starting with `$` are indirect lookups against the parent env (`$OPENROUTER_API_KEY` resolves at run time, keeping secrets out of the JSON config). Keys starting with `UNSET:` remove the named variable from the subprocess env (drop `ANTHROPIC_API_KEY` when swapping to non-Anthropic backends). See `docs/deepclaude-integration.md` and `docs/success_report.deepclaude.md`.
- **DeepSeek V4 Pro reasoning_content (RESOLVED via deepclaude in Round 4):** opencode's ai-sdk strips reasoning_content from the model's response, but DeepSeek's API requires it echoed back in subsequent requests, breaking every multi-turn opencode session at turn 2. No opencode model-level config flag fixes this. **The workaround is to NOT use opencode for DeepSeek V4 Pro multi-turn at all** — instead use Claude Code via the deepclaude env-swap pattern, which routes through OpenRouter's `/anthropic` endpoint and bypasses the request-payload bug entirely. Both deepclaude variants completed end-to-end at Tier A (84-89/100). The bug is opencode-specific; the model itself is fine.
- **Adding a new model**: see the "Adding A New Model" section in README.md for the full workflow — choose provider, add models.json entry, optionally wire a new provider in home opencode config, run, then analyze. The analysis MUST include reading the LLM integration code by hand to verify the model used real RubyLLM API methods (most models hallucinate fluent APIs like `chat.add_message()` or `RubyLLM::Client.new` — these crash at runtime).
- **Result tiers** for benchmark interpretation: Tier 1 = correct API + proper test mocking (works at runtime). Tier 2 = correct primary call but partial issues (multi-turn broken, wrong gem, Dockerfile bugs). Tier 3 = hallucinated API (NameError on first call). Two parallel success reports — `docs/success_report.md` for AMD server / cloud models, `docs/success_report.nvidia.md` for the NVIDIA RTX 5090 workstation profile. The NVIDIA report has the headline distillation finding (Claude reasoning distillation does NOT transfer library API knowledge).
- All Python scripts use only stdlib (Python 3.10+ required for `X | None` union syntax).
