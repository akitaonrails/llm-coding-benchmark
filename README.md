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
- `config/opencode.benchmark.json`
  Generated local `opencode` config used only for benchmark runs.
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

- `project/`
  The model's generated project workspace.
- `prompt.txt`
  The exact prompt used for that run.
- `opencode-output.ndjson`
  Raw JSON event stream from `opencode`.
- `opencode-stderr.log`
  Raw stderr from the `opencode` process.
- `followup-prompt.txt`
  The second-phase validation prompt for OpenRouter continuation runs.
- `followup-opencode-output.ndjson`
  Raw JSON event stream from the second-phase continuation.
- `followup-opencode-stderr.log`
  Raw stderr from the second-phase continuation.
- `session-export.json`
  Exported `opencode` session snapshot when available.
- `result.json`
  Normalized metadata used by the consolidated report.

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

- `llama4:scout` required reducing context from default to 204800 to fit in GPU memory. The 64 GB HF GGUF is near the hardware limit.
- `nemotron_cascade_2` was removed from the llama-swap server config. It can be re-added if a suitable GGUF becomes available.
- Reasoning models (`qwen3.5:35b`, some Qwen 3 variants) emit output in `reasoning_content` instead of `content`. This works with opencode but may affect token counting in the benchmark report.
