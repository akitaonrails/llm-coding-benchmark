# Forced-Delegation Orchestration Traces

A forensic walkthrough of every forced-delegation variant: what each planner actually said, what it dispatched to its subagent, what came back, and where each pairing struggled. Extracted directly from the per-run event streams (`opencode-output.ndjson` / `stream.ndjson`).

This is the companion to [`success_report.multi_model_forced.md`](success_report.multi_model_forced.md) — that doc has the rubric scores and headline comparisons; this doc shows you the actual mechanics of what each planner-executor pair did under the hood.

---

## Reading these traces

Each variant section lists:

- **Stats**: planner text turns, planner-side tool calls, subagent dispatches, token totals
- **Planner narrative**: every assistant text turn the planner emitted, in order
- **Dispatches**: every Task / spawn_agent call with a snippet of the prompt sent and the snippet returned
- **Where it struggled**: the specific failure mode the trace reveals

For full per-dispatch detail, the source ndjson files are linked at the top of each section.

---

## opencode_opus_kimi_forced — clean three-dispatch flow

**Source**: `results/opencode_opus_kimi_forced/opencode-output.ndjson` · 51 events · planner cost $1.20

### Stats
- **9 planner text turns** · 19 planner-side tool calls (1 Bash + 4 TodoWrite + 11 Read + 3 Task)
- Planner tokens: 16 in / 18,709 out / 91K cache write / 326K cache read
- **3 task dispatches** to `coder` subagent (Kimi K2.6)
- All 3 returned substantive results; no fix-ups needed

### Planner narrative

1. "I'll orchestrate this build through the coder subagent. Let me start by planning the full scope, then delegate in batches."
2. "Empty workspace. Now let me build the full plan."
3. "## PLAN"
4. *(after dispatch 1)* "Bootstrap clean. Rails 8.1.3 / Ruby 3.4.9 / Tailwind v4 / Hotwire wired. Let me verify key files directly and check the Gemfile before batching the next subtasks."
5. "Good. The generator produced a decent Dockerfile; I need to augment (add ruby_llm gem) and adapt it (Rails 8 entrypoint expects DB prep — I'll need to remove that since we have no AR). Dispatching the big integration batch now."
6. *(after dispatch 2)* "Excellent. The coder verified the real ruby_llm API by reading gem source — `add_message` and `complete` are real methods, `claude-sonnet-4-5` is a real alias in `aliases.json`. Let me verify key files directly before moving on."
7. "All four files are clean and use the real verified API. Now the partial is rendered via `turbo_stream.append` — Turbo will only call Stimulus `turbo:submit-end` on the form being submitted..."
8. *(after dispatch 3)* "All tests pass, rubocop clean (0 offenses), brakeman 0 warnings, 95.83% line coverage, no secrets leaked. Let me verify the Dockerfile's entrypoint situation and compose.yaml directly, then dispatch validation."
9. "All good. Now VALIDATE phase — dispatch the full end-to-end validation."

### Dispatches

| # | Description | Sent (chars) | Returned (chars) | Outcome |
|---|---|---:|---:|---|
| 1 | Bootstrap Rails app in-place | 2817 | 3030 | Clean. Rails 8.1.3, Ruby 3.4.9, Tailwind v4, Hotwire wired |
| 2 | Add gems, RubyLLM init, controller, views, Stimulus, routes | 13997 | 4008 | Subagent verified real ruby_llm API by reading gem source |
| 3 | Write tests, fix Dockerfile, add compose, README | 15022 | 3421 | All tests pass, RuboCop clean, Brakeman 0 warnings, 95.83% coverage |

### Where it struggled
**It didn't, until VALIDATE.** The harness `no-progress` watchdog killed the run during the dispatched validation step — likely `docker build` taking longer than 6 minutes with no event emission. The artifact on disk is shippable; the validation just wasn't empirically confirmed.

---

## opencode_opus_glm_forced (retry) — stalled before first dispatch

**Source**: `results/opencode_opus_glm_forced/opencode-output.ndjson` · 16 events · planner cost $0.26

### Stats
- 3 planner text turns · 4 planner-side tool calls (2 Bash + 2 TodoWrite)
- Planner tokens: 9 in / 2,227 out / 27K cache write / 73K cache read
- **0 task dispatches** — never fired

