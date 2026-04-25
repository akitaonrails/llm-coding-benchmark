# Forced-Delegation Multi-Agent Benchmark — Round 2 Deep Analysis

This is the standardized-rubric audit of the **forced-delegation** experiment, scoring each forced variant on the same 0-100 / 8-dimension rubric used in [`success_report.md`](success_report.md), and comparing each forced run head-to-head against the **same planner model running solo**.

If you want background on why forcing was attempted (community pushback on the free-choice "zero delegations" finding) and the general headline numbers, read [`success_report.multi_model.md`](success_report.multi_model.md) first. This document is the deeper per-variant audit and cost/quality comparison.

---

## TL;DR

**Forcing the orchestrator pattern produces equivalent or slightly-lower quality at substantially higher cost and wall time, with one striking exception.** The exception is when the harness itself was contaminating the planner — Claude Code's solo Opus 4.7 hallucinated `chat.complete` (Tier 3 in the original Round 1 report); forcing the work through Sonnet/Haiku coders **repaired** that regression because the executor wasn't subject to the planner's harness-context bloat.

Of seven attempts, **five produced auditable artifacts** (3 Tier A + 2 retry-stalls), one was a **VALIDATE-phase timeout with shippable artifact** (95/100), and two **retried-and-stalled** at the orchestration boundary (the original Round 1 first runs reported in `success_report.multi_model.md` produced ~70-88/100 artifacts but were lost when the retries collapsed without writing files).

---

## Round 2 Variants Audited

| Slug | Planner | Subagent | Harness |
|---|---|---|---|
| `claude_opus_sonnet_forced` | Opus 4.7 | Sonnet 4.6 (`sonnet-coder`) | Claude Code |
| `claude_opus_haiku_forced` | Opus 4.7 | Haiku 4.5 (`haiku-coder`) | Claude Code |
| `opencode_opus_kimi_forced` | Opus 4.7 | Kimi K2.6 (`coder`) | opencode |
| `opencode_opus_glm_forced` | Opus 4.7 | GLM 5.1 (Z.ai) | opencode |
| `opencode_opus_qwen_forced` | Opus 4.7 | Qwen 3.6 35B local | opencode |
| `gpt_5_4_multi_balanced_forced` | GPT 5.4 xHigh | GPT 5.4 medium | Codex |
| `gpt_5_4_multi_faster_forced` | GPT 5.4 xHigh | GPT 5.4 low | Codex |

Each pair runs the same forcing prompt: [`prompts/benchmark_prompt_forced_delegation.txt`](../prompts/benchmark_prompt_forced_delegation.txt) — explicit `plan → delegate → converge → validate` workflow that forbids the planner from using Write/Edit/Bash and requires every code change to flow through the subagent via `Task` / `spawn_agent`.

---

## Per-Variant Audits (standardized rubric)

### `claude_opus_sonnet_forced` — **92/100, Tier A**

Production-quality Rails 8 chat app, real verified RubyLLM API, real Turbo Streams, mocha + WebMock tests that actually exercise the HTTPS path, working multi-stage Dockerfile + compose.

| Dimension | Score | Notes |
|---|---:|---|
| Deliverable completeness | 24/25 | Dockerfile (Ruby 4.0.2, multi-stage), compose, hand-written README, all required gems in Gemfile, no nested subdir. |
| RubyLLM integration | 20/20 | `RubyLLM.chat(model:, provider:)`, `with_instructions`, `add_message(role:, content:)`, `chat.ask`, `reply.content` — all verified against `chat.rb:35,42,139,173`. |
| Test quality | 14/15 | `chat_service_test.rb` stubs the real OpenRouter HTTPS endpoint and asserts the request body contains prior turns (lines 56-71); error path covered. Missing API-key test the only gap. |
| Error handling | 9/10 | Service rescues `RubyLLM::Error`; controller rescues `ChatService::Error` and renders 422 turbo_stream flash. No env-var preflight. |
| Persistence | 6/10 | Singleton + Mutex in-process store. Thread-safe within one process; broken under multi-worker Puma. README acknowledges. |
| Hotwire/Turbo/Stimulus | 10/10 | Real `turbo_stream.append/update/replace`. Three Stimulus controllers (autoscroll with MutationObserver, message_form with autogrow + Enter-to-submit, flash). |
| Architecture | 5/5 | Clean ChatService PORO, ChatSessionStore PORO, thin controllers, partials decomposed, initializers centralized. |
| Production readiness | 4/5 | ERB-escaped LLM output, CSRF default, secrets from env only, Dockerfile non-root user. Singleton store breaks horizontal scaling (-1). |

