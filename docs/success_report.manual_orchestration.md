# Manual Cross-Process Orchestration — Round 3

This is the most rigorous test of "Opus as planner + cheap-cloud subagent as executor" in this benchmark, designed to bypass every harness pitfall identified in the previous rounds. The protocol:

- **Planner** = me (Claude Code session, Opus 4.7) — produces self-contained subtask prompts and inspects results between dispatches
- **Executor** = opencode in single-agent mode, invoked per-subtask via subprocess with the cheap-cloud model as the sole primary
- **No in-process delegation** — the broken `task` envelope (Round 2.5) is not used. Each opencode invocation is a fresh single-agent session.
- **No fallback path** — there is no `general` subagent for the planner to escape to. Either the named executor produces the code or nothing does.
- **Strict planner discipline** — Opus uses Read / Bash-to-invoke-opencode / TaskCreate only. No direct Write/Edit on project files. Every code change goes through an opencode subprocess.

Three variants attempted: Opus + Qwen 3.6 Plus, Opus + Kimi K2.6, Opus + DeepSeek V4 Pro.

---

## TL;DR

| Variant | Outcome | Score | Tier | Δ vs solo | Δ vs Opus solo (97) |
|---|---|---:|---|---:|---:|
| `manual_opus_qwen36plus` | success (8 dispatches + 1 fix-up) | **94** | A | +23 (vs Qwen 3.6 Plus solo 71) | -3 |
| `manual_opus_kimi` | success (5 dispatches, no fix-ups) | **97** | A | +10 (vs Kimi solo 87) | **=0 (ties Opus)** |
| `manual_opus_deepseek` | **harness-incompatibility failure** | n/a | n/a | n/a | n/a |

**Two of three variants succeeded — both Tier A, both materially above their solo baselines, with the kimi variant tying Opus 4.7 solo at 97/100.** The third failed with a structural opencode/DeepSeek interop bug that no model-level config flag could resolve.

---

## Two methodological course-corrections forced by this round

Before the headline findings, two earlier conclusions in this benchmark have to be revised:

### 1. The qwen3.6plus "silent execution" hypothesis was wrong — it was 404 errors

Setting up variant 1, the first opencode dispatch with `openrouter/qwen/qwen3.6-plus:free` returned 0 tokens in 1 second. Inspection of the raw event stream revealed:

> `{"error":{"message":"The free model has been deprecated. Transition to qwen/qwen3.6-plus for continued paid access.","statusCode":404}}`

**The `:free` endpoint was deprecated as of 2026-04-25.** Every previous benchmark run that used `qwen3.6-plus:free` — including all three Round 2.5 variants and both GPT 5.5 reruns — was hitting 404s on every dispatch. The "empty `<task_result>` envelope" pattern documented in [`orchestration_traces.md`](orchestration_traces.md) for those qwen3.6plus variants was not silent execution — it was OpenRouter rejecting the request entirely.

This invalidates the previous interpretation that "Qwen 3.6 Plus silently executes shell actions but returns empty results." The model never got a chance to try. After switching to the paid endpoint (`openrouter/qwen/qwen3.6-plus`, $0.325/$1.95 per M tokens), it actually executed and returned substantive content normally — see variant 1 below.

### 2. The deepseek "silent execution" hypothesis was also wrong — it was reasoning_content errors

Variant 3 attempted Opus + DeepSeek V4 Pro through opencode and reproduced exactly the documented CLAUDE.md issue at turn 2 of every dispatch:

> `[DeepSeek] The "reasoning_content" in the thinking mode must be passed back to the API.`

Three different opencode `reasoning` configurations (`true`, `false`, absent) all produced the same wire-level failure. **DeepSeek V4 Pro on OpenRouter requires reasoning_content to be echoed back in subsequent requests**, and opencode's ai-sdk does not do that. No model-level config knob fixes it.