### Planner narrative
1. "I'll start by exploring the workspace, then create a detailed plan, delegate all work to the coder subagent, and validate end-to-end."
2. "Good. Workspace is empty, Ruby 3.4.9, Rails 8.1.3 available via mise. Let me create the plan."
3. **"Now I'll dispatch Subtask 1 to the coder. It's a foundation step that must complete first before parallel work can start."**

Then 6 minutes of silence until SIGTERM.

### Where it struggled
**The `task` tool call never made it to the wire.** Planner announced the dispatch in a text turn, then the next event in the stream is the harness watchdog killing it. The Z.ai-hosted GLM 5.1 subagent was on a different provider lane than the OpenRouter-hosted Opus planner; opencode's task dispatcher appears to have a reproducibility issue at this boundary.

The first attempt of this variant (in the original Round 1 / Round 2 first-run data captured in `success_report.multi_model.md`) reportedly produced a Tier-A-ish artifact. The retry, on the same exact configuration, failed at this step. **Two stalls on the same boundary suggest the first run was the lucky one.**

---

## opencode_opus_qwen_forced (retry) — stalled before first dispatch

**Source**: `results/opencode_opus_qwen_forced/opencode-output.ndjson` · 13 events · planner cost $0.25

### Stats
- 3 planner text turns · 3 planner-side tool calls (1 Bash + 2 TodoWrite)
- Planner tokens: 8 in / 2,521 out / 27K cache write / 48K cache read
- **0 task dispatches**

### Planner narrative
1. "I'll orchestrate this build by planning the full scope first, then delegating all execution to the `coder` subagent."
2. "Empty workspace. Now let me build the full plan."
3. **"## 2. DELEGATE PHASE"**

Then silence → SIGTERM.

### Where it struggled
Identical failure mode to the glm retry. The Qwen 3.6 35B subagent runs locally on llama-swap — yet again a different provider lane than the planner. Same stall at the dispatch boundary.

---

## opencode_opus_qwen36plus_forced — subagent returned empty results, planner switched to `general`

**Source**: `results/opencode_opus_qwen36plus_forced/opencode-output.ndjson` · 90 events · planner cost $1.74

### Stats
- 16 planner text turns · 31 planner-side tool calls (10 Bash + 9 Read + 5 TodoWrite + 1 WebFetch + 6 Task)
- Planner tokens: 26 in / 29,349 out / 82K cache write / 988K cache read
- **6 task dispatches** — but first 2 returned **empty results** from Qwen 3.6 Plus

### Planner narrative (key moments)
1. "I'll orchestrate this build end-to-end..."
2. "Good — Ruby 3.4.9 and Rails 8.1.3 are available. Empty workspace."
3. *(after dispatch 1, looking at empty result)* **"The coder returned an empty result. Let me check the workspace state directly and retry with a cleaner dispatch."**
4. *(after dispatch 2, also empty)* **"Empty again. Let me check if the coder actually did something and just didn't report."**
5. **"The coder subagent is returning empty results and not doing any work. This may be a harness issue. Let me try with the `general` subagent instead."**
6. *(dispatch 3, sent to `general` not `coder`)* "Excellent — the `general` agent worked. The coder agent must have been misconfigured in this harness. I'll use `general` going forward."
7. *(dispatch 4 onwards via general)* "Now I'll dispatch a bigger batch: the full domain + controller + views + stimulus layer."
8. *(after dispatch 5)* "All 25 tests pass with 100% line / 83% branch coverage. Now the important note: the coder identified a real bug in `ChatService#reply_to` — the `rescue StandardError` swallows the `ArgumentError` raised for empty prompts."

### Dispatches

| # | Subagent | Description | Returned | Outcome |
|---|---|---|---:|---|
| 1 | `coder` (Qwen 3.6 Plus) | Subtask 1+2: skeleton + Gemfile | 117 chars (empty `<task_result>`) | **Silent no-op** |
| 2 | `coder` (Qwen 3.6 Plus) | Generate Rails 8 skeleton (retry) | 117 chars (empty) | **Silent no-op** |
| 3 | `general` (Opus fallback) | Generate Rails 8 skeleton | 3112 chars | Worked — `rails new` succeeded |
| 4 | `general` (Opus fallback) | Implement chat domain + controllers + views | 2829 chars | All four verifications pass |
| 5 | `general` (Opus fallback) | Write Minitest suite + SimpleCov | 1841 chars | All green, 100%/83% coverage |
| 6 | `general` (Opus fallback) | Add CI config, Dockerfile, compose, README | 3516 chars | All files present, `bin/ci` executable |