**Killer strength**: WebMock assertion that the *second* outbound request body contains prior conversation turns (`chat_service_test.rb:56-71`) — catches multi-turn regressions for real, not against a fake.
**Killer weakness**: `ChatSessionStore` is a process-local Singleton — under Puma cluster mode, conversations randomly disappear depending on which worker handles the request.

---

### `claude_opus_haiku_forced` — **90/100, Tier A**

Same shape as the Sonnet variant, with a more aggressive **dual test strategy** (FakeChat for unit isolation + a separate WebMock test that drives the real `RubyLLM::Chat` builder against a stubbed OpenRouter HTTPS endpoint with `assert_requested`).

| Dimension | Score | Notes |
|---|---:|---|
| Deliverable completeness | 24/25 | Dockerfile (Ruby 4.0.2, multi-stage), compose, real README, full Gemfile. -1 for missing `.gitignore`. |
| RubyLLM integration | 20/20 | All real API. Model id `anthropic/claude-sonnet-4.6` exists in registry (`models.json:29888`). |
| Test quality | 14/15 | Two-layer suite: `FakeChat` for fast unit + `chat_service_openrouter_test.rb:5-34` exercising real `RubyLLM.chat` with WebMock. Integration test posts turbo-stream and asserts rendered frame. |
| Error handling | 8/10 | `rescue StandardError` returns Result struct; controller renders error inline as assistant bubble. No boot-time env-var check. |
| Persistence | 5/10 | `ConversationStore` is a Singleton with `Concurrent::Map`. Multi-Puma-worker = split brain. |
| Hotwire/Turbo/Stimulus | 10/10 | Real Turbo Streams, two Stimulus controllers (autoscroll with MutationObserver, composer with Enter-to-submit), partials decomposed. |
| Architecture | 5/5 | DI-injected `chat_builder:` parameter on `ChatService` makes the test seam clean. |
| Production readiness | 4/5 | No leaked secrets, non-root container, healthcheck, WebMock blocks external in tests. Singleton -1. |

**Killer strength**: dual test strategy — one suite for speed, one suite that proves the wire shape via `assert_requested` against a stubbed OpenRouter URL.
**Killer weakness**: same Singleton store problem as the Sonnet variant — single Puma worker only.

---

### `opencode_opus_kimi_forced` — **95/100, Tier A** (highest of all 7)

Near-textbook artifact. The harness killed this run mid-VALIDATE phase (no-progress timeout 6 min after the planner dispatched the validation Task), so docker compose was never confirmed to boot — but static review predicts the artifact would survive validation.

| Dimension | Score | Notes |
|---|---:|---|
| Deliverable completeness | 24/25 | Multi-stage Dockerfile (Ruby 3.4.9), compose.yaml, real README, full Gemfile with WebMock. -1 for committed `master.key`. |
| RubyLLM integration | 20/20 | All real API. `claude-sonnet-4-5` alias verified at `aliases.json:75-78`. |
| Test quality | 14/15 | Three service tests stub the real `https://openrouter.ai/api/v1/chat/completions` URL and assert the request body replays full history (`chat_service_test.rb:34-57`). Controller tests exercise real Turbo Stream. -1 for missing API-failure test. |
| Error handling | 9/10 | `rescue StandardError` with logging + user-visible degraded message. No upfront missing-key preflight. |
| Persistence | 9/10 | Session cookie with symbol/string normalization (`chats_controller.rb:51-57`); single-process safe. Cookie size cap is the only real concern. |
| Hotwire/Turbo/Stimulus | 10/10 | Real Turbo Stream append+replace, two distinct Stimulus controllers, partials decomposed. |
| Architecture | 5/5 | Service object, thin controller, partials, initializer for config. |
| Production readiness | 4/5 | XSS-safe (`whitespace-pre-wrap` + default ERB escaping), CSRF default. `master.key` committed (-1). Compose has no healthcheck and a placeholder SECRET_KEY_BASE fallback. |

**Killer strength**: WebMock stubs that hit the *real* OpenRouter URL and assert the actual `messages[]` payload includes prior turns — would catch a regression to one-shot mode.
**Killer weakness**: `compose.yaml` is a single-service stub with no healthcheck and a fallback dummy `SECRET_KEY_BASE` — barely more than `docker run`.