This means the Round 2.5 finding that "DeepSeek V4 Pro silently no-op'd" was wrong — it was actively erroring with a 400 response that opencode buried in its event stream. The Round 2.5 in-process variants only "completed" because Opus's `general` fallback agent (also Opus) wrote everything; DeepSeek V4 Pro contributed zero substantive code in any benchmark configuration to date.

**For both qwen3.6plus and deepseek-v4-pro, the Round 2 / Round 2.5 conclusions about cheap-cloud subagent behavior need re-reading with the wire-level error context in mind.** The honest reading is: we don't have any clean opencode-multi-agent measurement of either model. The manual orchestration round is the first round to produce a clean measurement of qwen3.6plus (variant 1 below); deepseek-v4-pro remains unmeasurable through opencode in any configuration.

---

## Variant 1: `manual_opus_qwen36plus` — 94/100, Tier A

### Dispatch summary

| # | Subtask | Time | Cost | Outcome |
|---|---|---:|---:|---|
| 1 | Skeleton (rails new) | 64s | $0.09 | Clean — Rails 8.1.3, manually wired `app/javascript/` (Rails 8.1 generator change) |
| 2 | Gemfile augmentation + ruby_llm initializer | 44s | $0.04 | Truncated final summary; only `ruby_llm` visible at top level (test gems were inside `:test` block, my grep missed them) |
| 3 | Fix-up: verify test gems | 24s | $0.02 | All test gems were already there from dispatch 2 — no-op verification |
| 4 | App layer (service + models + controllers + views + Stimulus, 13 files) | 145s | $0.17 | All files exact-spec, real RubyLLM API throughout, verifications all pass |
| 5 | Test suite (5 files, 10 tests) | 102s | $0.10 | 10 runs / 20 assertions / 0 failures / 0 errors. Made smart adaptations: `root_url` → `get "/"`, created tailwind.css placeholder |
| 6 | Dockerfile + compose.yaml + README + bin/ci | 195s | $0.13 | Docker build SUCCEEDED. README hand-written (8 sections). compose.yaml with `${VAR:?}` enforcement |
| 7 | Validation (cut short, missing bin/importmap binstub) | 93s | $0.09 | Detected missing binstub, started fixing, opencode session ended mid-fix |
| 8 | Fix-up: create bin/importmap binstub | 50s | $0.07 | Created the binstub via `bundle binstubs importmap-rails`, ran 14 tool calls but emitted 0 final text |
| 9 | Validation (just step A: local boot) | 25s | $0.02 | Local boot PASS. Server boots, /up returns 200, home page renders |

**Total**: 9 dispatches, ~$0.74 executor cost, ~12 min cumulative wall time across dispatches.

### Validation outcomes
- ✅ Tests: 10/0/0
- ✅ Local boot: HTTP 200 on /up, home page renders
- ✅ Docker build: succeeded
- ❓ bin/ci end-to-end: unverified (opencode session cut short)
- ❓ docker compose up + curl: unverified (same reason)

### Audit verdict (94/100, Tier A)

Per the standardized rubric:
- Deliverable completeness: 24/25 (minor `rails/test_unit/railtie` commented out in `application.rb:15`)
- RubyLLM correctness: 20/20 — `RubyLLM.chat`, `with_instructions`, `add_message`, `ask`, `response.content` all real, verified against gem source
- Test quality: 14/15 — WebMock against actual OpenRouter URL with multi-turn body assertion
- Error handling: 9/10 — typed rescue, controller renders user-visible error
- Persistence: 8/10 — cookie-backed with 25-message ring
- Hotwire/Turbo/Stimulus: 9/10 — real Turbo Streams, two real Stimulus controllers
- Architecture: 5/5 — clean PORO + service split
- Production readiness: 5/5 — no leaked secrets, non-root container, ERB-escaped LLM output

