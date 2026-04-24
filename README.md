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

## Key Findings

The deep code reviews in `docs/success_report*.md` are the substance of this repo. Headlines:

- **Most models hallucinate the RubyLLM gem API.** Only Claude Opus/Sonnet and GLM 5 produce working code out of the box. Most models invent fluent APIs (`chat.add_message()`, `RubyLLM::Client.new`, `chat.complete`) that crash at runtime, then write tests that mock those invented APIs — so tests pass and the code is still broken. File-count and test-count are not reliable signals. See [`docs/success_report.md`](docs/success_report.md).
- **Claude reasoning distillation does NOT transfer library API knowledge.** A Qwen 3.5 27B distilled from Claude 4.6 Opus reasoning traces produced code that *looks* Claude-shaped but still hallucinated the RubyLLM API in the same way. API correctness is binary recall, not a reasoning skill. See [`docs/success_report.nvidia.md`](docs/success_report.nvidia.md).
- **Multi-agent subagent patterns don't fire on cohesive tasks.** Across 7 benchmark variants with Claude Code, opencode, and Codex multi-agent configurations — every model ignored its coding subagent and did 100% of the work itself. "Use PROACTIVELY" language was not persuasive against "skip for architectural decisions" caveats on a greenfield Rails build. See [`docs/success_report.multi_model.md`](docs/success_report.multi_model.md).
- **The harness matters for correctness, not just cost.** The same Opus 4.7 model produced Tier 1 code (correct RubyLLM API) in opencode and Tier 2/3 code (hallucinated `chat.complete`) in Claude Code. Claude Code's 6-11M cache-read tokens per run (vs opencode's ~210K) appear to nudge the model toward generic OpenAI-SDK patterns. Same model, different harness, different correctness.
- **GPT 5.4 via Codex CLI is Tier 2, not Tier 1.** The previous version of this report carried an author's vouch that GPT 5.4 "performs on par with Claude Opus." Concrete testing via Codex CLI at xHigh reasoning shows GPT 5.4 produces the most polished *architecture* of any model but hallucinates `chat.add_message(role:, content:)` as keyword args — crashes on multi-turn. ~$16/run, 15× Claude's cost for worse API correctness.
- **Xiaomi MiMo V2.5 Pro is the best non-Anthropic code we've seen — but still Tier 2.** At ~$0.14/run and 11 minutes, 8× cheaper than Opus. All API calls are genuinely correct (no hallucinations, no kwargs bugs) — the cleanest non-Anthropic output in the benchmark. But Tier 1 requires correct API AND proper LLM test mocking, and MiMo's tests never exercise the `ask` path. Add process-local `ChatStore` Singleton (doesn't survive restarts or work across workers), no error handling, and no system prompt — demo-quality, not production-quality. The 8× premium to Opus buys test harness, error boundary, persistence model, Docker hardening, and view polish — about 2 engineer-hours of patching if you try to ship MiMo's output as-is. For prototypes, MiMo wins on cost; for production, Opus. See [`docs/success_report.md`](docs/success_report.md#opus-47-vs-mimo-v25-pro--where-the-8-premium-goes).
- **DeepSeek V4 Pro writes Tier 1 code but opencode can't run it.** Same clean `@chat.ask()` pattern as MiMo, but DeepSeek's thinking mode requires the client to echo `reasoning_content` on every turn and opencode strips it — so the harness DNFs. V4 Flash at $0.01/run fixes V3.2's `RubyLLM::Client` hallucination but still uses `add_message(role:, content:)` kwargs (Tier 2). V3.2 → V4 is a real generational improvement.
- **Kimi K2.6 partially fixes K2.5's hallucinations.** Dropped the invented `chat.complete()` method (big win) but kept the `add_message(role:, content:)` kwargs bug. Moved K2.5 from Tier 3 to K2.6 Tier 2 — cheaper than Sonnet at $0.14/run, but at the same price point as MiMo which actually works. Pick MiMo over K2.6.

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
  Per-model artifacts for the AMD server / cloud profile (default).
- `results-nvidia/`
  Per-model artifacts for the NVIDIA RTX 5090 workstation profile.
- `docs/report.md`
  Auto-generated consolidated benchmark table for the AMD/cloud profile.
- `docs/report.nvidia.md`
  Auto-generated consolidated benchmark table for the NVIDIA workstation profile.
- `docs/success_report.md`
  **Hand-written deep code review** of every model in the AMD/cloud profile. Tier 1/2/3 runtime viability classification, per-model failure analysis, pricing/time/test comparison tables, and the documented limitations of file-count and test-count as benchmark metrics. Includes the Gemma 4 Ollama Cloud failure analysis.
- `docs/success_report.nvidia.md`
  **Hand-written deep code review** of every model in the NVIDIA workstation profile. Includes the headline finding that Claude reasoning distillation does NOT transfer library API knowledge.
- `docs/success_report.multi_model.md`
  **Hand-written deep code review** of 7 multi-agent benchmark variants (Claude Code subagents, opencode multi-agent, Codex multi-agent). Headline findings: zero models voluntarily delegated on a greenfield Rails task, and Claude Code produced measurably worse code than opencode for the same Opus 4.7 model due to harness context pollution.
- `docs/llama-swap.md`
  Comprehensive guide to the local llama-swap Docker setup for the NVIDIA profile (CUDA 12.8 + sm_120 build, model sourcing, VRAM budget, common pitfalls).
- `docs/codex-integration.md`
  Codex CLI integration guide: how GPT 5.4 runs via `codex exec` instead of opencode, all the hurdles encountered (shell wrapper, relative paths, sandbox flags, reasoning effort, JSONL format differences).
- `docs/ollama_warmup.md` / `docs/llama_swap_warmup.nvidia.md`
  Auto-generated per-model preflight tok/s reports.

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

## Two Local Backend Profiles: AMD Server vs NVIDIA Workstation

This repo supports running the local-llama-swap subset of the benchmark against **two different machines**, with separate config files and result directories so the runs don't overwrite each other:

| Profile | Hardware | llama-swap host | Models config | Results dir | Report |
|---|---|---|---|---|---|
| **AMD server** | Strix Halo, gfx1151, 128 GB unified | `http://192.168.0.90:11435` | `config/models.json` | `results/` | `docs/report.md` |
| **NVIDIA workstation** | RTX 5090, sm_120, 32 GB VRAM | `http://localhost:11435` | `config/models.nvidia.json` | `results-nvidia/` | `docs/report.nvidia.md` |

The NVIDIA profile is a **strict subset** of the AMD profile: only the local llama-swap models that fit in 32 GB of VRAM are included, with smaller `benchmark_context_override` values to keep KV cache within budget. The OpenRouter and Z.ai cloud models are not duplicated — those go in `config/models.json` alone since they don't depend on local hardware.

The Docker setup for the NVIDIA workstation lives at [`~/Projects/llama-swap-docker`](https://github.com/akitaonrails/llama-swap-docker) (separate repo). It builds llama.cpp from source against CUDA 12.8 with `CMAKE_CUDA_ARCHITECTURES=120` so the kernels target Blackwell directly.

### Run the NVIDIA profile

Make sure llama-swap is up locally first:

```bash
cd ~/Projects/llama-swap-docker
docker compose up -d --build
docker compose logs -f llama-swap   # watch until server ready
```

Then warmup and run the benchmark, redirecting outputs to the NVIDIA-specific paths:

```bash
cd ~/Projects/llm-coding-benchmark

# Warmup: probe each model's preflight tok/s
python scripts/warmup_llama_swap.py \
  --api-base http://localhost:11435 \
  --config config/models.nvidia.json

# Full benchmark for the NVIDIA subset
python scripts/run_benchmark.py \
  --config config/models.nvidia.json \
  --results-dir results-nvidia \
  --report docs/report.nvidia.md \
  --local-backend llama-swap \
  --local-api-base http://localhost:11435 \
  --opencode-config config/opencode.benchmark.local.json
```

The same `run_benchmark.py` and `warmup_llama_swap.py` scripts handle both profiles — only the file paths and api-base differ. Per-model results, comparison tables, and code review can be done independently for each profile.

### When to add NVIDIA-specific overrides

If a model needs a different context size, gem path, or skip flag specifically because it's running on the smaller VRAM, edit `config/models.nvidia.json` only — leave `config/models.json` untouched. The NVIDIA file is generated as a copy of the relevant entries with `benchmark_context_override` adjusted, and is meant to be hand-edited as the local set evolves.

Currently the NVIDIA subset is: `gemma4_31b`, `gpt_oss_20b`, `qwen3_32b`, `qwen3_5_27b_claude`, `qwen3_5_35b`, `qwen3_coder_next`. Models excluded for VRAM reasons: `glm_4_7_flash_bf16`, `qwen3_5_122b`, `llama4_scout` (all listed in the config file's bottom comment).

## Adding A New Model

To add and benchmark a new model, follow these steps in order. The flow differs depending on whether the model lives on a provider already wired (OpenRouter, Z.ai, llama-swap) or needs a brand new provider entry.

### 1. Choose the right provider

| Provider type | Use when | Example |
|---|---|---|
| `openrouter` | Model is exposed on openrouter.ai/models | Claude, GLM 5, Grok, Gemini, DeepSeek, Step, Kimi, MiniMax, Qwen cloud |
| `zai` | Model is on Z.ai's coding plan endpoint | GLM 5.1 |
| `ollama` (with `--local-backend llama-swap`) | Model is hosted on your llama-swap server | Local GGUFs (Qwen, Gemma, GLM, GPT OSS, Llama 4) |

### 2. Add the model to `config/models.json`

Append a new entry to the `models` array:

```json
{
  "slug": "vendor_name_version",
  "id": "openrouter/vendor/model-id",
  "label": "Vendor Model Name",
  "provider": "openrouter",
  "selection_reason": "One-line context (pricing, why it was added, known caveats)."
}
```

For local llama-swap models, also add `"llama_swap_model": "vendor:tag"` matching the name configured on the llama-swap server. For models you don't want to run by default, add `"skip_by_default": true`.

### 3. Wire a new provider (only if it doesn't exist yet)

If the model is on a brand new provider (e.g. you're adding `togetherai`, `groq`, `fireworks`):

1. Add a provider entry to your home opencode config (`~/.config/opencode/opencode.json`) under `provider.<name>`. Use `"npm": "@ai-sdk/openai-compatible"` and set `options.baseURL` to the provider's OpenAI-compatible endpoint and `options.apiKey` to `"{env:VENDOR_API_KEY}"`.
2. Make sure the API key env var is set in your shell (`source ~/.config/zsh/secrets`).
3. Run `python scripts/run_benchmark.py --model <slug> --sync-ollama-contexts-only` to regenerate the benchmark config and verify the provider entry is cloned correctly into `config/opencode.benchmark.json`.

**Z.ai gotcha:** Z.ai exposes two distinct API endpoints:
- `/api/paas/v4` (general PaaS): pay-per-token, but the latest GLM models (5.1, 5-turbo) are not accessible to all subscription tiers here.
- `/api/coding/paas/v4` (coding plan): the flat-rate Lite/Pro/Max subscription endpoint where GLM 5.1 *is* accessible to all tiers including Lite.

For GLM 5.1, the benchmark provider entry must point at `https://api.z.ai/api/coding/paas/v4`. Same `ZAI_API_KEY` works for both endpoints, but each endpoint enforces different model permissions.

### 4. Run the new model

```bash
python scripts/run_benchmark.py --model <slug>
```

For OpenRouter and Z.ai cloud models, phase 2 (Docker validation) runs automatically. For local models, phase 2 is opt-in via `"enable_followup": true` in `config/models.json`.

### 5. Analyze the result

After the run completes, do the analysis in this order:

**a. Quick metrics** (single-model summary):
```bash
python3 -c "
import json
d = json.load(open('results/<slug>/result.json'))
ps = d.get('project_summary', {})
print(f\"status={d.get('status')} elapsed={d.get('elapsed_seconds',0):.0f}s files={ps.get('file_count',0)}\")
print(f\"finish={d.get('finish_reason')} works={ps.get('works_as_intended')}\")
phases = d.get('phases', [])
for i, p in enumerate(phases):
    print(f\"  phase{i+1}: status={p.get('status')} tokens={p.get('tokens',{}).get('total',0)}\")
"
```
Look for `status=completed` (or `completed_with_errors`), `finish=stop`, and `works=yes`. Anything else is a structural failure.

**b. Structural completeness**: check that all benchmark artifacts are present in `result.json`'s `project_summary.present` map: `gemfile`, `routes`, `app_dir`, `views_dir`, `tests_dir`, `dockerfile`, `docker_compose_yml`, `readme_md`. A score of 9/9 is the minimum bar for a "successful" run.

**c. Test count**: structural test count is misleading on its own but useful as a sanity check. Count test methods in `results/<slug>/project/test/`:
```bash
grep -rEc '^\s*(test\s+["\x27]|def\s+test_)' results/<slug>/project/test/ | awk -F: '{s+=$2} END {print s}'
```

**d. CRITICAL — read the LLM integration code by hand.** This is the only step that catches the "looks complete but won't run" failure mode. Open `results/<slug>/project/app/services/*.rb` and `results/<slug>/project/app/controllers/*.rb` and verify the model used the **real RubyLLM API**:
   ```ruby
   chat = RubyLLM.chat(model: "anthropic/claude-sonnet-4")
   response = chat.ask("Hello")
   response.content
   ```
   Common hallucinations to watch for (every one of these is a runtime crash):
   - `RubyLLM::Client.new(...)` — class doesn't exist
   - `RubyLLM::Chat.new(...)` — constructor isn't public
   - `chat.add_message(role:, content:)` — method doesn't exist
   - `chat.complete(...)` — method doesn't exist
   - `chat.user(...)` / `chat.assistant(...)` — fluent helpers don't exist
   - `RubyLLM.chat(model:, messages: [...])` — batch signature doesn't exist
   - `Openrouter::Client.new(...)` — gem doesn't exist
   - Bypassing RubyLLM entirely with `OpenAI::Client` from `ruby-openai` (check if the gem is in `group :development, :test` — if so, prod will `NameError`)

**e. Check test mocking**: open the test files and verify they actually mock the LLM call (look for `mocha`, `Minitest::Mock`, or `WebMock`). Tests that hit the real API will pass locally with your key set but fail in CI. Tests that mock a hallucinated API will pass *and* lie about the code's correctness.

**f. Check the Dockerfile** for `RUBY_VERSION` (Ruby 4 doesn't exist as of this writing — `4.0.x` is a known model hallucination), `SECRET_KEY_BASE` handling, and port consistency between `EXPOSE` and `docker-compose.yml`.

**g. Categorize into a tier**:
- **Tier 1 (works)**: Correct RubyLLM API, proper test mocking, no Dockerfile bugs.
- **Tier 2 (works with caveats)**: Correct primary API call but partial issues (e.g. multi-turn history seeding broken, Ruby version typo, bypasses RubyLLM with raw HTTP but functional).
- **Tier 3 (broken core)**: Hallucinated API, NameError on first call, or fundamentally non-functional.

**h. Update the right success report:**
   - AMD server profile / cloud models → [`docs/success_report.md`](docs/success_report.md)
   - NVIDIA workstation profile (local llama-swap) → [`docs/success_report.nvidia.md`](docs/success_report.nvidia.md)

   Add the model's row to the relevant comparison tables (completeness, tests, gems, pricing, time, runtime viability). If the model belongs in Tier 2 or 3, add a short failure analysis paragraph. The current reports show the format.

### 6. Commit the result

`result.json`, `phase1-result.json`, and `phase2-result.json` are tracked. Everything else under `results/<slug>/` (project tree, prompt files, ndjson logs, session exports) is gitignored — those files often contain raw env captures including secrets, so do not force-add them.

```bash
git add results/<slug>/result.json results/<slug>/phase1-result.json results/<slug>/phase2-result.json config/models.json docs/success_report.md
git commit
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

Warmup writes (AMD/Ollama profile):

- `results/ollama_warmup.json`
- `docs/ollama_warmup.md`

Warmup writes (NVIDIA llama-swap profile):

- `results-nvidia/llama_swap_warmup.json`
- `docs/llama_swap_warmup.nvidia.md`

The consolidated auto-generated benchmark reports:

- `docs/report.md` — AMD/cloud profile (the default `--results-dir results/`)
- `docs/report.nvidia.md` — NVIDIA workstation profile (`--results-dir results-nvidia/`)

The hand-written deep code review and runtime viability analysis (which is what you usually want):

- `docs/success_report.md` — AMD/cloud profile
- `docs/success_report.nvidia.md` — NVIDIA workstation profile

For the local llama-swap Docker setup (only relevant if running the NVIDIA profile):

- `docs/llama-swap.md` — full guide, hardware tuning, common pitfalls

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

## Latest Benchmark Run

The benchmark currently covers **18 models** across 3 providers (OpenRouter, Z.ai direct, llama-swap local). 14 models complete the benchmark structurally; only 3 produce code that actually runs at runtime. See [`docs/success_report.md`](docs/success_report.md) for the full analysis with code review tiers.

**Runtime viability summary** (Tier 1 = actually works, Tier 2 = works with caveats, Tier 3 = broken core):

| Tier | Models |
|---|---|
| 1 (works) | Claude Opus 4.6, Claude Sonnet 4.6, GLM 5 |
| 2 (caveats) | GLM 5.1, Step 3.5 Flash, Qwen 3.5 35B (local) |
| 3 (broken) | Kimi K2.5, MiniMax M2.7, DeepSeek V3.2, Gemini 3.1 Pro, Grok 4.20, Qwen 3.6 Plus, Qwen 3 Coder Next, Qwen 3.5 122B |
| failed | GPT 5.4 Pro (tooling), Gemma 4 31B, GPT OSS 20B, Qwen 3 32B, Llama 4 Scout |

The headline finding: **structural completeness does not predict runtime correctness**. A model can produce a 9/9 artifact checklist with 37 test methods and still call a non-existent gem API. Only the Anthropic models and GLM 5 use the real `RubyLLM.chat`/`chat.ask` API correctly. See the [success report](docs/success_report.md) for per-model breakdown.

## Notes

- Warmup success does not guarantee full benchmark success. It only proves the model can load and answer a small prompt at a given context size.
- A model can still fail later during benchmark preflight, tool use, package installation, or long-context generation.
- If a local model is unstable near its verified maximum, prefer a conservative `benchmark_context_override`.
- If a benchmark or debug retry gets stuck, kill any stale `run_benchmark.py` or `opencode` process before retrying. Lingering workers can keep a remote Ollama model resident and make unload behavior misleading.

## What We Learned

- **Benchmark metrics lie about runtime correctness.** Test counts, file counts, and artifact checklists do not measure whether the generated code actually works. A model can write 37 test methods and still call a hallucinated API. The only reliable signal is reading the LLM integration code by hand and verifying it uses real gem methods. See [`docs/success_report.md`](docs/success_report.md) for the runtime viability audit.
- **Most models hallucinate the RubyLLM API.** Out of 14 models that "completed" the benchmark structurally, only 3 use the correct `RubyLLM.chat(model:)` / `chat.ask("...")` pattern: Claude Opus, Claude Sonnet, and GLM 5. The rest invent classes (`RubyLLM::Client`), methods (`add_message`, `complete`, `chat.user`), or bypass RubyLLM with the wrong gem (Grok 4.20 used `ruby-openai` from a `dev/test`-only Gemfile group → NameError in production).
- **The most reliable benchmark path** in this repo today is OpenRouter plus the two-phase continuation flow.
- **The follow-up prompt** materially improved run quality because it forced models to validate boot, Docker build, and Compose startup instead of stopping after code generation.
- `opencode` can continue an existing session for the second prompt, and that works well enough for the benchmark harness.
- The `opencode export` step is still flaky in this environment. The run metadata captures the session ID, but the exported JSON snapshot was not emitted in the latest successful reruns.
- **Local Ollama runs** are still useful for warmup experiments, but not reliable enough for unattended coding benchmarks on this hardware. llama-swap resolved most of these reliability issues (see below).
- If local serving matters, **llama-swap with HuggingFace GGUFs** is the recommended path. It resolved all the model loading, context drift, and lifecycle issues that made Ollama impractical for unattended runs.

## GPT 5.4 Pro: Tool Calling Incompatibility

GPT 5.4 Pro is the only OpenRouter cloud model that consistently fails the benchmark. Two separate runs both failed to complete:

- **Run 1:** Generated 1278 files over 46 minutes, then hit an OpenRouter credit exhaustion error that looped indefinitely (the error loop bug, now fixed). `finish_reason: tool-calls`, never reached `stop`.
- **Run 2:** Generated 1118 files over 48 minutes, ended with `finish_reason: tool-calls` and `works_as_intended: partial`. The project had code but was missing tests, Docker files, and README. Only 624 output tokens were recorded in the event stream despite 1118 files created, suggesting event capture was incomplete.

**Hypothesis:** GPT 5.4 is heavily trained for OpenAI's native function calling schema (`tool_choice`, `tools` with JSON schemas). The benchmark routes through opencode → OpenRouter → GPT 5.4, with tool schemas being translated at each hop. If GPT emits tool calls in a format that OpenRouter or opencode doesn't parse correctly, the agent loop breaks before the task completes.

**Supporting evidence:**
- Every other OpenRouter model (Claude Opus, Claude Sonnet, Kimi K2.5, DeepSeek V3.2, MiniMax M2.7, GLM 5, Qwen 3.6 Plus, Step 3.5 Flash) reached `finish_reason: stop` with successful two-phase completion.
- GPT is the only model that ends with `finish_reason: tool-calls` — it wants to keep calling tools but the loop terminates.
- The low recorded output token count (624) relative to the actual generated files (1118) suggests the ndjson event stream is not capturing GPT's tool outputs correctly.

**Important caveat:** This failure reflects an **opencode/OpenRouter tooling limitation**, not a GPT 5.4 Pro model capability issue. In the author's experience using GPT 5.4 Pro through native OpenAI tooling (Codex CLI, ChatGPT Pro), it performs on par with Claude Opus 4.6 for autonomous coding tasks. The benchmark's opencode-through-OpenRouter path cannot handle OpenAI's function calling response format, making this an unfair test of GPT's coding ability.

**Fair comparison path:** To properly benchmark GPT 5.4 Pro, it would need to run in its native tool environment — either through OpenAI's Codex agent tooling or the ChatGPT Pro ($200/mo) plan which provides unlimited GPT 5.4 Pro access with native function calling.

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