**Validate-phase timeout commentary**: The auditor's static review of the artifact predicts it would survive `docker compose up --build`. Dockerfile is the standard Rails 8 multi-stage with valid Ruby 3.4.9 and a working entrypoint; `Gemfile.lock` pins `ruby_llm 1.14.1`; tests are real and would run. The most likely cause of the 25-min hang is `docker build` (gem compilation under slow disk) or `bundle install` inside the container — not a code defect. **No artifact bug visible from static review would have downgraded the score.** That said, the run is reported as `failed` in `result.json` because the harness no-progress watchdog tripped, and we do not have empirical confirmation that compose came up. **The score stands at 95/100, Tier A, with the validation-completion question explicitly open.**

---

### `opencode_opus_glm_forced` — **0/100, Tier D** (retry stalled)

The first attempt (reported in `success_report.multi_model.md`) produced a roughly Tier-A artifact at ~88/100 with 1965 files and 10 delegations, then stalled in phase 2 validation. After the project directory was wiped to retry, the re-run **stalled at the orchestration boundary** — Opus generated a TODO plan, announced "Now I'll dispatch Subtask 1 to the coder," then sat for 6 minutes without ever emitting the `task` tool call. SIGTERM at 384s, **0 files written**, 973 output tokens.

| Dimension | Score | Notes |
|---|---:|---|
| All 8 dimensions | **0** | Empty `project/` directory. Nothing to evaluate. |

**Killer weakness**: forced-delegation guardrail froze the planner into inaction at the dispatch boundary. Same failure mode reproduced on the qwen retry — see below.

---

### `opencode_opus_qwen_forced` — **0/100, Tier D** (retry stalled)

Same story as glm. Original first run (in `success_report.multi_model.md` notes) produced ~2038 files / 7 delegations / Tier 2 artifact (`reply` instead of `reply.content` bug). Retry stalled at the same orchestration boundary as glm: 16-subtask plan written, "Starting Subtask 1" announced, then 6 minutes of silence until SIGTERM. **0 files written.**

| Dimension | Score | Notes |
|---|---:|---|
| All 8 dimensions | **0** | Empty `project/` directory. |

The plan quality before the stall was actually excellent — well-decomposed 16-subtask breakdown with correct gem list and proper test guidance. The `task` tool just never fired.

**Implication**: opencode's `task` dispatcher appears to have a reproducibility issue when the subagent is on a different provider lane than the planner (Z.ai for glm, llama-swap for qwen, both different from the OpenRouter-hosted planner). The kimi variant — both planner and subagent on OpenRouter — did not exhibit this stall.

---

### `gpt_5_4_multi_balanced_forced` — **94/100, Tier A**

Tight, well-architected Rails 8.1 chat app on Ruby 4.0.3 with verified-correct RubyLLM API usage, real Turbo Streams, mocked WebMock tests that exercise the actual `ruby_llm` HTTP path, and full Docker/compose/CI tooling.

| Dimension | Score | Notes |
|---|---:|---|
| Deliverable completeness | 24/25 | Multi-stage Dockerfile (Ruby 4.0.3), compose, real README, full Gemfile with WebMock, `bin/ci`. -1 for committed `master.key`. |
| RubyLLM integration | 20/20 | `RubyLLM.chat(model:, provider: :openrouter)`, `chat.add_message(normalized)` (single-hash arg matching `chat.rb:173`), `chat.ask`, `response.content.to_s`. Multi-turn via add_message loop. |
| Test quality | 14/15 | WebMock stubs the actual OpenRouter HTTP endpoint with full body assertion. **Spy module `RubyLLMChatSpy` prepends real `RubyLLM::Chat`** and asserts `ask` was called — proves real code path was exercised, not a fake. |
| Error handling | 10/10 | `ensure_api_key!` preflight, rescue for `RubyLLM::ConfigurationError` and `RubyLLM::Error, Faraday::Error`. Controller renders error as visible system bubble. |
| Persistence | 7/10 | Session-cookie transcript with 12-message cap. Cookie-safe but bounded; not shared across devices. |
| Hotwire/Turbo/Stimulus | 10/10 | Real `turbo_stream.append/replace`, two Stimulus controllers (composer with autosize + Cmd+Enter, transcript with MutationObserver auto-scroll). |
| Architecture | 5/5 | `ChatClient` service separated, controller concern `ChatSession`, view partials, custom error class hierarchy. |
| Production readiness | 4/5 | No `.env` committed, `.gitignore` covers `.env*`, Dockerfile drops to non-root, compose enforces required env. -1 for committed `master.key`. |

**Killer strength**: the spy-prepend test pattern proves the real `RubyLLM::Chat#ask` is invoked — green tests cannot pass against a hallucinated API.
**Killer weakness**: `config/master.key` committed — acceptable for a throwaway demo but the prompt explicitly forbids secrets in source files.