### Where it struggled
**Qwen 3.6 Plus as an opencode `coder` subagent silently returned empty `<task_result>` blocks.** The planner detected this on dispatch 2, attempted a third clean retry (still empty), then *correctly diagnosed it as a subagent issue and switched to opencode's built-in `general` agent.* That `general` subagent is a generic dispatch — likely backed by Opus again — so dispatches 3-6 weren't really testing the Qwen pairing at all; they were testing **Opus orchestrator + Opus fallback executor**, which is roughly equivalent to a solo Opus run with extra coordination overhead.

Then the run failed at no-progress timeout anyway — 113 files written before the stall — so this isn't a clean Tier-A artifact even after the fallback.

**Net finding**: Qwen 3.6 Plus does not function as a usable opencode subagent in this configuration. The model returns empty assistant outputs after receiving the dispatched prompt — possibly a tool-call serialization mismatch, possibly a behavior of the `:free` tier endpoint we used. Without further investigation we can only say: this pairing degenerates back to solo Opus.

---

## opencode_opus_deepseek_forced — same empty-result pattern as Qwen 3.6 Plus

**Source**: `results/opencode_opus_deepseek_forced/opencode-output.ndjson` (in-flight at time of writing) · 139 events · planner cost $1.94

### Stats (snapshot during run)
- 26 planner text turns · 40 planner-side tool calls (20 Bash + 9 Task + 7 Read + 4 TodoWrite)
- Planner tokens: 45 in / 26,170 out / 57K cache write / **1.87M cache read**
- **9 task dispatches** so far — multiple returning empty results, planner repeatedly working around it

### Planner narrative (struggle excerpts)
- "The coder returned an empty result. Let me check the workspace to see what was actually produced."
- "The coder created version files but didn't complete the Rails bootstrap. Let me resume the task with explicit instructions."
- "Coder still returning empty. Let me check what's on disk."
- "Rails app is now bootstrapped. The coder is succeeding silently — just returning empty text."
- *(several dispatches later)* **"Empty response again. The coder subagent in this harness seems to always return empty text but does perform actions."**
- *(then on inspection)* "Nothing. The coder subagent did nothing this time. Something is wrong with the coder subagent itself — it appears to be terminating without executing. **Let me try the `general` subagent instead** as the delegation tool the brief requires."
- "Only importmap + turbo installed. Stimulus did not run. Let me try again:"
- "Nothing written again. The coder is doing this intermittently — some prompts execute, others return empty without acting. Let me check if perhaps it's that the coder is limited in how many Write operations per session. Let me try splitting into two smaller tasks:"

### Where it struggled
**Same root cause as the Qwen 3.6 Plus run**: DeepSeek V4 Pro as opencode subagent emits the `<task_result>` envelope but with empty body content, intermittently. Sometimes it had actually performed shell actions silently; other times it had genuinely no-op'd. The planner had to manually inspect the filesystem after every dispatch to determine whether work happened, and route subsequent dispatches accordingly — eventually falling back to `general` for some subtasks the way the Qwen variant did.

That this happens on **two different OpenRouter-hosted "Tier B/C" cloud subagents** (Qwen 3.6 Plus and DeepSeek V4 Pro) suggests the pattern isn't model-specific — it's something about how those models respond to opencode's `task` tool envelope when the planner is a much stronger model. They appear to consume the prompt, partially execute, and return without populating the structured response. Worth filing upstream with opencode if you care about cheap-executor pairings.

---

## gpt_5_4_multi_balanced_forced — disciplined Codex spawn cycle with harness limits

**Source**: `results/gpt_5_4_multi_balanced_forced/opencode-output.ndjson` · 76 events · 0.96M input / 27K output tokens

### Stats
- **15 agent_message turns** from planner
- **23 collab_tool_call** entries — but split across 3 distinct primitive types:
  - `spawn_agent` (real dispatches): **9**
  - `wait` (planner waits for subagent): 8
  - `close_agent` (planner releases completed worker): 6
