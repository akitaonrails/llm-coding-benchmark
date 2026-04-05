# LLM Coding Benchmark

This repository benchmarks autonomous coding runs against one fixed Rails application brief. It is built to compare a mix of local Ollama-hosted models and cloud models under the same prompt family, collect normalized run metadata, and summarize the results in Markdown.

The benchmark runner currently uses:

```bash
opencode run --agent build --format json
```

Each model run gets its own workspace under `results/<slug>/project`, plus raw `opencode` logs and a normalized `result.json`.

The current successful path is a two-phase OpenRouter run:

1. phase 1 builds the Rails app
2. phase 2 continues the same session and validates local boot, `docker build`, and `docker compose up --build`

## What This Project Contains

- `config/models.json`
  Benchmark model list, model slugs, provider IDs, and optional per-model benchmark overrides.
- `prompts/benchmark_prompt.txt`
  Phase 1 implementation prompt used for every benchmark run.
- `prompts/benchmark_followup_prompt.txt`
  Phase 2 validation prompt used for OpenRouter continuation runs.
- `scripts/warmup_ollama_models.py`
  Verifies that the local Ollama models can actually load at useful context windows.
- `scripts/run_benchmark.py`
  Runs the benchmark, writes per-model outputs, and rebuilds `docs/report.md`.
- `scripts/analyze_results_runtime.py`
  Post-run validator that can try to boot generated projects locally, with Docker, and in a browser.
- `scripts/browser_probe.mjs`
  Headless Chromium helper used by the runtime validator.
- `config/opencode.benchmark.json` / `config/opencode.benchmark.local.json`
  Generated local `opencode` configs used only for benchmark runs. **Gitignored** — regenerated automatically.
- `llama.md`
  Notes on replacing Ollama with `llama.cpp` or other OpenAI-compatible local servers.
- `results/`
  Per-model artifacts and warmup output JSON.
- `docs/report.md`
  Consolidated benchmark report.
- `docs/ollama_warmup.md`
  Warmup summary report for local Ollama models.

## Benchmark Workflow

Recommended order:

1. Run the Ollama warmup first if you intend to benchmark local models.
2. Inspect or override any fragile local model context settings.
3. Generate the local benchmark `opencode` config.
4. Run the full benchmark or a subset.
5. For OpenRouter runs, let the harness continue into the second validation prompt before treating the run as final.
6. Rebuild the report from saved artifacts whenever needed.

## Warmup

Run:

```bash
python scripts/warmup_ollama_models.py
```

What it does:

- Reads the local Ollama model mappings from `~/.config/opencode/opencode.json`.
- Tries candidate context sizes for each `ollama` model listed in `config/models.json`.
- Records the highest verified working context per model.
- Writes machine-readable output to `results/ollama_warmup.json`.
- Writes a readable summary to `docs/ollama_warmup.md`.

Current warmup assumptions:

- Minimum useful target context is `32768`.
- Maximum practical context tested is `262144`.
- Each probe attempt can take up to `180` seconds.

## Local Opencode Benchmark Config

Benchmark runs do not rely on mutating your home `opencode` config.

Before execution, `scripts/run_benchmark.py` writes a local config file:

```text
config/opencode.benchmark.json
```

That file is built from your installed `~/.config/opencode/opencode.json`, but trimmed to the providers and models needed for the selected benchmark run. Benchmark subprocesses are launched with:

```text
OPENCODE_CONFIG=config/opencode.benchmark.json
```

This keeps the benchmark reproducible and lets the harness apply safe per-model context values without rewriting your global setup.

## Context Selection Rules

For Ollama models, the local benchmark config picks the context window in this order:

1. `benchmark_context_override` from `config/models.json`
2. `highest_verified_context` from `results/ollama_warmup.json`
3. whatever is already configured in your home `opencode` config

Use `benchmark_context_override` when a model needs a more conservative value than the warmup maximum. That override is also used during the benchmark preflight load step, not just during the final `opencode` run.

Example:

```json
{
  "slug": "gemma4_31b",
  "id": "ollama/google/gemma4-31b-it-bf16",
  "provider": "ollama",
  "benchmark_context_override": 98304
}
```

## Generate The Local Benchmark Config Only

If you want to refresh the local benchmark config without starting model runs:

```bash
python scripts/run_benchmark.py --sync-ollama-contexts-only
```

That will regenerate `config/opencode.benchmark.json` from the current model config and warmup results.

## Run The Benchmark

Run everything currently enabled by default:

```bash
python scripts/run_benchmark.py
```

At the moment, the default set is the OpenRouter subset that finished cleanly in the last fresh rerun:

- `claude_opus_4_6`
- `kimi_k2_5`
- `minimax_m2_7`

Run one or more specific models:

```bash
python scripts/run_benchmark.py --model qwen3_coder_next --model gpt_5_4_pro
```

Run only Gemma:

```bash
python scripts/run_benchmark.py --model gemma4_31b
```

Re-run a model even if `result.json` already exists:

```bash
python scripts/run_benchmark.py --model gemma4_31b --force
```

Limit how many selected models run in one invocation:

```bash
python scripts/run_benchmark.py --max-runs 3
```

Change the timeout from the default `90` minutes:

```bash
python scripts/run_benchmark.py --timeout-minutes 120
```

## Rebuild The Report Only

If the runs are already on disk and you just want to rebuild the Markdown summary:

```bash
python scripts/run_benchmark.py --report-only
```

If your warmup file lives somewhere else:

```bash
python scripts/run_benchmark.py \
  --report-only \
  --ollama-warmup-results path/to/ollama_warmup.json
```

## Outputs

Each model run writes to `results/<slug>/`:

- `result.json` — Normalized metadata used by the consolidated report. **Committed to git.**
- `phase1-result.json` / `phase2-result.json` — Per-phase raw result payloads. **Committed to git.**
- `project/` — The model's generated project workspace. **Gitignored.**
- `prompt.txt` — The exact prompt used for that run. **Gitignored.**
- `opencode-output.ndjson` — Raw JSON event stream from `opencode`. **Gitignored** (may contain secrets from env captured in tool output).
- `opencode-stderr.log` — Raw stderr from the `opencode` process. **Gitignored.**
- `followup-*` — Second-phase continuation output. **Gitignored.**
- `session-export.json` — Exported `opencode` session snapshot. **Gitignored.**

Warmup writes:

- `results/ollama_warmup.json`
- `docs/ollama_warmup.md`

The consolidated benchmark report is written to:

- `docs/report.md`

## Interpreting Results

`result.json` can end in one of these statuses:

- `completed`
  The command exited cleanly and the generated workspace looks like the requested Rails project.
- `completed_with_errors`
  The command exited cleanly, but the output looks incomplete or off-spec.
- `failed`
  The run exited with an error, or failed during benchmark preflight.
- `timeout`
  The run exceeded the configured timeout and was terminated.
- `not_run`
  The model has no saved result yet.

The report also includes:

- elapsed time
- token counts when available from `opencode`
- tokens/sec when available
- whether the generated workspace resembles the intended Rails app
- warmup-verified context information for Ollama models

## Opencode Expectations

This harness assumes:

- `opencode` is available on `PATH`
- your home `opencode` config exists at `~/.config/opencode/opencode.json`
- that config contains the provider definitions and model mappings the benchmark refers to

The benchmark uses your installed provider credentials indirectly through that source config, but the benchmark execution itself points `opencode` at the generated local config file.

## Latest Fresh Rerun

The last clean rerun after resetting `results/` executed only the currently trusted OpenRouter set, using the two-phase prompt flow. All three completed successfully:

| Model | Status | Elapsed (s) | Files | Notes |
| --- | --- | ---: | ---: | --- |
| Claude Opus 4.6 | completed | 970.51 | 1536 | Two-phase run completed and the generated workspace matched the target app shape. |
| Kimi K2.5 | completed | 1738.77 | 3405 | Two-phase run completed and produced the largest project tree in the rerun. |
| MiniMax M2.7 | completed | 847.23 | 100 | Two-phase run completed cleanly and was the fastest successful rerun. |

Additional notes from that rerun:

- all three fresh reruns finished with `finish_reason: stop`
- all three recorded `phases: 2`
- the harness attempted to export the final `opencode` session, but `session_exported` remained `false` in all three saved `result.json` files
- `docs/report.md` reflects this fresh rerun snapshot

## Notes

- Warmup success does not guarantee full benchmark success. It only proves the model can load and answer a small prompt at a given context size.
- A model can still fail later during benchmark preflight, tool use, package installation, or long-context generation.
- If a local model is unstable near its verified maximum, prefer a conservative `benchmark_context_override`.
- If a benchmark or debug retry gets stuck, kill any stale `run_benchmark.py` or `opencode` process before retrying. Lingering workers can keep a remote Ollama model resident and make unload behavior misleading.

## What We Learned