---

### `gpt_5_4_multi_faster_forced` — **94/100, Tier A**

Same shape and same score as the balanced variant — clean Rails 8.1 + Ruby 3.4.9 chat app, real RubyLLM integration, full Turbo wiring, WebMock-backed integration tests, working multi-stage Dockerfile + compose.

| Dimension | Score | Notes |
|---|---:|---|
| Deliverable completeness | 24/25 | Multi-stage Dockerfile (Ruby 3.4.9, non-root), compose, real README, full Gemfile, no nested subdir. |
| RubyLLM integration | 18/20 | All real API but pushes system messages via `add_message(role: :system, ...)` instead of the canonical `with_instructions` (-2). |
| Test quality | 14/15 | `chat_client_test.rb:7-54` exercises the LLM path via WebMock against the real OpenRouter URL with payload-shape assertion. Error-path tests for missing key + 503. Integration tests cover Turbo Stream success/failure/clear. |
| Error handling | 10/10 | Preflight blank check, specific rescues for `ConfigurationError`, `ModelNotFoundError`, `RubyLLM::Error`, `Faraday::Error`, `Timeout::Error`. Controller catches and re-renders with flash + draft preserved. |
| Persistence | 8/10 | Session cookie via `session[:chat_transcript]`. Multi-worker-OK; capped ~4KB. |
| Hotwire/Turbo/Stimulus | 10/10 | Three `turbo_stream.replace` targets per response, turbo frames in views, real Stimulus composer with autosize/keydown/submit lifecycle. |
| Architecture | 5/5 | PORO `ChatClient` service, thin controllers, view partials, helpers extracted. |
| Production readiness | 5/5 | No `.env` committed, no secrets in source, escaped output via `simple_format(h(...))`, non-root container, healthcheck wired. |

**Killer strength**: WebMock test that asserts the exact OpenRouter payload (`chat_client_test.rb:30-53`) — proves the integration would actually wire correctly at runtime.
**Killer weakness**: system prompts via `add_message(role: :system, ...)` instead of `with_instructions` — works (system role is supported) but couples the test to RubyLLM's `developer` role rewrite.

---

## Forced vs Solo: Same Planner, Different Setup

For each forced variant, this section compares it head-to-head against the **same planner model running solo** (no subagent, same Rails brief, same audit rubric). This is the apples-to-apples comparison that the round 2 experiment was designed to enable.

### Claude Code Opus 4.7 + Sonnet/Haiku coder vs solo Opus 4.7 in Claude Code

| Run | Time | Cost | Score | Tier | Notes |
|---|---:|---:|---:|---:|---|
| `claude_opus_alone` (solo, free-choice round) | **11 min** | **$6.74** | ~50–60 (Tier 3) | C/D | Hallucinated `chat.complete`. Tests mocked the hallucination so they passed green. |
| `claude_opus_sonnet_forced` | 25 min | $5.77 | **92** | **A** | Sonnet wrote the integration; no hallucination. |
| `claude_opus_haiku_forced` | 19 min | $3.49 | **90** | **A** | Haiku wrote the integration; no hallucination. |

**The forced variants REPAIRED the harness regression.** Solo Opus 4.7 in Claude Code produced Tier 3 code (the well-documented `chat.complete` hallucination — see `success_report.multi_model.md` Part 1). When the implementation work was forced through Sonnet or Haiku, the executor was insulated from whatever in the Opus-in-Claude-Code context window was nudging it toward the OpenAI-SDK mental model. **Quality went up, cost stayed flat or went down.**

This is the only one of the three harness pairings where forcing was a clear win. It only worked because the solo baseline was already broken in this harness.

### opencode Opus 4.7 + (Kimi/GLM/Qwen) vs solo Opus 4.7 in opencode

| Run | Time | Cost | Score | Tier | Notes |
|---|---:|---:|---:|---:|---|
| `claude_opus_4_7` (solo, opencode) | **18 min** | **~$1.10** | **97** | **A** | Benchmark leader. The "true" Opus baseline. |
| `opencode_opus_kimi_forced` | 25 min | ~$2–3 (planner) | 95 | A | Slightly lower score, ~2× cost, slower. VALIDATE timeout open. |
| `opencode_opus_glm_forced` (retry) | 6 min | ~$0.26 | **0** | **D** | Stalled at task dispatch. 0 files. |
| `opencode_opus_qwen_forced` (retry) | 6 min | ~$0.25 | **0** | **D** | Stalled at task dispatch. 0 files. |