- 13-item todo list, all completed

### Planner narrative (key moments)
1. "Planning the full build first, then I'll dispatch the first coder task with the exact file and validation requirements so implementation can proceed without back-and-forth."
2. *(first spawn fails)* **"The harness rejected the first spawn because full-history fork can't be combined with an explicit agent type. I'm retrying with a fresh coder context and the full subtask embedded inline."**
3. "Reconnaissance is complete: the root is effectively empty, and the scaffold target is `Ruby 4.0.3` with `Rails 8.1.3`."
4. *(later)* "I caught a version drift from the generated scaffold: the app is currently on `ruby-4.0.2` even though reconnaissance found `4.0.3` available. I'm sending a fix-up now..."
5. *(during convergence)* **"The convergence audit spawn was blocked by the harness's open-agent limit. I'm closing the completed workers and then I'll re-run the audit task cleanly."**
6. "The convergence pass found two leftover generated assumptions and cleaned them. I'm re-running the full validation matrix now under `mise exec ruby@4.0.3`, including local boot and Docker Compose, so the final state is post-fix and not based on earlier results."

### Dispatches (real spawn_agents only)

| # | Subtask | Notes |
|---|---|---|
| 1 | Workspace reconnaissance and scaffold plan | Coder reports Ruby/Rails versions |
| 2 | Initial Rails app generation in workspace root | Scaffold landed cleanly |
| 3 | Dependency setup for LLM/quality tooling | Gemfile augmented |
| 4 | Fix-up: align Ruby baseline to newest mise version | 4.0.2 → 4.0.3 |
| 5 | Combined: chat architecture + UI + OpenRouter + Minitest | Big batch (5147-char prompt) |
| 6 | Combined: CI/security + container + docs | Delivery layer |
| 7 | Convergence audit + fix-ups | Hit open-agent limit, retried |
| 8 | (retry) Convergence audit | Cleaned 2 cross-file drifts |
| 9 | Final end-to-end validation matrix | Post-fix re-validation |

### Where it struggled
**Two distinct harness limits surfaced.** First, the initial spawn was rejected because Codex doesn't allow combining "full-history fork" with explicit agent type — planner adapted, retried with embedded context. Second, the convergence audit spawn hit the open-agent concurrency cap, so the planner had to issue 6 `close_agent` calls in sequence to free worker slots before re-spawning. Both adaptations show the planner fluently navigating Codex's harness primitives.

The real implementation work — once dispatched — landed cleanly. Coder model (GPT 5.4 medium) executed instructions literally without inventing structure; the convergence pass did real cross-file drift cleanup before the final validation. This is the most disciplined orchestration in the entire dataset.

---

## gpt_5_4_multi_faster_forced — same shape, more spawns, more cached input

**Source**: `results/gpt_5_4_multi_faster_forced/opencode-output.ndjson` · 175 events · 4.75M input / 35K output tokens

### Stats
- **31 agent_message turns**
- **53 collab_tool_call** entries (~21 real spawn_agent, rest are wait + close_agent)
- 12-item todo list

### Planner narrative (sample beats)
1. "I'm breaking the build into explicit subtasks first and tracking them as a visible plan, then I'll dispatch those subtasks to the `coder` with the full context needed for each one."
2. "The scaffold step is taking longer than a quick command, likely because Ruby/Rails installation is happening under mise. I'm holding the critical path here because the next tasks depend on the generated app layout and versions."
3. "I'm doing a read-only verification pass on the exact files it touched, then I'll hand off the SPA layer against that confirmed contract."
4. *(after service spawn)* "The service task completed with a live OpenRouter smoke check and the expected missing-key behavior."
5. *(after verification)* "Verification surfaced two concrete integration risks worth removing now: the model ID is duplicated, and one RubyLLM failure class can still escape the service wrapper. I'm sending a narrow fix-up before the UI task so the controller can depend on a cleaner error contract."
6. *(after SPA spawn)* "Verification found two concrete issues: a real Turbo regression in the flash target, and a documented keyboard shortcut that the Stimulus controller doesn't implement. I'm sending a narrow fix-up for both before we lock in the test suite."
7. *(after CI spawn)* "Verification found one concrete CI mismatch worth fixing before Docker validation: `bin/ci` is bypassing the checked-in `bundler-audit` wrapper, so the configured audit settings aren't actually what CI runs."