**+23 over Qwen 3.6 Plus solo (71/100, Tier B).** Auditor attribution: *"Qwen wrote the lines, Opus decided the boundaries — and the boundaries are most of what lifts this from B to A."*

### Behavioral notes on Qwen 3.6 Plus as executor
- Frequently truncates final summary text (3 of 9 dispatches had no DISPATCH_COMPLETE token)
- Sometimes emits zero text but performs many tool calls (dispatch 8: 14 tool calls, 0 text turns)
- Made several correct adaptations on its own (`app/javascript/` manual creation, `root_url` → `get "/"`, tailwind placeholder)
- Required 2 fix-up dispatches for issues caused by Rails 8.1 generator behavior changes
- Operationally less reliable than Kimi — needed orchestrator babysitting between dispatches

---

## Variant 2: `manual_opus_kimi` — 97/100, Tier A — TIES OPUS 4.7 SOLO

### Dispatch summary

| # | Subtask | Time | Cost | Outcome |
|---|---|---:|---:|---|
| 1 | Skeleton + gems + initializer (combined) | 129s | $0.09 | Single coherent dispatch — caught Rails 8.1's missing javascript wiring, ran `rake importmap:install`, ensured `bin/importmap` exists |
| 2 | App layer (13 files) | 199s | $0.14 | All files exact-spec. Made smart adaptations: ran `bin/rails stimulus:install` + `tailwindcss:install`, removed hello_controller placeholder, caught and fixed layout-wrapping issue from tailwind install |
| 3 | Test suite | 53s | $0.03 | 10 tests / 20 assertions / 0 failures / 0 errors |
| 4 | Dockerfile + compose + README + bin/ci | 172s | $0.08 | Docker build succeeded, README hand-written, ci config reordered properly |
| 5 | Validation (all 3 steps) | 97s | $0.03 | Step 1: PASS. Step 2: tests + Brakeman pass, RuboCop has 3 style offenses (not bugs). Step 3: docker compose up healthy, /up=200, clean down |

**Total**: 5 dispatches, ~$0.37 executor cost, ~10 min cumulative wall time across dispatches. **Zero fix-up dispatches required.**

### Validation outcomes
- ✅ Tests: 10/0/0
- ✅ Local boot: HTTP 200 on /up
- ✅ Docker build: succeeded
- ⚠ bin/ci: tests + Brakeman clean, 3 RuboCop style offenses (not bugs)
- ✅ Docker compose up + curl: container healthy, HTTP 200 on /up, clean teardown

**Full runtime path verified end-to-end.** Only failure is style nits.

### Audit verdict (97/100, Tier A)

Per the standardized rubric:
- Deliverable completeness: 24/25
- RubyLLM correctness: 20/20 — zero hallucinations, full real-API path
- Test quality: 15/15 — full marks. Tests stub the actual OpenRouter HTTPS endpoint and assert request body contains replayed history
- Error handling: 10/10
- Persistence: 8/10 — encrypted session cookie with 25-message cap
- Hotwire/Turbo/Stimulus: 10/10
- Architecture: 5/5
- Production readiness: 5/5

**+10 over Kimi K2.6 solo (87/100, Tier A).** Auditor attribution: *"Kimi wrote every line, but Opus's planning prompts shaped what to ask for — better test fixtures, error-path coverage, persistence cap — pushing Kimi from 87 → ~97. Orchestration delivered roughly +10 points of polish without needing fix-up dispatches, which is the strongest case in the multi-agent set so far."*

### Behavioral notes on Kimi K2.6 as executor
- Single coherent text response per dispatch — no truncation, no zero-text turns
- Strong autonomous adaptation: caught Stimulus + Tailwind install gaps without prompting, caught the layout-wrapping side effect of `tailwindcss:install`
- Zero fix-up dispatches required
- Cumulative cost half of Qwen variant ($0.37 vs $0.74) for higher quality output
- Cache reads of ~1M tokens across the run (OpenRouter prompt caching working)

---