**Forcing in opencode is at best marginally degrading, at worst a complete failure.** The kimi pairing — same provider lane (OpenRouter) for planner and subagent — works, scoring 95 vs the 97 solo baseline at roughly 2× the cost. The glm and qwen pairings — different provider lanes (Z.ai and llama-swap) — exhibit a reproducible task-dispatcher stall. (Their original Round 1 first runs, before being wiped for retry, did produce ~88 and ~70 artifacts respectively per the `success_report.multi_model.md` notes; the retries broke completely.)

### Codex GPT 5.4 xHigh + GPT 5.4 (medium/low) vs solo GPT 5.4 xHigh

| Run | Time | Cost | Score | Tier | Notes |
|---|---:|---:|---:|---:|---|
| `gpt_5_4_codex` (solo xHigh) | **22 min** | **~$16** | **97** | **A** | Most production-polish in the benchmark; tied with Opus on score. |
| `gpt_5_4_multi_balanced_forced` | 30 min | ~$1–3 | 94 | A | xHigh planner + medium executor. ~85% cost reduction. |
| `gpt_5_4_multi_faster_forced` | 53 min | ~$3–6 | 94 | A | xHigh planner + low executor. Slowest run, but still cheaper than solo xHigh. |

**Codex forced delegation is the only pairing where forcing improves the cost picture.** Quality drops 3 points (97 → 94, both still Tier A). Cost drops 50–85% by pushing the execution work to a cheaper reasoning tier. Wall time goes up 35-140% as a coordination penalty. **For deployments where you can absorb the wall-time cost, `gpt_5_4_multi_balanced_forced` is the most cost-efficient way to get Tier A from this benchmark.**