### Where it struggled
Not where you might expect — the planner *successfully caught and fixed multiple integration drifts* in the verification rounds (Turbo flash target, missing Stimulus shortcut, model-ID duplication, escaping RubyLLM error class, CI bypassing wrapper). This is the variant that, in Round 1 free-choice mode, was Tier 2; under forced delegation with the structured CONVERGE phase, it caught its own bugs and reached Tier A.

The cost was wall time (53m) and 4.75M cached input tokens — every spawn re-sends the full historical context to the executor. xHigh planner reasoning + low executor isn't a free pairing.

---

## claude_opus_sonnet_forced — clean 10-dispatch flow, planner read-verifies between

**Source**: `results-claude-code/claude_opus_sonnet_forced/stream.ndjson` · 800 events · $5.77, 43 turns

### Stats
- 11 planner text turns
- Planner-side tool calls: 1 ToolSearch + 148 Bash + 10 TodoWrite + 10 Agent + 33 Write + 49 Read + 1 Glob + 8 Edit (note: the **Write/Edit/Bash counts here include subagent-thread tool uses** — the planner-only direct file ops as captured in `success_report.multi_model.md` were 0 Write/Edit and 11 read-only Bash)
- **10 Agent dispatches** to `sonnet-coder`

### Planner narrative
1. "I'll plan the Rails chat app build, then delegate each subtask to the coder."
2. *(after dispatch 1)* "Skeleton looks clean. Now I'll update the todos and delegate subtask 2: the chat feature."
3. *(after dispatch 2 + verify)* "Importmap/turbo/stimulus were not installed (missing `app/javascript/` and `config/importmap.rb`). Dispatching a fix-up subtask."
4. "Dispatching subtask 3: Stimulus controllers."
5. "Dispatching subtask 4: tests."
6. *(after dispatch 5)* "All tests green. Let me verify the service test actually exercises the HTTP layer."
7. "Solid coverage. Moving to subtask 5: quality tooling."
8. "Local validation fully green. Moving to Docker validation."
9. "Build complete. End-to-end validation passed."

### Dispatches

| # | Subtask | Returned summary |
|---|---|---|
| 1 | Rails skeleton + ruby_llm wiring | "All gems are properly resolved" |
| 2 | Chat feature with Hotwire | (multi-line summary) |
| 3 | Wire importmap + hotwire (fix-up) | "All done" |
| 4 | Stimulus UX controllers | "Done" |
| 5 | Minitest suite with WebMock | "14 runs, 55 assertions, 0 failures, 100% line coverage" |
| 6 | RuboCop/Brakeman/SimpleCov/bundle-audit + CI | "All deliverables in place" |
| 7 | Docker + compose | (multi-line) |
| 8 | README.md | "Rails-default placeholder replaced with full specified content. No deviations." |
| 9 | Validate local boot + tests | "All steps green" |
| 10 | Validate Docker + compose | "All cleaned up" |

### Where it struggled
**Only one fix-up loop**: dispatch 2 didn't wire importmap/turbo/stimulus into `app/javascript/` despite the gems being in the Gemfile, so dispatch 3 was a tightly-scoped fix-up. Otherwise this is the cleanest forced run in the dataset — every dispatch has a clear scope, the verification reads between dispatches caught the one gap, and the validation phase ran end-to-end without timeouts.

---

## claude_opus_haiku_forced — 5 batched dispatches, fewer round-trips

**Source**: `results-claude-code/claude_opus_haiku_forced/stream.ndjson` · 623 events · $3.49, 34 turns

### Stats
- 8 planner text turns
- Planner-side tool calls: 1 ToolSearch + 102 Bash + 6 TodoWrite + **5 Agent** + 24 Write + 37 Read + 14 Edit
- **5 Agent dispatches** to `haiku-coder` (half as many as the sonnet variant)

### Planner narrative
1. *(after first plan)* "Let me create the todo list and start delegating to the coder."
2. *(after dispatch 1)* "Scaffold looks clean. Now the chat app code."
3. **"Let me verify the ruby_llm API claim — CLAUDE.md explicitly warns about hallucinated APIs."**
4. "API is real and the coder's usage works. Let me also sanity-check that the app boots."
5. *(after dispatch 3)* "All 20 tests pass. Now Docker + README."
6. **"Let me spot-check the ChatService since CLAUDE.md warned about hallucinated RubyLLM APIs."**
7. "Real ruby_llm API (I verified `RubyLLM.chat`, `add_message`, and `ask` all exist in 1.14.1). No hallucinated calls."
8. "## Done — validation PASS end-to-end"

