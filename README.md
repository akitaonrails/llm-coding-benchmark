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
- Local Ollama runs are still useful for warmup experiments, but not reliable enough for unattended coding benchmarks on this hardware.
- If local serving matters, a direct OpenAI-compatible server such as `llama.cpp` or LM Studio is the better next path to test than trying to push further on the current Ollama setup.

## Known Local Model Limits

Several local Ollama models were rechecked after adding cleaner unload/preflight behavior. The current status is:

- `qwen3_5_35b`
  Usable enough to benchmark. It completed a full autonomous run, but the generated project was still off-spec.
- `gemma4_31b`
  Effectively unusable in the current `opencode + Ollama` path. Preload succeeds at a conservative context, but the first real streamed request fails with Ollama HTTP `500` and `model failed to load`.
- `glm_4_7_flash_bf16`
  Effectively unusable in the current harness. Preload succeeds, but `opencode` never receives a first output chunk and the run sits waiting with no stdout/stderr progress.
- `llama4_scout`
  Effectively unusable in the current harness. Preload succeeds, but the model unloads or disappears from `/api/ps` before the benchmark emits any output.
- `qwen3_5_122b`
  Not practical in the current harness. Preload succeeds at reduced context, but during the actual run Ollama drifts back to `262144` context and `opencode` stalls before first output.
- `qwen3_32b`
  Technically runnable, but too slow to keep in the default set for this benchmark.
- `qwen3_coder_next`
  Technically runnable, but too slow to keep in the default set for this benchmark.
- `nemotron_cascade_2`
  Not usable in the current harness. Ollama preload works, but `opencode` fails immediately with `ProviderModelNotFoundError` because this custom local model entry is not resolved cleanly through the generated benchmark config.

There is also a separate integration limitation for some custom Ollama model entries:

- community or custom-tagged models that are not already present in the home `opencode` model registry can fail with `ProviderModelNotFoundError`
- this affected the Qwen 3.5 coder wrapper variants and the Nemotron benchmark entry when driven only through the generated local benchmark config

In practice, the current reliable local path is to favor the built-in Ollama model IDs that already exist in `~/.config/opencode/opencode.json`, then use the benchmark-local config only to narrow context and permissions.