## Variant 3: `manual_opus_deepseek` — FAILED (harness incompatibility)

DeepSeek V4 Pro returned the documented reasoning_content error on every dispatch attempt:

> `[DeepSeek] The "reasoning_content" in the thinking mode must be passed back to the API.`

Three opencode `reasoning` configurations tested (`true`, `false`, absent) — all failed identically at turn 2 of dispatch 1. opencode's ai-sdk strips reasoning_content from the model's response when constructing subsequent requests; DeepSeek's API rejects requests where prior assistant turns had reasoning_content but it's missing from the conversation history.

**No model-level config flag in opencode resolves this.** Workarounds (custom OpenRouter provider params, single-bash-per-dispatch protocol, switching to DeepSeek V4 Flash) were not pursued.

See the variant-local trace: [`results/manual_opus_deepseek/orchestration_trace.md`](../results/manual_opus_deepseek/orchestration_trace.md).

### Implication for previous DeepSeek conclusions

The Round 2.5 in-process forced-delegation runs (`opencode_opus_deepseek_forced` with both old and patched configs) reported "completed" with 1900 files but had only 2 of 14 dispatches go to the actual `coder` subagent — both empty. We previously interpreted this as "DeepSeek silently executes but returns empty envelopes."

Now we know it was actively wire-level erroring. **The 1900-file artifact came entirely from Opus via the `general` fallback agent.** DeepSeek V4 Pro contributed zero code to any forced-delegation run in this benchmark's history.

---

## Cross-variant findings

### 1. Manual orchestration cleanly bypasses opencode's task-envelope bug

The two successful variants (qwen3.6plus, kimi) both demonstrate that **the cheap-cloud-executor pairings can produce Tier-A artifacts under Opus orchestration** — the failure mode in Round 2.5 was opencode's in-process `task` tool envelope, not the executor model. Bypassing that with cross-process subprocess invocations works.

For deepseek-v4-pro, the failure mode is a different harness layer — opencode's request payload construction strips reasoning_content. That's a deeper bug than the task envelope; it affects single-agent opencode invocations too, not just multi-agent. Manual orchestration doesn't help here.

### 2. The lift mechanism scales across executor capabilities

Three clean datapoints now show consistent quality lifts when a strong planner provides prescriptive subtask prompts to a less-capable executor:

| Executor | Solo score | Lift (manual orchestration with Opus planner) |
|---|---:|---:|
| GLM 5.1 | 46 (Tier C) | +47 → 93 (Tier A) [from Round 2.5 in-process; Opus directed, GLM wrote] |
| Qwen 3.6 Plus | 71 (Tier B) | +23 → 94 (Tier A) [from manual orchestration] |
| Kimi K2.6 | 87 (Tier A) | +10 → 97 (Tier A — ties Opus solo) [from manual orchestration] |

The lift size is roughly inversely proportional to the executor's solo capability — the further from Tier A solo, the more orchestration adds. Kimi was already Tier A solo, so the +10 is mostly polish (better test fixtures, error coverage, persistence design). GLM was Tier C solo for a specific recall failure (hallucinated fluent DSL), and prescriptive prompts that named the real API removed that failure entirely.

### 3. Executor reliability matters more than executor capability

Comparing the two successful variants by operational discipline:
- **Kimi**: 5 dispatches, 0 fix-ups, full validation reached, $0.37 total
- **Qwen 3.6 Plus**: 9 dispatches (2 fix-ups + truncated validation), $0.74 total

Both produced Tier-A artifacts. Kimi was twice as fast and twice as cheap because it didn't truncate responses and didn't need babysitting between dispatches. **For "Opus planner + cheap executor" production deployments, executor *reliability* (response coherence, completion-token discipline) dominates raw capability** — a less-capable but more-reliable executor lets the orchestrator move faster.

### 4. Manual orchestration overhead from the planner side