### Dispatches

| # | Subtask | Returned summary |
|---|---|---|
| 1 | Scaffold Rails + Gemfile + bundle install | "Rails scaffolding complete" |
| 2 | Build chat app code | (multi-line) |
| 3 | Write tests + tooling | (multi-line) |
| 4 | Write Dockerfile + compose + README | (multi-line) |
| 5 | Run full end-to-end validation | "Step 6: ✓ PASS" |

### Where it struggled
**It didn't.** The planner deliberately batched into 5 larger dispatches (vs Sonnet's 10), accepting bigger per-dispatch prompts (13K and 14K chars) to reduce round-trips. The CLAUDE.md "hallucinated APIs" warning is visible in the planner narrative: it twice paused to manually verify the ruby_llm API after the executor wrote code. That extra discipline is part of why this variant scored 90/100 with the cheapest executor model in the matrix.

---

## Cross-variant pattern: where the orchestrator pattern broke

Three distinct failure modes emerged across the dataset:

### Failure mode 1 — Cross-provider task dispatcher stall (opencode `glm`, `qwen`)
Planner reaches the dispatch announcement, then the `task` tool call simply never makes it to the wire. 6-minute stall, SIGTERM, 0 files. Reproduced on two unrelated retries with subagents on different provider lanes (Z.ai for glm, llama-swap for qwen) than the OpenRouter Opus planner. **Hypothesis**: opencode's task dispatcher serializes the cross-provider auth/routing step in a way that blocks the planner thread. **Did not occur** when both lanes were OpenRouter (kimi).

### Failure mode 2 — Subagent silent no-op (opencode `qwen3.6plus`, `deepseek`)
Planner dispatches successfully. Subagent receives the prompt, returns the `<task_result>` envelope — but the body is empty, sometimes after the model has actually performed shell actions, sometimes without performing anything. Planner detects the mismatch via filesystem inspection, eventually switches to opencode's built-in `general` subagent (which is just Opus again), at which point the run becomes "solo Opus with extra coordination overhead." Affected both Qwen 3.6 Plus and DeepSeek V4 Pro on OpenRouter, suggesting a model-class issue (smaller models echo-pass the tool envelope without populating the response field) rather than a single bad gateway.

### Failure mode 3 — Validation timeout despite shippable artifact (opencode `kimi`)
Planner completes implementation cleanly, all tests pass, dispatches the validation step — and the dispatched docker build / docker compose up runs longer than the 6-minute no-progress watchdog allows. SIGTERM with a complete artifact on disk. Static review of the artifact predicts validation would have passed; we just don't have empirical proof. The watchdog needs a longer grace window for VALIDATE-phase dispatches that wrap container builds.

### What worked cleanly
- **Codex `spawn_agent`** with same-tier executor (GPT 5.4 medium/low): worked through harness primitives (`wait`, `close_agent`) and recovered from concurrency-cap rejections on its own.
- **Claude Code `Agent`** with Sonnet/Haiku coders: 5-10 dispatch round-trips, one fix-up at most, clean end-to-end validation.
- **opencode `task`** with same-lane strong executor (Kimi K2.6 on OpenRouter): 3 batched dispatches, no fix-ups, but VALIDATE timeout.

The three success patterns differ in granularity (Codex 9-21 spawns, Claude Code 5-10 dispatches, opencode 3 dispatches) but share two traits: (a) executor was capable enough to populate substantive `<task_result>` content, and (b) provider routing was stable.

---

## Source files (raw event streams)

If you want to dig deeper, the per-variant traces are in `/tmp/orch_traces/<slug>.md` (regenerable from the ndjson files via the extraction script). Each contains every planner text turn and every dispatch with full prompt/result snippets up to ~400 chars.

The raw event streams themselves live alongside each variant's `result.json`:

- opencode runs: `results/<slug>/opencode-output.ndjson`
- Codex runs: `results/<slug>/opencode-output.ndjson` (same filename, different event format)
- Claude Code runs: `results-claude-code/<slug>/stream.ndjson`

