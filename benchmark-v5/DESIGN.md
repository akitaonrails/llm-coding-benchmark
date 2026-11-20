# Benchmark v5 — Cost, Speed & Prompt-Caching Economics

**Status:** Active design (2026-11-19). Supersedes the unimplemented Oct 9 autonomy proposal (archived at [DESIGN.autonomy-proposal.md](DESIGN.autonomy-proposal.md)).

## 1. Premise & Objective

Commercial Tier-A models have converged on the ability to build standard full-stack web applications from scratch. v5 stops treating "can it build a Rails app?" as the differentiator and instead measures **what it actually costs and how long it takes** to ship a verified, working web app using each provider's **preferred native harness** — with full, cache-aware token accounting.

Primary questions:
1. **Total API-equivalent cost ($)** to build and validate a working greenfield Rails app.
2. **Prompt-caching impact**: cache hit rate, cache-write overhead (1.25×/2×), actual cost vs. no-cache counterfactual cost, and net savings (%).
3. **Wall-clock time (minutes)** and output/reasoning verbosity.
4. **Subscription break-even** (runs/month on Claude Max, ChatGPT Pro, Google AI Pro/Ultra, Z.ai, Kimi, Muse).

## 2. Task Brief (v2 14-Goal Greenfield Rails App, 2 Phases)

v5 reuses the **v2 greenfield RubyLLM Rails chat SPA** (a richer, 14-goal evolution of v1: G1–G14 — Tailwind, Hotwire/Stimulus/Turbo Streams, true streaming, multi-turn payload test, concurrency-safe bounded persistence under `WEB_CONCURRENCY=2`, `server_time` + `calculator` tools, structured-output auto-title, token budgeting, Minitest/SimpleCov, RuboCop/Brakeman/bundle-audit, production Dockerfile + Docker Compose).

- **Phase 1 (Build):** [prompts/phase1_build.txt](prompts/phase1_build.txt)
- **Phase 2 (Validate):** [prompts/phase2_validate.txt](prompts/phase2_validate.txt) — local boot, streaming proof, tool proof, multi-worker restart survival, test/CI gates, `docker build`, and `docker compose up --build`.

### Standardized Nudge Policy (Up to 2 Nudges Allowed)

Because v5 focuses on **total cost to a working deliverable**, if a model finishes Phase 2 with failing tests, a broken boot, or a failing Docker/Compose build (especially smaller/cheaper models), the runner allows **up to 2 standardized nudges**:
- **Nudge 1 ([prompts/nudge1.txt](prompts/nudge1.txt)):** Generic verification & completion prompt (no task-specific hints).
- **Nudge 2 ([prompts/nudge2.txt](prompts/nudge2.txt)):** Generic failure-investigation prompt pointing only to the failing command category (e.g., tests / boot / Docker).

Every nudge's tokens, cache usage, cost, and wall time are **summed into the run's total cost and time** and explicitly annotated (`nudges: 0 | 1 | 2`) in the final report.

## 3. Candidate Roster (Newest Tier-A Family Models Only)

Scoped to current v4 Tier-A families (excluding Xiaomi, Nex, Sakana, StepFun per user scope):
- **Anthropic (`claude`):** Claude Fable 5.2, Claude Mythos 5.2 *(if account access available)*, Claude Opus 5.5, Claude Sonnet 5.5
- **OpenAI (`codex`):** GPT-6.2 Astra, GPT-6.2 Sol, GPT-6.1 Terra, GPT-6 Luna
- **Google (`agy`):** Gemini 4 Carbon, Gemini 4 Neon, Gemini 4 Hydrogen
- **xAI (`grok`):** Grok 4.7
- **Z.ai (`zcode`):** GLM-5.3
- **Moonshot (`kimi`):** Kimi K3.1 Pro
- **Alibaba (`qwen`):** Qwen 4 Max
- **DeepSeek (`opencode`):** DeepSeek V4.1 Flash (1017), DeepSeek V4 Pro (0813)
- **Meta (`muse`):** Muse Wonder 1.0

## 4. Isolation & Anti-Cheating Controls

Every run executes under strict isolation:
- Atomic same-filesystem shield moving sibling `results*`, `docs/success_report*.md`, `CLAUDE.md`, and `.agents/skills/benchmark-audit` outside the repo before runs and restoring after.
- Per-workspace `git init` + `GIT_CEILING_DIRECTORIES` pointing to the results parent directory so `git log` / `git show` cannot traverse into the benchmark repo.
- Isolated `HOME` / `XDG_CONFIG_HOME` for `claude`, `muse`, and `opencode` so user-level MCP servers, personal skills, and plugins never contaminate token counts or behavior.

## 5. Cache-Aware Cost Accounting

All harnesses normalize to a single per-phase token schema:
- `input_uncached`, `cache_read`, `cache_write` (split `5m` vs `1h` where exposed), `output`, `reasoning` (verified per harness to prevent double-counting when `output` already includes `reasoning`, as confirmed on `agy` 1.5.13).
- **Actual Cost ($):** `input_uncached × r_in + cache_read × r_cr + cache_write × r_cw + billable_output × r_out` (with long-context step-up where applicable).
- **No-Cache Counterfactual ($):** `(input_uncached + cache_read + cache_write) × r_in + billable_output × r_out`.
- **Net Cache Savings ($ and %):** `No-Cache − Actual`.
- **Cache Hit Ratio (%):** `cache_read / (input_uncached + cache_read + cache_write)`.

Pricing source of truth: [config/pricing_v5.json](../config/pricing_v5.json) and [docs/pricing.md](../docs/pricing.md).