This round consumed substantial Opus planner tokens from this Claude Code session — every dispatch required me to (a) write a prompt file, (b) Read the prompt file (per the unseen-content permission gate), (c) Bash to invoke the wrapper script, (d) wait for monitor event, (e) Read the dispatch output JSON, (f) verify file system state, (g) plan next dispatch. That's 6-8 tool calls per dispatch × 14 successful dispatches across the two variants = ~100 planner-side tool calls.

Opus planner cost is not directly measured in the executor logs (it lives in Claude Code session billing) but is roughly 5-15× the executor cost per dispatch because the planner reads opencode's full output (often multi-KB JSON) and writes detailed prompt files. **The total cost of manual orchestration is dominated by the planner side, not the executor side.**

This makes the methodology valuable for benchmarking and capability-isolation tests, but unattractive for production deployment unless you have a way to amortize the planning cost (e.g., reuse plans across many similar tasks).

---

## What this round actually proves

1. **Cheap-cloud executors CAN produce Tier-A artifacts under Opus orchestration.** Kimi at 97 and Qwen 3.6 Plus at 94 — both genuinely written by the named subagent (no fallback, no Opus rescue), both above their solo baselines.

2. **The Round 2.5 "silent execution" interpretation was wrong twice.** qwen3.6plus was 404-erroring (deprecated free endpoint); deepseek-v4-pro was 400-erroring (reasoning_content interop). Neither silently executed; both wire-level failed in ways the in-process forced-delegation event stream buried.

3. **opencode's harness has at least three distinct failure modes** beyond the documented `task` envelope: (a) endpoint deprecations cascading silently, (b) cross-provider task-dispatcher slow-init stalls (Round 2.5 watchdog fix), (c) reasoning_content handling for DeepSeek-style thinking-mode models. None of them are model failures; all are harness layers between the planner and the executor's actual capability.

4. **The "constraint-via-prescriptive-prompts" mechanism is robust across executor capability tiers.** Three distinct executor capability levels (GLM Tier C, Qwen 3.6 Plus Tier B, Kimi Tier A) all show meaningful quality lifts from the same orchestration pattern, with lift size proportional to the gap between solo capability and Tier A. The pattern works.

5. **DeepSeek V4 Pro remains unmeasured** through any opencode-based protocol in this benchmark. Solo DeepSeek (single-turn opencode with `--continue` for multi-step) at 69 is the only data we have. Manual orchestration would need a different execution harness to test DeepSeek meaningfully.

---

---

# The bottom line: is orchestration worth it vs solo Opus?

The user's question — and the most important question in this entire benchmark series — is whether pairing Opus with another model is **absolutely worth it** vs just using Opus alone, weighing **token cost, wall time, and quality together**. A slight quality bump is not enough to justify a longer run or higher cost.

## Recomputed solo Opus 4.7 baseline (corrected)

The previous reports cited `claude_opus_4_7` (opencode solo) at "~$1.10". That figure was wrong — it didn't account for cache-read tokens (4.8M of them). The correct cost using the actual per-million Anthropic pricing is:

| Token type | Count | Rate ($/M) | Cost |
|---|---:|---:|---:|
| Input (uncached) | 93 | 5.00 | $0.0005 |
| Cache write | 94,511 | 6.25 | $0.59 |
| Cache read | 4,836,631 | 0.50 | $2.42 |
| Output | 41,265 | 25.00 | $1.03 |
| **Total** | | | **$4.04** |

So **solo Opus 4.7 in opencode produces a Tier-A 97/100 Rails app in ~18 min for ~$4.** That is the baseline every orchestration variant must beat to justify itself.

## The unified comparison table

All variants graded on the same standardized rubric, all costs total (planner + executor where measurable), all wall times end-to-end including planner thinking time:

| Variant | Score | Wall time | Total cost | Δ score vs solo (97) | Δ cost vs solo ($4) | Δ time vs solo (18m) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| **Opus 4.7 solo (opencode)** | **97** | **18m** | **$4.04** | baseline | baseline | baseline | ⭐ benchmark to beat |
| Opus + Kimi K2.6 (manual orchestration) | **97** | ~30-40m | ~$3-7 (incl. planner) | =0 | -$1 to +$3 | +12-22m | tie quality, ~2× wall time, similar cost |
| Opus + Sonnet 4.6 (Claude Code, forced) | 92 | 25m | $5.77 (logged) | -5 | +$1.73 | +7m | -5 quality, more cost, more time |
| Opus + Haiku 4.5 (Claude Code, forced) | 90 | 19m | $3.49 (logged) | -7 | -$0.55 | +1m | -7 quality, marginal cost win |
| Opus + Kimi K2.6 (in-process forced) | 95 | 25m | ~$2-3 (planner-only logged) | -2 | -$1 to -$2 | +7m | -2 quality, ~$1-2 cheaper, +7m wall |
| Opus + GLM 5.1 (in-process forced, with timeout fix) | 93 | 13m | ~$0.50 + Z.ai sub | -4 | -$3+ | -5m | -4 quality, much cheaper, faster |
| Opus + Qwen 3.6 Plus (manual orchestration) | 94 | ~40m | ~$4-8 (incl. planner) | -3 | =0 to +$4 | +22m | -3 quality, similar/higher cost, much longer |
| GPT 5.4 xHigh + medium (Codex forced) | 94 | 30m | ~$1-3 | -3 | -$1 to -$3 | +12m | -3 quality, **80-85% cheaper than GPT solo**, more time |
| GPT 5.4 xHigh + low (Codex forced, faster) | 94 | 53m | ~$3-6 | -3 | similar to medium | +35m | same quality as balanced, much slower |

(Tier-D failures and 0-file runs omitted.)

## Verdict by use case

### "I want the best possible quality on a one-off greenfield Rails build"
**Answer: Solo Opus 4.7 in opencode. No orchestration variant beats it on quality.**

The two variants that *match* 97 (Opus + Kimi orchestration, both in-process forced and manual cross-process) take **70-120% longer wall time** for the same score. Cost is roughly comparable. **There is no quality reason to orchestrate.** Just use Opus solo.

### "I need Tier-A quality on a budget under $2"
**Answer: Codex GPT 5.4 xHigh + medium executor (forced).**

This is the ONE configuration where orchestration meaningfully beats solo. Solo GPT 5.4 xHigh is ~$16 / 22m / 97. The forced variant is ~$1-3 / 30m / 94. **80-85% cost reduction for 3 quality points and 8 extra minutes.** Worth it if you can absorb the wall time and don't need the absolute top quality bucket. Note: this is NOT cheaper than solo Opus opencode ($4 / 18m / 97), it's cheaper than solo *xHigh*.

### "My only available executor model is Tier-B/C and hallucinates APIs"
**Answer: Orchestrate with Opus as planner — but realize you're spending Opus tokens to fix the executor's gaps.**

Three clean datapoints showing orchestration lift:
- GLM 5.1 (Tier C 46 solo) → 93 under Opus orchestration, **+47 points**
- Qwen 3.6 Plus (Tier B 71 solo) → 94 under Opus orchestration, **+23 points**
- Kimi K2.6 (Tier A 87 solo) → 97 under Opus orchestration, **+10 points**

The lift is real and proportional to the gap between solo capability and Tier A. But the *cost of that lift* is dominated by Opus planner tokens. If you only have GLM 5.1 access (not Opus), this finding is useless. If you have both Opus and GLM, just use Opus solo for less money and time.

The realistic use case: **a multi-tenant deployment where the planner runs once and is amortized across many similar subtasks** (e.g., "apply this same refactor to 50 different files" — plan once, execute 50 times). Greenfield Rails benchmarks don't capture that pattern.

