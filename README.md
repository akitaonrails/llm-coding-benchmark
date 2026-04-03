# LLM Coding Benchmark

This repository benchmarks autonomous coding runs against one fixed Rails application brief. It is built to compare a mix of local Ollama-hosted models and cloud models under the same prompt, collect normalized run metadata, and summarize the results in Markdown.

The benchmark runner currently uses:

```bash
opencode run --agent build --format json
```

Each model run gets its own workspace under `results/<slug>/project`, plus raw `opencode` logs and a normalized `result.json`.

## What This Project Contains

- `config/models.json`
  Benchmark model list, model slugs, provider IDs, and optional per-model benchmark overrides.
- `prompts/benchmark_prompt.txt`
  The single prompt used for every benchmark run.
- `scripts/warmup_ollama_models.py`
  Verifies that the local Ollama models can actually load at useful context windows.
- `scripts/run_benchmark.py`
  Runs the benchmark, writes per-model outputs, and rebuilds `docs/report.md`.
- `config/opencode.benchmark.json`
  Generated local `opencode` config used only for benchmark runs.
- `results/`
  Per-model artifacts and warmup output JSON.
- `docs/report.md`
  Consolidated benchmark report.
- `docs/ollama_warmup.md`
  Warmup summary report for local Ollama models.

## Benchmark Workflow

Recommended order:

1. Run the Ollama warmup first.
2. Inspect or override any fragile local model context settings.
3. Generate the local benchmark `opencode` config.
4. Run the full benchmark or a subset.
5. Rebuild the report from saved artifacts whenever needed.

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

Run everything:

```bash
python scripts/run_benchmark.py
```

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

## Notes

- Warmup success does not guarantee full benchmark success. It only proves the model can load and answer a small prompt at a given context size.
- A model can still fail later during benchmark preflight, tool use, package installation, or long-context generation.
- If a local model is unstable near its verified maximum, prefer a conservative `benchmark_context_override`.