The reason this works in Codex but not in opencode is structural: Codex's `spawn_agent` runs the executor in the same harness with the same tool sandbox; opencode's `task` tool dispatches across provider boundaries that introduce latency and (in glm/qwen's case) reproducibility issues.

---

## Cross-Variant Observations

### 1. Variance is small among Tier A forced runs

Five of the seven forced variants (3 successful + 2 successful Round 1 first-runs from the previous report's notes) cluster in the **88–95 range**. The rubric was designed with low variance in mind on cohesive Rails work, and the forced runs confirm it: when the executor model is competent, the artifacts converge to a similar shape (Singleton/cookie store, multi-stage Dockerfile, WebMock-stubbed tests, real Turbo Streams).

### 2. Test-quality patterns repeat across executors

Every Tier A forced run independently arrived at the same WebMock pattern: stub the real OpenRouter HTTPS URL, assert the request body shape, ideally assert that the *second* request includes prior turns. This is more rigorous than the solo Opus baseline's FakeChat-only suite, suggesting the planner's CONVERGE-phase verification rounds nudged executors toward better tests than they would have written unilaterally.

### 3. Persistence is the recurring weak spot

Three of the four Tier A forced runs use a process-local Singleton (`ChatSessionStore`/`ConversationStore`) that breaks under multi-worker Puma. The kimi and balanced variants use session-cookie storage which is multi-worker safe but capped at ~4KB. None of the forced runs implemented Redis/Rails.cache. **The orchestrator pattern doesn't help with persistence design choices** — that's still a one-shot decision the planner makes once and the executor implements literally.

### 4. The "harness regression repair" effect is only visible because solo Opus in Claude Code was broken

The strongest single argument for forced delegation in this dataset is the Claude Code repair (Tier 3 → Tier A). But that's a special case: solo Opus 4.7 in opencode and solo GPT 5.4 in Codex were both already Tier A at 97/100. The forced variants in those harnesses only matched (kimi 95) or slightly lagged (Codex 94) the solo baseline, while costing more in dollars or wall time.

If you're running on a harness that produces good solo output, forcing delegation is a wash. If you're running on a harness that's actively degrading your model, forcing delegation can route around the damage — but at that point the cleaner fix is to switch harnesses.

### 5. Forced delegation has a real failure mode that solo runs don't

Two of the seven retries (glm, qwen) produced **zero files** because the planner stalled at the task-dispatch boundary. Solo runs cannot fail this way — there is no dispatch boundary to stall at. The forcing prompt + cross-provider task dispatcher creates a new failure surface that simply does not exist in solo runs.

---

## Round 2.5: harness-fix reruns and the attribution problem

After publishing the original Round 2 report, the failed and degraded variants were re-run with two harness changes:

1. **`--no-progress-minutes 15`** (vs default 6) — to test whether the cross-provider stall was a true hang or just slow init
2. **Reasoning passthrough** on subagent provider entries (`scripts/benchmark/config.py` patch emitting `"reasoning": true` on the provider model entry for cheap-cloud reasoning subagents) — to test whether the empty-`<task_result>` mode was opencode dropping reasoning content

See [`orchestration_traces.md`](orchestration_traces.md) — the "Harness fix attempts (Round 2.5)" section — for the per-variant dispatch tallies and the bottom-line verdict on each fix. Short version: the watchdog change works (the cross-provider stall was slow Z.ai/llama-swap init, not a hang), but reasoning passthrough was a no-op (the cheap-cloud subagents still return empty result envelopes). What rescued the runs that "completed" was Opus's iteration discipline: filesystem inspection between dispatches, fallback to opencode's built-in `general` agent (which is just Opus again) when the configured `coder` produced empty results.

### Re-audit results vs original-run scores and solo baselines

Each rerun artifact was re-scored against the same standardized rubric used elsewhere in this report. The attribution column is critical: in three of four cases the score reflects what Opus-as-fallback produced, NOT what the named subagent produced.

| Variant (rerun) | Rerun score | Tier | Δ vs Opus solo (97) | Δ vs subagent solo | Real attribution |
|---|---:|---|---:|---:|---|
| `opus + glm` | **93** | A | -4 | **+47** (GLM 5.1 solo: 46, Tier C) | **Genuinely GLM-written under Opus direction.** All 4 dispatches went to GLM; no fallback. The hallucinated fluent DSL (`c.user/c.assistant`) that tanked solo GLM is absent from this artifact — Opus's prescriptive subtask prompts constrained GLM's API surface choices |
| `opus + qwen-local` | **92** | A | -5 | n/a (no comparable solo) | **Mostly Opus-via-`general` fallback.** 6 of 8 substantive dispatches via `general`. Qwen 3.6 35B local contributed effectively zero substantive code |
| `opus + qwen3.6plus` | **92** | A | -5 | +21 nominal (Qwen 3.6 Plus solo: 71) | **Opus 4.7 solo, mislabeled.** Phase 2 transcript shows Opus *explicitly self-overrode* the delegation rule ("deliberate, documented departure from the phase-1 delegation constraint because the coder is a hard blocker"). Qwen 3.6 Plus contributed zero. The +21 over Qwen solo is meaningless because Qwen wasn't measured |
| `opus + deepseek` | **95** | A | -2 | +26 nominal (DeepSeek V4 Pro solo: 69) | **Mostly Opus-via-`general` fallback.** 12 of 14 substantive dispatches via `general`. DeepSeek V4 Pro contributed 2 dispatches, both empty |

### The one clean signal: GLM 5.1 lift

The GLM rerun is the only case where the named subagent actually wrote the code AND the rubric score moved. **GLM jumped from 46/100 (Tier C, hallucinated fluent DSL) to 93/100 (Tier A, real API).** That's a 47-point lift, attributable to:

1. **Constrained API surface**: Opus's task prompts referenced specific real RubyLLM methods (`RubyLLM.chat`, `with_instructions`, `add_message`, `ask`, `response.content`) by name. GLM had no need to invent the fluent DSL because Opus had already specified the real one.
2. **Decomposed scope**: Each dispatch was a tightly-scoped subtask with explicit acceptance criteria. The "build a chat app" prompt that triggered solo GLM's hallucinated abstractions was never given to the subagent — only "implement this controller method against this service contract" sized chunks were.
3. **Verification rounds**: Opus inspected the output between dispatches and would have caught a fluent-DSL regression in the first dispatch (it didn't have to, but the discipline was there).

This is the strongest single piece of evidence in the entire experiment that **forced delegation can elevate a Tier-C executor to Tier A by transferring the planning model's API knowledge through prescriptive subtask prompts.** The "harness regression repair" finding from the Claude Code variants is the same mechanism in a different clothing — there too, an executor that wouldn't have produced clean RubyLLM code on its own (Opus-in-Claude-Code, which hallucinated `chat.complete`) was guided to clean output by a planner who'd already pinned the API surface.

### Why the other three reruns aren't measurements of the named subagents

For Qwen-local, Qwen 3.6 Plus, and DeepSeek V4 Pro, opencode's `task` envelope is broken in a way that returns empty result bodies to the planner regardless of whether the subagent has actually performed work. The cheap-cloud models silently *do* execute shell commands and write files, but opencode's task-result parsing doesn't capture their final assistant message into the `<task_result>` envelope.

When this happens, two things determine outcome:

1. **Whether the planner trusts on-disk evidence over the empty envelope** (Opus does; GPT 5.5 does not — see GPT 5.5 reruns below)
2. **Whether the planner falls back to a different subagent type** (`general`, which is just Opus, vs continuing to dispatch to the broken `coder`)

In the qwen-local and deepseek cases, Opus tried `coder` 1-2 times, saw empty results AND no progress on disk, then routed all subsequent work to `general`. The named subagent contributed effectively zero code. Their high scores measure *Opus's ability to recover from a broken subagent*, not the subagent's capability.

In the qwen3.6plus case, Opus went a step further and explicitly stopped using the delegation harness mid-run, declaring the configured `coder` a "hard blocker." That run is Opus solo, scored 92 — about 5 points below Opus solo's normal 97 because the orchestration overhead consumed some of the budget that would have gone into polish.

### GPT 5.5 reruns — same harness, different outcome

The same patched config was used for two GPT 5.5 + cheap-cloud-subagent reruns. Both **produced zero files** and failed:

| Variant | Status | Time | Files | Failure mode |
|---|---|---:|---:|---|
| `gpt55 + qwen3.6plus` | failed | 18.5m | 0 | Looped on empty `<task_result>` results, never inspected filesystem, watchdog killed it |
| `gpt55 + deepseek` | completed_with_errors | 3.8m | 0 | Accepted empty result as authoritative; declared "hard blocker: empty workspace" and bailed |

Under identical harness and subagent configurations, **Opus completes and GPT 5.5 fails — entirely because of how each planner handles a broken subagent envelope.** This is a real planner-capability finding orthogonal to the rubric: model evaluation of forced-delegation orchestration must include "does the planner verify subagent claims against ground truth, or does it trust the harness's reported output?"

### Updated takeaway

The conclusion in the original Round 2 section ("forcing the orchestrator pattern produces equivalent or slightly-lower quality at substantially higher cost") still holds for the Tier-A subagent pairings (Sonnet, Haiku, Kimi, GPT 5.4 medium/low) where the executor's protocol is compatible with the harness. The new evidence from Round 2.5 adds two refinements:

1. **For Tier-C subagents with known recall failures (GLM 5.1 fluent DSL):** forced delegation under a strong planner can produce a substantial quality lift (+47 points GLM 5.1 → A tier). The mechanism is API-surface constraint via prescriptive subtask prompts, not the delegation itself.
2. **For cheap-cloud subagents that opencode's `task` envelope can't parse (Qwen 3.6 Plus, DeepSeek V4 Pro):** the experiment is currently unmeasurable — the runs only "complete" because the planner falls back to a different subagent. The named subagent's true capability under forced delegation cannot be evaluated until the protocol gap is fixed upstream.

---

## Compliance with the "no direct Write/Edit/Bash" rule

(Re-extracted from the existing Round 2 report for completeness — these planner-only counts exclude tool calls made by subagents.)

| Variant | Direct Bash (planner) | Direct Write/Edit (planner) |
|---|---:|---:|
| `claude_opus_sonnet_forced` | 11 (all read-only: `ls`, `mise ls`, `cat`) | **0** |
| `claude_opus_haiku_forced` | 16 (read-only + 5 `ruby -e "..."` introspection probes) | **0** |
| `opencode_opus_kimi_forced` | 1 (`pwd && ls -la` workspace probe) | **0** |
| `opencode_opus_glm_forced` (retry) | 2 (read-only) | **0** |
| `opencode_opus_qwen_forced` (retry) | 1 (read-only) | **0** |
| `gpt_5_4_multi_balanced_forced` | **0** | **0** |
| `gpt_5_4_multi_faster_forced` | **0** | **0** |

**Codex's `spawn_agent` architecture is the only one that enforces planner compliance at the harness level.** Claude Code and opencode allowed the Opus planner to run inspection Bash commands despite the prompt forbidding it outright. The spirit was respected (zero file mutations by the planner) but the letter wasn't.

---

## Final Summary Table

| Variant | Score | Tier | Time | Cost | Tools | Verdict vs solo planner |
|---|---:|---|---:|---:|---|---|
| `claude_opus_sonnet_forced` | **92** | A | 25m | $5.77 | Claude Code | **+30+ points** vs Tier-3 solo Opus in Claude Code (harness regression repaired); slightly cheaper |
| `claude_opus_haiku_forced` | **90** | A | 19m | $3.49 | Claude Code | **+30+ points** vs solo; ~half the cost |
| `opencode_opus_kimi_forced` | **95** | A | 25m¹ | ~$2–3 | opencode | -2 vs solo Opus 97; ~2× cost; slower; VALIDATE timeout open |
| `opencode_opus_glm_forced`² | 0 | D | 6m³ | ~$0.26 | opencode | retry stalled; total failure (Round 1 first run was ~88) |
| `opencode_opus_qwen_forced`² | 0 | D | 6m³ | ~$0.25 | opencode | retry stalled; total failure (Round 1 first run was ~70) |
| `gpt_5_4_multi_balanced_forced` | **94** | A | 30m | ~$1–3 | Codex | -3 vs solo GPT 5.4 97; **80–85% cheaper**; 35% slower |
| `gpt_5_4_multi_faster_forced` | **94** | A | 53m | ~$3–6 | Codex | -3 vs solo GPT 5.4 97; **60–80% cheaper**; 140% slower |

¹ Killed by harness no-progress watchdog during VALIDATE phase. Artifact predicted to survive validation by static review; no empirical confirmation.
² First-run Round 1 results (~88 and ~70) were lost when project directories were wiped for retry; retries reproducibly stalled at task dispatch.
³ Retry stall time, not the original first-run time.

---

## Practical Takeaways

1. **For benchmarking purposes, solo > forced on cohesive greenfield Rails work.** Three of the three harness pairings produce equal-or-worse quality artifacts at higher dollar cost (Codex) or higher dollar+wall-time cost (opencode/Claude Code), with the single exception of repairing the Claude Code Opus regression.

2. **The Codex pairing is the only one where forcing trades cost for quality predictably.** If you specifically want a way to get Tier A from this benchmark for cheaper than solo xHigh, `gpt_5_4_multi_balanced_forced` is the answer (~80% cheaper at 3 points lower).

3. **opencode's cross-provider task dispatch has a reproducibility issue.** Two of three opencode forced retries stalled at zero files when the subagent was on a different provider lane than the planner. Same-lane (kimi via OpenRouter, planner via OpenRouter) worked. Worth investigating before deploying opencode multi-agent in production with mixed providers.

4. **The new failure mode introduced by forced delegation is real.** The "0 files written, 6 minutes of silence" stall pattern doesn't exist in solo runs. If you're running a forcing prompt in production, you need an upstream watchdog and a fallback to solo.

5. **The verification-rounds finding from the original Round 2 report holds.** WebMock multi-turn assertions, payload-shape assertions, and `assert_requested` proofs of real-API invocation appeared more consistently in the forced runs than in solo runs of the same planner model. The structured CONVERGE phase is plausibly responsible. **A simpler intervention — adding "after each major component is done, do a read-only verification pass" to the solo prompt — would likely capture most of this gain without the coordination overhead.**

6. **GLM 5.1 lift is the real headline of Round 2.5.** The only clean apples-to-apples measurement of a Tier-C subagent under Opus orchestration produced a **47-point quality jump** (46 → 93). Mechanism: prescriptive subtask prompts that name the real RubyLLM API methods kept GLM from inventing its own fluent DSL. **For models with known recall failures, forced delegation can substitute the planner's API knowledge for the executor's.**

7. **Three of four Round 2.5 reruns are not measurements of the named subagent.** Opus's filesystem-inspection workaround and `general` fallback rescued runs that opencode's `task` envelope had broken — producing Tier-A artifacts attributed to subagents that contributed effectively zero code. The harness gap means the cheap-cloud forced-delegation experiment is currently unmeasurable for Qwen 3.6 Plus, DeepSeek V4 Pro, and Qwen 3.6 35B local. GPT 5.5 in the same configuration produces zero files because it lacks Opus's recovery discipline.

---

## Cross-Reference

- [`success_report.md`](success_report.md) — main benchmark, full 23-model rankings, methodology
- [`success_report.multi_model.md`](success_report.multi_model.md) — Round 1 free-choice multi-agent + Round 2 first-run findings (overall narrative, headline numbers)
- [`success_report.nvidia.md`](success_report.nvidia.md) — NVIDIA RTX 5090 workstation profile + Claude reasoning distillation finding
- [`orchestration_traces.md`](orchestration_traces.md) — **per-variant forensic walkthrough** of what each planner said, what it dispatched, what came back, and where each pairing struggled
- [`audit_prompt_template.md`](audit_prompt_template.md) — the standardized 0-100 / 8-dimension rubric used in this report
- [`codex-integration.md`](codex-integration.md) — Codex CLI integration details
- [`prompts/benchmark_prompt_forced_delegation.txt`](../prompts/benchmark_prompt_forced_delegation.txt) — the forcing prompt used for all Round 2 runs