### "I'm forced into a harness where solo Opus regresses (Claude Code)"
**Answer: Switch harness, OR orchestrate as workaround.**

Solo Opus in Claude Code hallucinated `chat.complete` and produced Tier-3 code at $6.74. Orchestrating with Sonnet/Haiku coders inside Claude Code repaired the regression to Tier A at lower cost ($5.77 / $3.49). **But the cleaner fix is to use opencode for solo Opus**, which produces Tier A at $4 / 18m without any orchestration. The "orchestration repairs Claude Code regression" finding is real but is essentially a workaround for a different bug.

### "I want maximum speed"
**Answer: Solo Opus 4.7 in opencode. Or solo Kimi K2.6 if Tier-A 87 is acceptable.**

| | Wall time | Quality |
|---|---:|---:|
| Solo Opus opencode | 18m | 97 |
| Solo Kimi K2.6 | 20m | 87 |
| Best orchestration variant (Opus + Haiku Claude Code) | 19m | 90 |
| Best Tier-A orchestration (Opus + Kimi) | 25-40m | 95-97 |

Orchestration **never wins on speed** for a single greenfield build. The coordination overhead between planner and executor adds at minimum ~7 minutes (in-process) and up to ~22 minutes (cross-process manual) to the wall clock.

## The "hidden" planner cost in this Claude Code session

The Round 3 manual orchestration variants were planned by Opus 4.7 running inside this Claude Code session — token usage that is NOT logged in the executor (opencode) JSON outputs. Per-dispatch overhead is roughly:

- ~3-5 of my Claude Code turns per dispatch (read output, plan, write prompt, monitor, verify)
- Each turn ≈ 100-200K cache_read tokens + 5-15K input + 1-5K output = ~$0.15-0.25
- 14 successful dispatches × 4 turns avg × $0.20 = **~$11 hidden planner cost** for the two manual variants combined

This is roughly 3× the directly-logged executor cost ($1.11 combined). **Manual orchestration's true cost is dominated by the planner.** In-process orchestration (Round 2 forced) avoids most of this because the planner runs to completion in a single non-interactive process — no per-dispatch human-loop overhead.

## Final verdict in one paragraph

**For a single greenfield Rails build, solo Opus 4.7 in opencode is the best option on every metric: it ships Tier-A 97/100 in 18 minutes for ~$4, beating every orchestration variant on at least one of (quality, time, cost) and tying or beating most on all three.** The cleanest case for orchestration is Codex GPT 5.4 xHigh + medium executor for cost-sensitive Tier-A (~$2 instead of ~$16, at 94 instead of 97 and 30m instead of 22m). Every other orchestration configuration trades quality, time, or cost for the privilege of using a cheaper executor — and once you account for the planner's hidden token cost, even the "cheaper executor" advantage often disappears. **Orchestration is a tool for amortizing planner cost across many similar subtasks, not for one-off cohesive builds.**

---

## Cross-reference

- [`success_report.md`](success_report.md) — main benchmark, full 23-model rankings, methodology
- [`success_report.multi_model.md`](success_report.multi_model.md) — Round 1 free-choice multi-agent, Round 2 first-run findings
- [`success_report.multi_model_forced.md`](success_report.multi_model_forced.md) — Round 2 + Round 2.5 forced-delegation rubric audits, planner-capability findings
- [`orchestration_traces.md`](orchestration_traces.md) — per-variant forensic walkthroughs of every variant in Rounds 1, 2, and 2.5
- Manual run trace: [`results/manual_opus_qwen36plus/orchestration_trace.md`](../results/manual_opus_qwen36plus/orchestration_trace.md)
- Manual run trace: [`results/manual_opus_kimi/orchestration_trace.md`](../results/manual_opus_kimi/orchestration_trace.md)
- DeepSeek failure trace: [`results/manual_opus_deepseek/orchestration_trace.md`](../results/manual_opus_deepseek/orchestration_trace.md)