- The most reliable benchmark path in this repo today is OpenRouter plus the two-phase continuation flow.
- The follow-up prompt materially improved run quality because it forced models to validate boot, Docker build, and Compose startup instead of stopping after code generation.
- `opencode` can continue an existing session for the second prompt, and that works well enough for the benchmark harness.
- The `opencode export` step is still flaky in this environment. The run metadata captures the session ID, but the exported JSON snapshot was not emitted in the latest successful reruns.
- Local Ollama runs are still useful for warmup experiments, but not reliable enough for unattended coding benchmarks on this hardware. llama-swap resolved most of these reliability issues (see below).
- If local serving matters, llama-swap with HuggingFace GGUFs is the recommended path. It resolved all the model loading, context drift, and lifecycle issues that made Ollama impractical for unattended runs.

## GPT 5.4 Pro: Tool Calling Incompatibility

GPT 5.4 Pro is the only OpenRouter cloud model that consistently fails the benchmark. Two separate runs both failed to complete:

- **Run 1:** Generated 1278 files over 46 minutes, then hit an OpenRouter credit exhaustion error that looped indefinitely (the error loop bug, now fixed). `finish_reason: tool-calls`, never reached `stop`.
- **Run 2:** Generated 1118 files over 48 minutes, ended with `finish_reason: tool-calls` and `works_as_intended: partial`. The project had code but was missing tests, Docker files, and README. Only 624 output tokens were recorded in the event stream despite 1118 files created, suggesting event capture was incomplete.

**Hypothesis:** GPT 5.4 is heavily trained for OpenAI's native function calling schema (`tool_choice`, `tools` with JSON schemas). The benchmark routes through opencode → OpenRouter → GPT 5.4, with tool schemas being translated at each hop. If GPT emits tool calls in a format that OpenRouter or opencode doesn't parse correctly, the agent loop breaks before the task completes.

**Supporting evidence:**
- Every other OpenRouter model (Claude Opus, Claude Sonnet, Kimi K2.5, DeepSeek V3.2, MiniMax M2.7, GLM 5, Qwen 3.6 Plus, Step 3.5 Flash) reached `finish_reason: stop` with successful two-phase completion.
- GPT is the only model that ends with `finish_reason: tool-calls` — it wants to keep calling tools but the loop terminates.
- The low recorded output token count (624) relative to the actual generated files (1118) suggests the ndjson event stream is not capturing GPT's tool outputs correctly.

**Fair comparison path:** To properly benchmark GPT 5.4 Pro, it would need to run in its native tool environment — either through OpenAI's Codex agent tooling or the ChatGPT Pro ($200/mo) plan which provides unlimited GPT 5.4 Pro access with native function calling. The current opencode-through-OpenRouter path is not a fair test of GPT's coding ability.

## Ollama vs llama-swap

This project supports two local model backends. Ollama was the original backend; llama-swap was added after Ollama proved unreliable for unattended benchmark runs.

### Why llama-swap

Six of the eight local models that failed under Ollama load and run correctly under llama-swap with no code changes on the benchmark side:

| Model | Ollama | llama-swap | Notes |
| --- | --- | --- | --- |
| Gemma 4 27B | `model failed to load` (HTTP 500) | 47.6 tok/s | HF GGUF Q8, was bf16 under Ollama |
| GLM 4.7 Flash | opencode never received first output | 47.4 tok/s | HF GGUF Q8, was bf16 under Ollama |
| Llama 4 Scout | model unloaded before benchmark started | 17.5 tok/s | HF GGUF, context capped at 204800 |
| Qwen 3.5 35B | completed but off-spec output | 49.7 tok/s | HF GGUF, reasoning model |
| Qwen 3.5 122B | context drifted to 262144, stalled | 23.1 tok/s | HF GGUF |
| GPT OSS 20B | `ProviderModelNotFoundError` | 78.3 tok/s | HF GGUF |
| Qwen 3 32B | ran but too slow (7.96 tok/s) | 11.7 tok/s | same Ollama GGUF |
| Qwen 3 Coder 30B | ran but too slow (6.59 tok/s) | 72.9 tok/s | same Ollama GGUF |

### llama-swap benchmark results

After fixing the `OPENCODE_CONFIG` relative path bug (which caused all earlier llama-swap runs to silently fall back to Ollama on port 11434), the following results were obtained with confirmed llama-swap connections on port 11435:

| Model | Status | Time | Files | Notes |
|---|---|---:|---:|---|
| **Qwen 3 Coder Next** | completed | 17m | 1675 | Full Rails app, tests, Docker, README |
| **Qwen 3.5 35B** | completed | 28m | 1478 | Full Rails app, all artifacts |
| **Qwen 3.5 122B** | completed | 43m | 1503 | Full Rails app, all artifacts |
| **GLM 4.7 Flash** | failed (partial) | 20m | 2029 | All artifacts present; ended mid-tool-call (`finish_reason=tool-calls`) instead of `stop` |
| **Gemma 4 31B** | failed | 11m | 1277 | Infinite tool call repetition loop (see below) |
| **GPT OSS 20B** | failed | 10m | 1310 | Created Rails app in wrong directory (`project/app/` instead of `project/`) |
| **Qwen 3 32B** | failed | 10m | 62 | Auto-killed: too slow (7.32 tok/s average, below 10 tok/s threshold) |
| **Llama 4 Scout** | skipped | — | — | No tool call parser in llama.cpp (see below) |

### Local model failure analysis

**Gemma 4 31B — infinite tool call repetition loop.** After 11–38 steps of productive work (depending on `--reasoning-format`), the model enters a loop emitting identical tool calls with the same output token count each step. With `--reasoning-format none`, the model gets ~11 productive steps before emitting empty `<|channel>thought<channel|>` tokens in a loop. Without the flag, it loops from step 1 with exactly 31 output tokens per step. This is the known llama.cpp repetition bug ([#21375](https://github.com/ggml-org/llama.cpp/issues/21375)). PR [#21418](https://github.com/ggml-org/llama.cpp/pull/21418) was supposed to fix it but the loop persists on build b1-c08d28d. The model works correctly for short conversations (1–5 tool calls) but degrades in long agentic sessions.

**Llama 4 Scout — no tool call parser in llama.cpp.** Llama 4 uses a pythonic tool call format (`[func(param="value")]`) that llama.cpp cannot parse. The model outputs tool calls as plain text in the `content` field with `finish_reason: "stop"`, so opencode never detects a tool invocation. vLLM has a dedicated `llama4_pythonic` parser but llama.cpp has no equivalent. There is no workaround from the config side — the model needs upstream llama.cpp support.

**GPT OSS 20B — wrong working directory.** The model completed 51 tool-calling steps and produced 1310 files, but created the entire Rails app under `project/app/` instead of using the project root as instructed. The benchmark checks `project/Gemfile`, `project/config/routes.rb`, etc., which don't exist at the expected paths. This is a model capability issue — a 20B model doesn't reliably follow workspace instructions for complex tasks.

**GLM 4.7 Flash — partial success.** Produced a complete-looking Rails app (2029 files, all benchmark artifacts detected) but the opencode session ended with `finish_reason=tool-calls` instead of `stop`, meaning the model was mid-tool-call when the session terminated. The benchmark marks this as "failed" but the project output appears functional. Needs `--jinja --reasoning-format none` on llama-server; `<think>` tags appear in content but don't break the AI SDK or tool calling.

**Qwen 3 32B — too slow for practical use.** The benchmark's speed gate auto-killed the run after averaging 7.32 tok/s over the first 3 steps (threshold: 10 tok/s). At this speed, a full benchmark would take hours. The model works correctly but the hardware can't serve it fast enough.

### Key differences

**Reliability.** The core problem with Ollama was unpredictable model lifecycle behavior during long autonomous runs. Models would silently unload mid-session, ignore requested context sizes, or fail to stream the first token after a successful preload. llama-swap runs each model as a dedicated llama.cpp process with fixed configuration, so what works in preflight works in the benchmark.

**Context management.** Ollama required per-request `num_ctx` negotiation, and the benchmark harness had to probe context sizes during warmup, maintain a fallback cascade, and still sometimes saw Ollama revert to default context mid-run. llama-swap configures context per model in the server config file. The benchmark harness does not need to negotiate context at all — it just sends a preload request and gets back a pass/fail.

**Model lifecycle.** Ollama required explicit unload requests (`keep_alive: 0`) that were flaky — models sometimes stayed resident and interfered with the next run. llama-swap automatically unloads the current model when a different one is requested. The benchmark's unload step is a no-op.

**Model format.** Several models that failed as Ollama-native entries work fine as HuggingFace GGUF downloads. The bf16 variants that Ollama struggled with (Gemma 4, GLM 4.7 Flash) load correctly as Q8 quantized GGUFs under llama-swap, and often run faster because they fit entirely in GPU memory.

**Integration cost.** Ollama has tighter opencode integration — model IDs in the opencode config map directly to Ollama's registry. llama-swap requires a separate `llama_swap_model` field in `config/models.json` to map between the opencode model ID and the llama-swap model name. This is a minor config inconvenience.

### Running with each backend

Ollama (original, less reliable for long runs):

```bash
python scripts/run_benchmark.py --model qwen3_32b
```

llama-swap (recommended for local models):

```bash
python scripts/run_benchmark.py \
  --local-backend llama-swap \
  --local-api-base http://192.168.0.90:11435 \
  --model gemma4_31b \
  --model glm_4_7_flash_bf16 \
  --model llama4_scout \
  --model qwen3_32b \
  --model qwen3_coder_next \
  --model qwen3_5_35b \
  --model qwen3_5_122b \
  --model gpt_oss_20b
```

### Known llama-swap limits

- **KV cache cold start.** llama-swap runs each model with `--ctx-size 0` (full default context). When a model is swapped in, the first request triggers KV cache allocation which can pin the GPU at 100% for 1–3 minutes before inference begins. This looks like a hang but is normal — the benchmark's 6-minute no-progress timeout accommodates it. Capping `--ctx-size` in the llama-swap server config would speed up model swaps but reduce available context.
- `llama4:scout` required reducing context from default to 204800 to fit in GPU memory. The 64 GB HF GGUF is near the hardware limit.
- `nemotron_cascade_2` was removed from the llama-swap server config. It can be re-added if a suitable GGUF becomes available.
- The opencode config must not include `permission` in the JSON file — opencode rejects it as invalid. Permissions are passed via the `OPENCODE_PERMISSION` environment variable at runtime instead.
- The source opencode config (`~/.config/opencode/opencode.json`) may carry `reasoning: true` and `tool_call: true` flags on Ollama model entries that are incorrect for the llama-swap GGUF variant. The benchmark config generator now strips these flags for llama-swap models unless explicitly declared in `config/models.json`.
- Ollama and llama-swap share the same GPU. The benchmark harness now evicts Ollama-resident models before starting a llama-swap run, and cleans up both backends after the benchmark finishes. Without this, large models fail to load with "upstream command exited prematurely" because the GPU is already occupied.
- When running OpenRouter and llama-swap benchmarks in parallel, use separate opencode config files (`--opencode-config config/opencode.benchmark.local.json`) to avoid one run overwriting the other's generated config.

### llama.cpp tool calling compatibility

Tool calling through llama-server's OpenAI-compatible `/v1/chat/completions` endpoint depends on llama.cpp having a parser for each model's native tool call format. Not all models are supported:

| Model | Tool calling | Required flags | Benchmark result |
|---|---|---|---|
| **Gemma 4 27B** | Partial (b8665+) | `--jinja --reasoning-format none` | Tool calls work for short sessions but model enters infinite repetition loop after ~11 steps in long agentic runs ([#21375](https://github.com/ggml-org/llama.cpp/issues/21375)). `--reasoning-format none` helps delay the loop. Without it, loops from step 1. |
| **GLM 4.7 Flash** | Yes | `--jinja --reasoning-format none` | Completed benchmark with 2029 files. `<think>` tags in content don't break tool calling. Session ended mid-tool-call but project output is functional. |
| **Qwen 3.5 (35B, 122B)** | Yes | `--jinja --reasoning-format none` | Both completed successfully (28m/1478 files and 43m/1503 files). |
| **Qwen 3 Coder (30B)** | Yes | `--jinja` | Completed successfully (17m, 1675 files). Best local model result. |
| **GPT OSS 20B** | Yes | `--jinja` | Tool calls work but model created Rails app in wrong directory. Model capability issue, not llama.cpp. |
| **Qwen 3 32B** | Yes | `--jinja` | Tool calls work but model too slow (7.3 tok/s) for practical benchmarking. |
| **Llama 4 Scout** | No | — | llama.cpp has no parser for Llama 4's pythonic format (`[func(param="value")]`). Tool calls appear as plain text. Needs upstream support similar to vLLM's `llama4_pythonic` parser. |

**Stale opencode processes.** When a benchmark run is killed or times out, opencode child processes can remain alive and hold a SQLite lock on `~/.local/share/opencode/opencode.db`. This causes all subsequent opencode instances to hang silently with zero output. Before re-running benchmarks, always kill stale processes:

```bash
pkill -f 'opencode.*run.*agent'
```