---

## Harness fix attempts (Round 2.5)

After documenting the three failure modes above, two harness changes were applied to test which were truly model issues vs harness misconfiguration:

1. **15-min no-progress watchdog** (CLI flag `--no-progress-minutes 15`, vs the 6-min default) — to test whether cross-provider stalls were slow init or hard hangs
2. **Reasoning passthrough on subagent provider entries** (`scripts/benchmark/config.py` patch — auto-emit `"reasoning": true` on the provider model entry for known reasoning-class subagents: DeepSeek V4 Pro, DeepSeek V4 Flash, Qwen 3.6 family, Qwen 3.5 family, Kimi K2.6) — to test whether the empty-`<task_result>` mode was opencode dropping reasoning_content

Six variants were re-run with both fixes simultaneously: 4 with Opus 4.7 as planner, 2 with GPT 5.5.

### Fix 1 (15-min watchdog) — works

| Variant | Old config (6-min watchdog) | New config (15-min watchdog) |
|---|---|---|
| `opus + glm` | failed at 6m, 0 dispatches, 0 files (cross-provider stall) | **completed at 12.75m, 4 dispatches, 1703 files** |
| `opus + qwen-local` | failed at 6m, 0 dispatches, 0 files (cross-provider stall) | **completed at 13m, 8 dispatches, 1537 files** |

The cross-provider task-dispatcher "stall" was actually slow first-call init on Z.ai (GLM) and llama-swap (Qwen-local). 6 min wasn't enough for the first cross-provider auth + spawn round-trip; 15 min is. **Failure mode 1 was harness config, fully resolved by the watchdog change.**

### Fix 2 (reasoning passthrough) — no measurable effect

The reasoning passthrough setting was correctly emitted on every targeted subagent provider entry (verified in the generated `config/opencode.benchmark.json`). All six reruns nonetheless exhibited the **same empty-`<task_result>` pattern** as the original runs. Concrete dispatch tally per variant after the fix was active:

| Variant | Dispatches | Empty `<task_result>` | Substantive | Subagent split | Files |
|---|---:|---:|---:|---|---:|
| opus + glm | 4 | **4 (100%)** | 0 | coder (GLM)×4 | 1703 |
| opus + qwen-local | 8 | 2 | 6 | coder×2, **general×6** | 1537 |
| opus + qwen3.6plus | 4 | **4 (100%)** | 0 | coder (Qwen)×4 | 138 |
| opus + deepseek | 14 | 3 | 11 | coder×2, **general×12** | 1902 |
| gpt55 + qwen3.6plus | 3 | 2 | 1 | coder×3 | 0 |
| gpt55 + deepseek | 4 | **4 (100%)** | 0 | coder×4 | 0 |

Even with `reasoning: true` on the provider entry, **the cheap-cloud subagents continued to return empty `<task_result>` envelopes** while sometimes silently performing substantial shell work (1700+ files for GLM, 138 for Qwen 3.6 Plus). The setting was a no-op for this failure mode. **The actual empty-result mechanism is something other than reasoning_content stripping** — possibly opencode parsing only the model's last assistant message and these models emitting a final tool-call instead of a closing text turn, or possibly a tool-call envelope versioning mismatch.

### What actually saved the Opus reruns: planner-side filesystem inspection

Looking at how the four "completed" Opus reruns survived the empty-result mode:

- **GLM and Qwen 3.6 Plus**: Opus saw empty `<task_result>` outputs but verified via `Read` that files were appearing on disk (the subagent was silently doing the work). It kept dispatching to `coder` and trusted the on-disk evidence over the empty envelope. 4/4 dispatches "succeeded" by this criterion.
- **Qwen-local and DeepSeek V4 Pro**: Opus tried `coder` for the first 1-2 dispatches, saw empty results AND nothing on disk, then **switched to opencode's built-in `general` subagent** (which is just Opus again) for the remaining 6-12 dispatches. The `general` agent returned substantive results because it's not subject to whatever envelope mismatch breaks the cheap-cloud subagents.

In every "completed" case, **opencode's `task` envelope was broken** for the cheap-cloud subagent. Opus's recovery discipline — read the filesystem, decide whether the empty envelope hides real work, fall back to a different subagent type if not — is what salvaged the runs.

### GPT 5.5 doesn't have the same recovery discipline

The two GPT 5.5 reruns demonstrate that planner capability matters here:

| Variant | Dispatches | Empty | Substantive | Files | Outcome |
|---|---:|---:|---:|---:|---|
| `gpt55 + qwen3.6plus` | 3 | 2 | 1 | **0** | failed (15-min watchdog timeout, planner stuck in redispatch loop) |
| `gpt55 + deepseek` | 4 | **4 (100%)** | 0 | **0** | completed_with_errors (gave up at "hard blocker: empty workspace") |

GPT 5.5's response to empty `<task_result>` results was either:
- **Loop and redispatch the same subtask** (qwen3.6plus case) — every redispatch returned empty, GPT 5.5 never inspected the filesystem to discover that nothing had actually happened, and the watchdog killed it
- **Give up immediately** with a "hard blocker" message (deepseek case) — accepting the empty result as authoritative and concluding the workspace was unrecoverable

Neither GPT 5.5 run produced any files. Compare to Opus, which under the *same* harness conditions with the *same* subagents either completed (1703 files for GLM, 138 for Qwen3.6Plus) or fell back to `general` (1537 files for Qwen-local, 1902 for DeepSeek). **The "rescue" wasn't the harness fix — it was Opus's iteration discipline.**

### Updated verdict on each failure mode

| Mode | Original verdict | Verdict after fix attempt |
|---|---|---|
| 1. Cross-provider stall (glm, qwen-local) | "harness — likely opencode internal" | **harness, fully fixed by 15-min watchdog (slow init, not hang)** |
| 2. Empty `<task_result>` (qwen3.6plus, deepseek) | "harness — opencode strips reasoning_content" | **harness, but reasoning passthrough is NOT the fix.** Real cause is downstream of provider model options — likely opencode's task-result parsing of the subagent's final message. Opus salvages it via filesystem inspection + `general` fallback; GPT 5.5 doesn't. |
| 3. Validation-phase timeout (kimi) | "harness, trivial fix" | **confirmed harness — DeepSeek rerun completed phase 2 cleanly under the 15-min watchdog** |

### What we did NOT measure

These reruns intentionally did not change the planner-prompt or the subagent-prompt, so we still don't know:
- Whether a stricter subagent prompt ("you MUST emit a final plain-text summary after every dispatch") would force these models to populate the `<task_result>` body
- Whether opencode's `task` tool has a config flag to capture intermediate assistant messages or tool-call results into the task result
- Whether Codex's `spawn_agent` would exhibit the same empty-result issue with these models (we'd need to add Codex pairings with cross-provider OpenRouter subagents, which Codex doesn't currently support)

### Bottom-line update

Of the three failure modes documented in the original `orchestration_traces.md`:
- **One was a clean harness misconfiguration** (no-progress watchdog), now fixed in the codebase
- **One was a deeper protocol mismatch** that the obvious config knob doesn't address; the cheap-cloud subagents we paired with opencode all silently execute but return empty result envelopes, and only a **planner with iteration discipline (Opus)** can route around it
- **One was a timeout calibration issue** for long docker builds, now resolved by the same watchdog change

The model-vs-harness question therefore has a more nuanced answer: opencode's subagent protocol does not robustly accommodate the way these specific cloud models terminate their dispatched work, but the gap is not in the dimension we patched (reasoning passthrough) — it's in result-envelope parsing. Until that's investigated upstream, the practical guidance for cheap-cloud-executor pairings is: pair them with a planner that knows to verify filesystem state, not just trust the `<task_result>` envelope.

> **Update from Round 4**: For DeepSeek V4 Pro specifically, the unmeasurable-through-opencode finding was resolved by switching to a different harness entirely. Routing Claude Code through OpenRouter's Anthropic-compatible endpoint (the deepclaude env-swap shim) bypasses opencode's request-payload construction altogether. Both `claude_code_deepseek_v4_pro_or` and `claude_code_deepseek_v4_pro_or_sonnet` ran to completion at 84/100 and 89/100 (Tier A) with full multi-turn, no reasoning_content errors. See [`success_report.deepclaude.md`](success_report.deepclaude.md). The bug was opencode-specific, not a general DeepSeek-on-OpenRouter constraint.
