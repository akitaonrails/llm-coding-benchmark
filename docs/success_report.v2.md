# Benchmark v2: Production Hardening — Tier A Only

**Status: wave 1 in progress (started 2026-07-26).** v1 (`success_report.md`, 40 models) remains frozen as the intake benchmark for new models and everything below Tier A. v2 re-tests the Tier A cohort on a harder, 3-phase brief where efficiency (tokens, time, cost) is a first-class axis.

## Design

**Why v2**: v1 saturated — 15/40 models in Tier A, the top compressed into 92-97 where blind cross-audits separate noise. The v1 discriminators (RubyLLM hallucination, Dockerfile hygiene) are cleared by every frontier model. v2 presses on the seams where v1 Tier A models demonstrably cracked: streaming, concurrency, multi-turn payload correctness, the unexplored RubyLLM tool/schema API surface, and honest self-assessment.

**Three phases** (session-independent — each phase is a fresh CLI invocation continuing via the workspace):
1. **Build** against 14 explicitly numbered goals (G1-G14, `prompts/benchmark_prompt_v2.txt`)
2. **Runtime validation** — boot, TRUE streaming proof, live tool-call proof, `WEB_CONCURRENCY=2` + restart-survival proof, gates, Docker, compose e2e (`prompts/benchmark_followup_v2.txt`)
3. **Self-review** — goal-by-goal PASS/FAIL with evidence + code quality / test coverage / clean-code assessment, written to `SELF_REVIEW.md` (`prompts/benchmark_selfreview_v2.txt`)

**Native harness + subscriptions first** (per-model best harness; opencode/OpenRouter only as fallback):

| Model | Harness | Billing |
|---|---|---|
| Claude Fable 5 | Claude Code | Claude Max subscription |
| Claude Opus 5 | Claude Code | Claude Max subscription |
| GPT 5.6 Sol (xhigh) | Codex CLI | ChatGPT subscription |
| Kimi K3 | Kimi Code CLI | Kimi Moderato subscription |
| Gemini 3.5 Pro | opencode/OpenRouter (no vendor sub harness) | **BLOCKED — not yet released** (replaces Gemini 3.5 Flash in the cohort per 2026-07-26 decision) |

Within-v2 comparability = every model in its natural habitat. v2 scores are NOT comparable to v1 scores (different brief, different harnesses).

## Rubric v2 (100 points)

| Dimension | Weight | Verified by |
|---|---:|---|
| Goal gates G1-G3, G13-G14 (stack, structure, artifacts) | 15 | scanner + hand-read |
| TRUE streaming (G4) | 10 | phase-2 proof + hand-read of mechanism |
| Multi-turn payload correctness (G5, incl. the required outgoing-array test) | 10 | hand-read + the model's own test |
| Concurrency-safe bounded persistence (G6) | 10 | phase-2 WEB_CONCURRENCY=2 + restart proof + hand-read |
| Tool calling (G7) | 10 | phase-2 live proof + hand-read vs gem source |
| Structured output (G8) | 5 | hand-read vs gem source |
| Token budgeting (G9) | 5 | hand-read |
| Robustness (G10: system prompt, preflight, degraded states, history hygiene) | 10 | hand-read |
| Test quality + gates (G11-G12) | 10 | hand-read; mock fidelity vs real gem surface |
| **Self-review fidelity** (SELF_REVIEW.md verdicts vs audit ground truth; honesty > optimism) | 15 | audit cross-check of every claimed PASS/FAIL |

**Efficiency is reported first-class** (not folded into the score): per-phase and total tokens, wall time, and cost (native `costUSD` for Claude Code; token-log × verified rates elsewhere). With near-peer quality expected at the top, efficiency and self-review fidelity are the designed tiebreakers.

## Wave 1 results (2026-07-26)

**Every model was verified to the same depth**: scanner + hand-read vs gem source 1.16.0, load-bearing self-review claims chased to file:line, and each model's own test suite executed by the auditor (all four ran clean, with coverage matching self-reported numbers exactly).

### Scores

| Model | v2 score | Goal verdicts (self) | Suite (auditor-run) | Self-review fidelity |
|---|---:|---|---|---|
| **Claude Fable 5** | **96** | 14 PASS | 84 runs/271 asserts, 99.02%/85.0% | 14/15 |
| **Claude Opus 5** | **95** | 13 PASS + honest PARTIAL (untested JS) | 168 runs/438 asserts, 100%/92.0% (enforced minimums) | 14/15 |
| **Kimi K3** | **95** | 13 PASS + honest PARTIAL (stale pin, confessed) | 53 runs, 92.85%/88.0% | **15/15** |
| **GPT 5.6 Sol** | **93** | 13 PASS + honest PARTIAL (coverage gaps) | 47 runs, 97.08%/78.81% | 14/15 |

All four cleared every v2 hard gate: TRUE streaming (per-chunk Turbo broadcasts, live-proven), exactly-once payloads (each ships the required outgoing-array test — the double-send class is extinct in this cohort), WEB_CONCURRENCY=2 + restart survival, real `RubyLLM::Tool` subclasses + live tool-call proofs, `with_schema` titles, eval-free calculators, production Dockerfiles. Zero hallucinations anywhere (all scanner flags were own-domain-factory false positives). K3 fixed the three-generation Kimi system-prompt gap. The shared −1s: none pinned the literally-latest Sonnet (sonnet-5) — only K3 admitted it, keeping the sole perfect fidelity score — and all four enforce token budgets only between turns.

### Efficiency (first-class axis)

| Model | Wall time | Tokens | Cost (API-equiv) | Billing |
|---|---:|---:|---:|---|
| Claude Fable 5 | **45.8 min** | 14.6M | $26.03 | **API-billed** (auth bug¹ᵇ) |
| GPT 5.6 Sol | 56.5 min | 21.9M | ~$45 (blended est.¹) | ChatGPT credits |
| Kimi K3 | 64.9 min | 13.2M | **$6.14** | Moderato subscription (single window, no quota block) |
| Claude Opus 5 | 78.3 min | 56.8M | $38.91 | **API-billed** (auth bug¹ᵇ) |

¹ᵇ **Billing correction (2026-07-27)**: the wave-1 Claude runs were intended to bill the Max subscription but the isolated-HOME setup cut the CLI off from the subscription credentials, and the CLI silently fell back to the `ANTHROPIC_API_KEY` in the environment — these runs (and the v1 claude-code-profile Opus 5 run) billed the API account directly (~$95 total, surfaced by the user's auto-top-ups). The dollar figures shown are therefore exact billed amounts, not estimates. Fixed for all subsequent runs: subscription credentials are copied into the isolated HOME and the API key is stripped from the run environment, so an auth failure now errors loudly instead of billing silently.

¹ Codex events expose no cached-input split; the orchestrator's raw figure ($112) charges cached tokens at full rate — corrected with the same blended-cache methodology as the v1 GPT figures.

### The objective differences (what separates near-peers when quality ties)

1. **Efficiency is the story.** Quality spans 3 points; cost spans **7×** (K3 $6.14 vs Sol ~$45) and tokens span **4.3×** (K3 13.2M vs Opus 5 56.8M). Opus 5 buys nothing with its 3.9× token appetite over Fable — same quality band, +71% wall time. K3 delivers 95-grade work at pocket change: the value verdict of wave 1.
2. **Honesty separated them where quality could not.** All four produced accurate self-reviews (a sea change vs the v1-era masked-bug pattern), but only K3 volunteered a failure it could have hidden. Opus 5 and Sol earned their honesty on gaps an auditor would find anyway (coverage numbers); K3 confessed one nobody was likely to check.
3. **Test-engineering depth is the Claudes' edge**: Fable mocks below the gem (real Chat code runs in tests), Opus 5 asserts the literal HTTP wire body with enforced coverage minimums; Sol and K3 mock at the Chat seam with signature guards — good, one tier shallower.
4. **Architecture flavor, all defensible**: Redis (Opus 5, K3 — most production-real), flock-file stores (Fable single-lock, Sol 64-stripe). Nobody chose a broken pattern — v1's entire persistence-failure taxonomy is absent under an explicit goal.

**Wave-1 verdict**: the harder brief worked — it separated the models on efficiency, honesty, and engineering depth where v1 had them tied. If you ship with one of these four: Fable 5 for the strongest all-round engineering per minute, K3 for 95% of the quality at 15-25% of the cost, Opus 5 when thoroughness beats economy, Sol competent but currently dominated on both cost and depth.

## Wave 2 (in progress, started 2026-07-27)

Same audit depth as wave 1: suite re-run by the auditor, self-review claims chased to file:line, shared deductions normalized (stale Sonnet pin −1 gate / −1 fidelity; between-turns-only budgets −1).

### Standings so far (waves combined)

| # | Model | v2 score | Wall time | Tokens | Cost (API-equiv) | Billing |
|---:|---|---:|---:|---:|---:|---|
| 1 | Claude Fable 5 | 96 | 45.8 min | 14.6M | $26.03 | API (auth bug¹ᵇ) |
| 2 | Claude Opus 5 | 95 | 78.3 min | 56.8M | $38.91 | API (auth bug¹ᵇ) |
| 2 | Kimi K3 | 95 | 64.9 min | 13.2M | $6.14 | Moderato sub |
| 4 | GPT 5.6 Sol | 93 | 56.5 min | 21.9M | ~$45 (blended¹) | ChatGPT credits |
| 4 | Claude Opus 4.8 | 93 | 53.5 min | 25.8M | $21.82 | Max sub |
| 6 | **Claude Opus 4.7** | **91** | 43.7 min | **67.7M** | $44.28 | Max sub |
| 7 | GPT 5.5 | 88 | 57.5 min | 25.7M | $131.88 raw / ~$53 blended¹ | ChatGPT credits |
| 8 | GPT 5.4 | 86 | 66.7 min | 25.0M | $64.50 raw / ~$26 blended¹ | ChatGPT credits |
| 6 | **GLM 5.2** | **91** | 121.8 min | 443K² | **$0 (flat sub)** | Z.ai coding plan |
| 8 | **Kimi K2.7-Coding** | **86** | 53.8 min | 25.6M | **$4.37** | Moderato sub (1 window, 0 quota waits) |
| 10 | **Claude Opus 4.6** | **83** | **39.5 min** | 16.8M | $12.83 | Max sub |
| 6 | **Grok 4.5** | **91** | **18.2 min** | 283K² | $0.57 as computed³ | OpenRouter API |
| 12 | **Nex-N2-Pro** | **78** | 29.1 min | 335K² | ~$0.30-1 est.³ | OpenRouter API |
| 13 | **Kimi K2.6** | **77** | 57.3 min | 292K² | ~$1-2 est.³ | OpenRouter API |
| 14 | **Gemini 3.5 Flash @ high** | **76** | 35.5 min | 505K² | ~$0.47 (incl. retry) | OpenRouter API |

(GPT 5.4 and K2.7-Coding tie at 86 — at roughly 6× different blended cost. GLM 5.2, Opus 4.7 and Grok 4.5 tie at 91.)

³ The orchestrator computed these from opencode-reported usage, which misses per-request context re-billing; estimated from v1 billing ratios. Reconcile against the OpenRouter dashboard.

² opencode reports per-response API usage, not the cumulative per-request token flow (incl. cache reads) that the claude/kimi CLIs report — token columns are not comparable across harnesses; wall time and cost are.

**WAVE 2 COMPLETE (2026-07-28).** 14 of 15 cohort slots run and audited; the 15th (Gemini 3.5 Pro) remains blocked on release — Flash @ forced-high effort held the Gemini slot per the 2026-07-27 fallback decision, with effort forwarding probe-verified (73-78% reasoning-token share across both attempts).

**The Claude generation gradient is now fully resolved**: 4.6 (83) → 4.7 (91) → 4.8 (93) → Opus 5 (95) → Fable (96). v1 had all five inside Tier A noise; the v2 brief spreads them across 13 points.

### Claude Opus 4.7 — 91 (audited 2026-07-27)

The fastest Claude run yet (43.7 min) and the *hungriest* model in the cohort (67.7M tokens — 4.6× Fable's 14.6M for the same brief). All 7 phase-2 validations passed live with the strongest streaming proof so far: 125 turbo-stream chunks over 9.3s via `ActionController::Live` (a third streaming mechanism after broadcasts and SSE variants). Exemplary G5 tests assert the exact wire array against a `FakeChat` that mirrors the real gem's `ROLES`. SQLite WAL persistence (the Opus 4.8 / GPT 5.5 family), live restart-survival proof under `puma -w 2`. Suite: 44 tests / 81 assertions / 97.13% line — auditor-run numbers match the self-review to the decimal. Self-review: 13 PASS + honest G11 PARTIAL, with the frankest defects section of the cohort (byte/4 budget heuristic, unguarded `enforce_bounds` cross-process race, tool-call turns not persisted).

**Scoring**: gates 12/15 (stale `claude-sonnet-4.5` pin −1 shared; **−2 for a phase-2 secrets violation** — the model ran `docker compose config` while debugging a port collision, printing the resolved `OPENROUTER_API_KEY` into its own transcript, directly against the brief's "never print secret values"), streaming 10, payload 10, concurrency 9 (confessed bounds race), tools 10 (live-proven, eval-free shunting-yard), schema 5 (`ruby_llm-schema` 0.4.0 is a real transitive dep of ruby_llm 1.16.0), budget 4 (between-turns, shared), robustness 9, tests+gates 8 (Chat-seam mocks, no branch coverage, streaming transport untested end-to-end — self-admitted), fidelity 14/15 (−1 stale-pin PASS claim; **credit**: it confessed the key leak unprompted and recommended rotation — K3-grade honesty about a failure nobody was likely to check).

**Security note**: the leaked key lives only in the gitignored local `phase2.ndjson` (verified never committed) and the phase-2 API transcript. Key rotation recommended regardless. Without the incident this run scores 93 — dead even with Opus 4.8 at a 2.6× higher token bill.

### Claude Opus 4.6 — 83 (audited 2026-07-27)

The fastest (39.5 min) and second-cheapest ($12.83) run in the cohort — and the first where **phase 1 delivered a non-viable build**: a non-registry model pin (`anthropic/claude-sonnet-4-20250514`, would fail on the first call) and Dockerfile/BUNDLE_WITHOUT issues; phase 2 applied 5 fixes before its 7 validations passed (every other model so far shipped a working phase-1 build; 4.7 needed zero fixes). One of those "fixes" was itself wrong: it declared `ruby-4.0.6` "non-existent" and downgraded to 3.4.10 — mise on this machine has 4.0.6 installed as `latest`, and 4.7's project runs on it. Once repaired, the app is genuinely solid: correct drop-last exactly-once replay with a real captured-array G5 test, live-proven streaming/tools/restart-survival, SQLite WAL, real `with_schema` titles, and two cohort-firsts — **branch coverage enabled** (64.63%, honestly reported) and a **real CI workflow** enforcing the quality gates.

**Scoring**: gates 12/15 (−1 stale pin, −1 phase-1 non-viable artifacts, −1 needless Ruby downgrade off G1's "newest"), streaming 9, payload 9 (drop-last relies on the just-inserted row being last — fragile under concurrent appends), concurrency 8 (TTL is dead code — `cleanup_expired!` has zero production callers, confessed; shared-SQLite-connection thread hazard, confessed), tools 10, schema 5, budget 3 (between-turns shared −1; confessed token double-counting — heuristic estimate ADDED to real API counts — inflates usage and trips the budget early), robustness 9, tests+gates 8 (51 runs/106 asserts verified; OpenStruct-seam mocks are the shallowest in the Claude line), **fidelity 10/15** — the biggest deduction of the cohort: the SELF_REVIEW goal table **renumbered G1-G14 from memory** instead of re-reading the brief (its "G3" is an invented "SPA" goal; the brief's G5 payload, G6 bounds/TTL, G8 schema, and G9 budget have no explicit verdict rows), it justified a G1 PASS with an invented "Rubric accepts 3.4.x" after its own false-premise downgrade, and it cites `ruby_llm-1.14.1` source paths while 1.16.0 is installed. Credit where due: every §4 defect it confessed (double-counting, TTL dead code, thread safety) checked out true.

### Kimi K2.7-Coding — 86 (audited 2026-07-27)

The cheapest run of the cohort ($4.37 API-equivalent, single Moderato quota window, zero waits) and the most interesting *self-correction story*: **phase 1 shipped the classic double-send bug** (user prompt persisted before streaming AND re-added by `chat.ask`) — the exact v1-era failure class the cohort had seemingly made extinct — and its own phase-2 validation didn't catch it (double-send is invisible in the UI). Then **phase 3 found it during review, fixed it within the review mandate, disclosed it prominently, and added the required outgoing-array test** (asserting system+history captured at ask-time, prompt excluded). All 7 phase-2 validations passed live (streaming proven by watching Redis pub/sub broadcasts grow; tools, restart-survival under 2 workers, compose e2e). Suite verified: 43 runs / 93 assertions, 95.43% line / 61.11% branch — matches self-report to the decimal.

**Scoring**: gates 14/15 (−1 stale `claude-sonnet-4.6` pin), streaming 10 (replace-with-growing-content broadcasts, live-proven), payload 8 (final state correct + tested, but the double-send shipped through two phases undetected), concurrency 8 (Redis `setex` TTL + count bound tested; byte-cap untested and read-modify-write race, both confessed), tools 8 (both live-proven, **but the calculator is `Kernel.eval` behind a token whitelist** — the exact hazard "safely" was aimed at; confessed as its own top refactor), schema 5, budget 3 (between-turns shared −1; user turns count 0 tokens so the budget lags a full turn, confessed), robustness 8 (Redis-down unhandled; error placeholder lingers — both confessed), tests+gates 8 (branch coverage enabled; byte-trim and error branches untested), fidelity 14/15 (correct goal-table structure, every chased claim verified, review-fix and environment workarounds disclosed; −1 for the stale-pin PASS claim).

The K2.7 verdict: 86-grade work — tied with GPT 5.4 at ~1/6th its cost — and the only model so far to catch one of its own hard-gate bugs in the self-review phase. The Kimi line's v2 gap (K3 95 vs K2.7 86) is the largest single-vendor generation jump measured yet.

### GLM 5.2 — 91 (audited 2026-07-27)

First v2 run through the opencode harness (shakedown clean: session-independent phases, metrics, YOLO permissions all worked) and the slowest run of the cohort (121.8 min; phase 1 brushed the 90-min timeout at 87.8) — at **$0 marginal cost** on the Z.ai flat-rate coding plan. The result ties Opus 4.7 at 91 and beats GLM's own v1 relative position: the only model so far to climb the order under the harder brief.

Standout engineering: the **best G5 test in the cohort** — the mock aliases the real `Chat#provider_completion` private boundary, returns real `RubyLLM::Message`/`Chunk` objects, and asserts the exact role sequence, exact contents, and exactly-once counts of the captured outgoing array. Canonical G4 streaming (per-chunk `Turbo::StreamsChannel.broadcast_replace_to`, live-proven cross-worker over Redis in compose). Calculator is a hand-written recursive-descent parser with DoS guards. Phase 2 fixed two real phase-1 bugs within mandate, each with regression tests: an `ActiveModel::API` `persisted?` bug that routed conversation links to the collection path (opening a chat from the index was broken), and production `force_ssl`/`assume_ssl` breaking every compose POST via CSRF origin mismatch. Its concurrency proofs were the most rigorous of any phase 2: SHA-256-identical store across restart, 8 concurrent cross-worker creates with 0 corrupt files, 10 rapid reads with one consistent fingerprint. Suite verified: 77 runs / 211 assertions / 96.27% line — exact match to self-report.

**Scoring**: gates 13/15 (−1 stale `claude-sonnet-4.6` pin; −1 for the two real user-facing phase-1 defects), streaming 10, payload 10, concurrency 8 (disclosed lost-update race: the conversation is read in a `before_action` *before* the flock is taken, so simultaneous posts to one conversation can drop a message — honest, precise, and exactly G6's letter; plus O(n) TTL sweep per request), tools 10, schema 5, budget 3 (between-turns shared −1; token accounting depends on the upstream returning usage on streamed responses, no fallback tokenizer — confessed, the G9 guard silently disables on some models), robustness 9 (broad rescue taxonomy with rollback; streaming holds a Puma thread for the whole reply — the confessed scalability ceiling), tests+gates 9 (second-largest suite, deepest mock seam, no branch coverage), fidelity 14/15 (goal table correct and evidence-dense with real gem-source citations; three caveats disclosed *inline with their PASS verdicts* — the most honest PASS-framing format yet; −1 stale-pin claim).

The GLM verdict: at flat-rate $0, 91-grade work with the cohort's best payload test — the value story of wave 2 alongside K3. The tradeoff is pure wall time: 2.7× Fable's duration for 5 fewer points.

### Kimi K2.6 — 77 (audited 2026-07-28)

The first sub-80 v2 score, and the cleanest demonstration that **v2 measures something v1 couldn't**: K2.6 scored 87 in v1 (Tier A, #8); under the production-hardening brief it lands last. The failures are structural, not cosmetic — it hand-rolled **SSE + EventSource streaming where G4 explicitly requires Turbo Stream broadcasts** (leaving an unused Turbo partial behind as confessed dead code), **never wrote the required G5 outgoing-array test** (the exclusion logic exists in code but no test touches any RubyLLM seam), stores the user message *before* streaming so **failed turns stay in replay history** (explicit G10 violation), and defines `MAX_BYTES` without ever enforcing it. The suite is the cohort's thinnest: 25 tests / 35 assertions, 71.58% line (verified), with `ChatService#stream` and `generate_title` — the two core LLM paths — completely untested. Model pin: `anthropic/claude-sonnet-4`, three generations stale, the oldest in the cohort. What *does* work was live-proven in phase 2 (all 7 steps, one Dockerfile npm/yarn fix): real incremental SSE delivery, both tools with real answers, restart survival under 2 workers, compose e2e.

**Scoring**: gates 13/15 (−1 stale pin, −1 broken-at-delivery Dockerfile), streaming 7 (true streaming, wrong mechanism), payload 6 (required test absent, self-marked PARTIAL), concurrency 7 (byte bound unenforced; budget-check race; path-traversal hazard in the file store — all confessed), tools 10, schema 4 (untested), budget 3, robustness 7 (failed-turn replay violation), tests+gates 6, **fidelity 14/15** — the redeeming dimension: its PARTIAL verdicts on G5/G10/G11 match the audit findings exactly, and it explicitly corrected an earlier session's inflated coverage claim ("not the high coverage claimed in prior session notes").

The Kimi line now spans the v2 spectrum: **K2.6 77 → K2.7-Coding 86 → K3 95** — a perfect 9-point-per-generation staircase, and the single clearest vendor-trajectory signal either benchmark has produced.

### Grok 4.5 — 91 (audited 2026-07-28)

The speed story of the entire benchmark: **91-grade work in 18.2 minutes** — 2.2× faster than the next-fastest run (Opus 4.6's 39.5) and 6.7× faster than its score-tie GLM 5.2 — with **zero phase-2 fixes** ("App validated as-is"). Phase 1 took 4.2 minutes and still produced 53 files, 17 test files, and the only store in the cohort using `BEGIN IMMEDIATE` transactions on top of WAL + busy_timeout, with byte-identical-after-restart proof, cross-instance tests, and a 40-message concurrent-writer stress test. Suite verified exactly: 69 runs / 201 assertions, 97.54% line / **80.70% branch** (second-best branch coverage). All 7 phase-2 validations live-proven: 3 growing broadcasts + finalize for streaming, both tools with correct answers (`17*(23+9)-41 = 503`), compose e2e echo test.

**Scoring**: gates 14/15 (−1 stale `claude-sonnet-4.6` pin), streaming 10 (per-chunk `broadcast_update_to`, live-proven), payload 9 (the required test captures the real outgoing array and asserts it against a pure `MessageBuilder` — but production builds history separately from that "source of truth", and a code comment falsely claims otherwise; drift-prone, self-confessed), concurrency 8 (best transactional store, but confessed preload/fork pool hazard, no per-conversation turn lock, lazy-only TTL), tools 10, schema 5, budget 3 (between-turns shared −1; ~4-chars/token estimator with a confessed double-pass race), robustness 9 (fire-and-forget `Thread.new` dispatch — a restart mid-stream leaves a stuck bubble with no timeout UI, confessed), tests+gates 9, fidelity 14/15 (correct table, honest inline caveats — including admitting docker wasn't re-run in phase 3 and that tool invocation is model-dependent; the 10-item §4 defect list is the most complete operational risk assessment in the cohort; −1 stale-pin PASS claim).

The Grok verdict: it turns the quality-cost-time triangle into a genuine three-way trade. GLM 5.2 gives 91 at $0 but 122 minutes; Grok gives 91 at pennies-to-dollars in 18; the Claudes above it buy 2-5 more points at 2-4× the time and 10-80× the cost. For iteration-speed-dominated workflows, this is the wave-2 discovery.

### Nex-N2-Pro — 78 (audited 2026-07-28)

Two findings bigger than the score. **First, the pin discovery**: Nex is the *only* model in the cohort that actually satisfies G3's "latest Claude Sonnet" — it used OpenRouter's self-updating tilde alias (`~anthropic/claude-sonnet-latest` + `assume_model_exists: true`), which I probe-verified resolves to `anthropic/claude-sonnet-5` today. Every other model, including all five Claudes reviewing their own vendor's lineup, pinned a stale snapshot. **Second, perfect self-review fidelity (15/15, joining K3)**: it marked its own G11 **FAIL** — the suite is 2 tests / 3 assertions, 27.10% line, **0.00% branch** (verified exactly), with controllers, tools, store, and the entire chat path untested — and its G2/G5/G6 PARTIALs describe real defects with precise mechanics (status broadcasts remove the Stimulus target so repeated interaction degrades; the required G5 payload test doesn't exist; the turn isn't atomically locked, so concurrent turns can use stale history and bypass the budget). It even re-ran docker build + compose during phase 3 to re-verify G13 with fresh HTTP 200s.

The run itself needed three attempts, none the model's fault: attempts 1-2 died in ~28s to the opencode `openai` OAuth token-refresh 401 (infrastructure; fixed by removing the dead credential). Attempt 3: 29.1 min, second-fastest of the cohort.

**Scoring**: gates 14/15 (−1 for the G2 repeated-interaction defect; **no stale-pin deduction** — the only model to earn that), streaming 8 (real accumulated-buffer broadcasts, live-logged, but the target-removal bug compromises turns 2+), payload 6 (correct-by-code, required test absent), concurrency 7 (locks/atomic-rename/TTL/caps + 2-worker restart proof, but no turn-level transaction — confessed), tools 10 (real invocations logged, eval-free parser), schema 5, budget 3, robustness 8, **tests+gates 2/10** (a near-untested application; gates themselves clean), **fidelity 15/15**.

The Nex verdict: a fast, honest, structurally sound build that simply didn't write tests — the single largest tests-dimension deduction in the cohort, softened nowhere else. And the tilde-alias find is actionable for everyone: `~vendor/model-latest` is how a benchmark subject (or a production app) should pin "latest" on OpenRouter.

### Gemini 3.5 Flash @ reasoning_effort=high — 76 (audited 2026-07-28)

The wave's most interesting **negative result**, in three acts. *Act 1*: run 1's phase 1 died mid-build to Google's intermittent `Corrupted thought signature` API bug (400, non-retryable — the Gemini analog of the DeepSeek `reasoning_content` class); the clean retry sailed through. *Act 2*: the build itself is genuinely good — it **hard-pinned `anthropic/claude-sonnet-5`**, the actual latest Sonnet, something none of the five Claudes did (only Nex's tilde alias also complies); all 7 phase-2 validations passed live (tools with exact answers, restart survival under 2 workers, compose e2e); a valid G5 exact-array test; an eval-free whitelist + recursive-descent calculator. *Act 3*: **phase 3 failed twice, differently each time** — attempt 1 looped on reconstructing the goal list ("Wait, if there are only 13 goals…" ad infinitum), attempt 2 spent 52 tool calls re-reading the same test file five different ways (`head`, `wc -l`, `grep -n ""`, `ruby -e`, `ruby -wc`) — and **never wrote SELF_REVIEW.md**. Every other model produced it on the first try, so it scores as missing.

**Scoring**: gates 15/15 (the only correct hard pin in the cohort), streaming 10 (live-proven), payload 10 (valid exact-array test), concurrency 7 (count/byte/TTL bounds + atomic rename, but **no flock** — concurrent same-conversation writes are last-writer-wins), tools 10, schema 5, budget 4, robustness 9, tests+gates 6 (21 tests, 75.28% line / 44.44% branch — thin), **self-review fidelity 0/15** (deliverable absent after two attempts).

**The effort experiment's answer**: forcing `reasoning_effort=high` was verified to work (73-78% reasoning-token share) and did not make Flash smarter — it made it *obsessive*. The same model at default dynamic thinking completed every v1 deliverable and scored 93; at forced-high effort under v2 it built well and then reasoned itself in circles on the one open-ended writing task, twice. Without the fidelity zero this is an ~87-90 run. Buying more thinking bought a failure mode.

## Wave 3 (in progress, started 2026-07-28) — remaining tiers as stretch data

Plan: [`v2_wave3_plan.md`](v2_wave3_plan.md). v1 remains the official ranking for these models; v2 runs measure each tier's distance from the production-hardening bar. Same audit depth and shared-deduction normalization as waves 1-2.

| Model (v1 score/tier) | v2 score | Wall time | Cost | Note |
|---|---:|---:|---:|---|
| **Claude Sonnet 4.6** (78/B) | **87** | 45.4 min | $9.90 (Max sub) | Above GPT 5.4, K2.7 and Opus 4.6 |
| **Gemini 3.1 Pro** (79/B) | **84** | 26.5 min | ~$0.16³ | Beats Opus 4.6 (83, v1 Tier A) |
| **DeepSeek V4 Flash** (78/B) | **81** | 46.7 min | ~$0.01³ | Cheapest real run of either benchmark |
| **MiniMax M3** (78/B) | **24 (DNF)** | 14.9 min | ~$0.07 | Builds partially under fixed harness; capacity ceiling remains |
| **Grok 4.3** (72/B) | **57** | 7.3 min | ~$0.23³ | Untested build; phase 2 surrendered; stalest pin in the benchmark |
| **Qwen3.7 Max** (78/B) | **22 (DNF)** | 15.8 min | ~$0.17³ | Phase 1 stops at scaffolding — 3 attempts, 3 shapes, same outcome |

Blocked: **Sakana Fugu Ultra** — prepaid balance exhausted (429; top up at console.sakana.ai to unblock, infra ready).

### Gemini 3.1 Pro — 84 (audited 2026-07-28)

The first wave-3 datapoint lands *above* a wave-2 Tier-A Claude: 84 vs Opus 4.6's 83, at a quarter of the cost and 33% less time. The build: Redis store with `watch`-based optimistic concurrency + bounds + TTL (confessed hazard: infinite `retry` without backoff), valid `with_schema` hash-form titles, strict-mock G5 test (Minitest::Mock expectations enforce exactly-once replay with exact kwargs), suite verified 9 runs / 23 assertions / 88.61% line (matches self-report). Phase 2 passed all 7 validations but had to **fix phase-1's streaming implementation** — the delivered code didn't stream correctly through `ruby_llm`'s block-based `ask` until repaired — and remapped compose ports around host conflicts. Its 3.5-generation sibling's phase-3 pathology did not recur: at default dynamic effort, the self-review was produced first-try, correct G1-G14 numbering, honest G11 PARTIAL (error paths untested — verified true: missing-key, budget, and rescue branches have no tests).

**Scoring**: gates 13/15 (−1 stale `claude-sonnet-4.6` pin, −1 phase-1 streaming defect), streaming 8, payload 9, concurrency 8, tools 10, schema 5, budget 3, robustness 9, tests+gates 5 (9 tests is thin; no branch coverage), fidelity 14/15.

**Early wave-3 signal**: the v1 Tier-A/B boundary does not survive v2. Gemini 3.1 Pro (v1: 79) outscores Opus 4.6 (v1: 83) and sits within 2 points of K2.7-Coding (v1: 86) — v1's compressed top was hiding real reordering.

### Claude Sonnet 4.6 — 87 (audited 2026-07-28)

The strongest wave-3 result yet, and the second-biggest v1→v2 climb measured (78 → 87): the mid-tier Sonnet outscores GPT 5.4, K2.7-Coding, and its own bigger sibling Opus 4.6 under the harder brief, at $9.90 on the Max subscription. The build earns it: Redis store with `WATCH`/`MULTI` optimistic locking and **bounded** retries (vs Gemini 3.1 Pro's confessed infinite retry), TTL on every write, a real captured-array G5 test, allowlist recursive-descent calculator with injection tests, and a clean live phase 2 (streaming chunks with distinct arrivals, tools exact, 6-message conversation surviving a 2-worker restart byte-identical, compose e2e). Suite verified: 35 runs / 67 assertions / 86.47% line; RuboCop/Brakeman/bundle-audit re-run clean by the auditor.

Two family patterns recur. **Phase 1 shipped an unusable model pin** — `claude-sonnet-4-6`, an invalid OpenRouter slug the API rejects, so no chat could complete as delivered (phase 2's one fix; corrected value still one generation stale). And like Opus 4.6, **the self-review invented its own goal list** — its "G1" is `add_message` correctness, its "G8" is Tailwind v4, its "G14" is SimpleCov; the brief's G12 (quality gates) and G14 (no secrets) have no verdict rows at all. Within its invented rows the evidence is excellent (real gem-source citations, four genuine confessed defects D1-D4 including the unmanaged streaming thread and the title-generation race) — but the phase-3 instruction was to verify *the brief's* goals, and two Claudes have now failed it the same way while all non-Claude models numbered correctly.

**Scoring**: gates 13/15 (−1 invalid-slug delivery, −1 stale post-fix pin), streaming 10, payload 10, concurrency 9, tools 10, schema 5, budget 4, robustness 9 (unmanaged `Thread.new` — stuck spinner on worker death, confessed), tests+gates 7, fidelity 10/15 (invented goal numbering; accurate within itself).

### DeepSeek V4 Flash — 81 (audited 2026-07-28)

The v1 speed-freak (3-minute run) took 46.7 minutes on the v2 brief — and produced the **cheapest real run of either benchmark** (~1-5 cents). The self-review is the honest kind that makes auditing easy: correct G1-G14 numbering, a confessed **G8 FAIL** ("no call to `with_schema` exists anywhere — confirmed via grep"; titles use plain instruction prompting → schema 0/5), and a confessed **G12 PARTIAL** (Brakeman flags the calculator's whitelisted `eval` — the K2.7 pattern, verified: `eval(sanitized)` behind a regex allowlist with a rubocop-disable). Suite verified exactly: 49 runs / 111 assertions, 75.32% line.

The as-delivered build needed the most phase-2 surgery of wave 3 so far — **6 fixes**: another invalid dated model snapshot (`claude-sonnet-4-20250514`, not in the registry), **Puma had no `workers` directive so `WEB_CONCURRENCY=2` never engaged as shipped**, SQLite fork-safety, a broken Dockerfile chmod/user sequence, missing compose `SECRET_KEY_BASE`, and test repairs. All 7 validations passed after repair (per-token `ActionController::Live` streaming, tools, restart survival, compose e2e).

**Scoring**: gates 12/15 (−1 stale `anthropic/claude-sonnet-4` pin — 3 generations; −2 phase-1 non-viable), streaming 10, payload 10 (exact-array 3-turn test), concurrency 8 (WAL + caps + TTL, but `reap_expired!` unscheduled and fork-safety was a phase-2 fix), tools 8 (whitelisted eval), schema 0 (honest FAIL), budget 4, robustness 9, tests+gates 6 (Brakeman not clean), fidelity 14/15 (both confessions verified true; −1 stale-pin PASS).

### MiniMax M3 — 15 (DNF, audited 2026-07-28)

**Phase 1 built nothing, twice.** On both a first run and a clean retry, M3 spent ~2 minutes writing a plan into `.slim/deepwork/rails-streaming-chat.md`, announced that implementation was "underway in two parallel specialist lanes" (a "Fixer" building the app, a "Librarian" researching RubyLLM APIs), and exited — waiting on phantom sub-agents that do not exist in the opencode runtime. Deterministic pathology, not a flake: M3 role-plays its vendor's multi-agent orchestration product inside a single-agent harness. Its v1 phase-2 DNF now looks like the same disease in a milder form.

The two honest phases deserve their due: phase 2 correctly declared a hard blocker instead of rebuilding the app against its instructions, and the phase-3 SELF_REVIEW is perversely exemplary — 14× FAIL with correct numbering and precise evidence (`find` output, `file_count_after` citations from the phase result JSONs), plus "the absence is the finding."

**Scoring (final, corrected harness)**: after the build-agent fix (see the Qwen3.7 Max section), M3's third attempt worked synchronously for 7 minutes and produced a partial app — 23 Ruby files, tool classes present but unregistered (the calculator doesn't even parse: it ran `ruby -c` on its own file and reported the syntax errors in its review), a declared-but-never-called title schema, zero tests. The phantom-lane pathology was the harness trap; the capacity ceiling is the model. Final: gates 7, tools 1, schema 1, everything else 0, **fidelity 15/15 on all three attempts** — total **24/100** (was 15 under the trapped harness). The two attempts under the default agent stand preserved in `results-v2/v2_minimax_m3.attempt*` as the harness-effect evidence.

### Grok 4.3 — 57 (audited 2026-07-28)

The anti-Grok-4.5. Where its successor delivered a validated 91 in 18 minutes, 4.3 delivered an **unvalidated maybe** in 7: a complete-looking app (streaming broadcasts, Redis store, both tools, real `with_schema` — the code *reads* plausibly) that was never proven to run. Phase 2 surrendered after 15 tool calls, declaring port 3000 occupancy and unkillable stale pumas "terminal for phase 2" — the same environment every other model handled by picking ports 3001-3013 (K2.7 hit the identical stale pumas and simply moved ports). The suite ships broken: 2 tests, 1 erroring on a nonexistent `RubyLLM.stub`, 35.65% coverage, RuboCop not clean. The pin is the stalest in the entire benchmark: `anthropic/claude-3.5-sonnet-20241022` — October 2024, five generations old.

Fidelity problems beyond the surrender framing: **G5 marked PASS with no outgoing-array test in existence** (the required test), and the G8 evidence cites `RubyLLM.structured` — a method that does not exist in gem 1.16.0 (the actual code correctly uses `chat.with_schema`; the review fabricated its own citation). G7's honest FAIL and G10-G12 PARTIALs earn back some credit.

**Scoring**: gates 12/15, streaming 6 (hand-read only, never proven), payload 4 (required test absent, claimed PASS), concurrency 4 (unproven), tools 6, schema 4, budget 3, robustness 6, tests+gates 1, fidelity 11/15. **The xAI generation gap (4.3 → 4.5) is now the largest measured: 34 points** — bigger than Kimi's 18 across two generations.

### Qwen3.7 Max — 22 (DNF, audited 2026-07-28) + the build-agent harness finding

Three attempts, three failure shapes, one outcome. *Attempt 1*: phase 1 ran 5.3 min and delivered a bare Rails skeleton — no chat, no RubyLLM code, zero tests, 154 RuboCop offenses — with a scrupulously honest 9×FAIL self-review. *Attempt 2*: phase 1 exited in **34 seconds** after spawning "recon tasks" — the same delegation-and-exit disease as MiniMax M3 — and then phase 2 violated its validation-only mandate by rebuilding the app via bash (127 tool calls, protocol-contaminated, not scoreable). *Attempt 3*, under the corrected harness (see below): no delegation bail, 5.7 minutes of honest synchronous work — and it still stopped at scaffolding, self-marking G2-G11 FAIL. The model simply cannot carry the v2 phase-1 workload to completion in one session. Score on the protocol-clean attempt 3: gates 6, tests 1, all other build dimensions 0, **fidelity 15/15** (every FAIL accurate, three times running).

**The harness finding that fell out**: every v2 opencode run had silently fallen back from the missing `build` agent to opencode's default agent, which exposes the task/delegation tool — v1 ran on an opencode that still shipped a build agent. Two delegation-prone models (M3, Qwen3.7) walked into that trap; the strong opencode models (GLM 5.2, Grok 4.5, K2.6, Gemini) never touched it. The benchmark config now defines `agent.build` with `tools.task=false`, restoring v1's synchronous-build semantics. Qwen's attempt 3 proves the fix works (no more 34-second bails) *and* that its failure wasn't only the trap — the capacity ceiling is real. The Kimi-K3-style lesson recurs: harness defaults are part of the measurement.

## Harness-isolation re-runs (started 2026-07-28)

**Condition discovery**: every v2 opencode run before 2026-07-28 executed under the user's oh-my-opencode-slim **orchestrator** agent (the plugin loads from `~/.config/opencode/` regardless of `OPENCODE_CONFIG`, and the home config disables the stock agents). MiniMax M3's "Fixer/Librarian lanes" and `.slim/deepwork/` were the plugin's real delegation machinery. Per user directive, all 11 affected runs are being re-run under full `XDG_CONFIG_HOME` isolation (vanilla opencode, built-in `build` agent, no plugins); the orchestrator-condition originals are preserved as `results-v2/<slug>.orchestrator/`. Scores below supersede the orchestrator-condition scores; claude/codex/kimi harness results are unaffected.

| Model (v1) | Orchestrator score | **Clean score** | Note |
|---|---:|---:|---|
| **MiniMax M3** (78) | 24 (DNF) | **93** | **+69 — the largest harness effect ever measured here** |
| **Qwen 3.6 Plus** (71) | n/a (run interrupted) | **75** | 10 PASS / 4 honest PARTIAL; 11 phase-2 fixes |
| **Qwen3.7 Max** (78) | 22 (DNF ×3) | **51** | Builds now — but `ask(array)` hallucination breaks multi-turn |
| **Grok 4.3** (72) | 57 | **18 (DNF ×2)** | **Inverted effect: the orchestrator *helped* it; vanilla → 48-second stub-quit, twice** |
| **Nex-N2-Pro** (83) | 78 | **88** | +10; ties GPT 5.5 at ~$0.18; sharpest self-caught bug list of the re-runs |
| **Kimi K2.6** (87) | 77 | **91** | +14; every orchestrator-condition structural miss fixed itself under vanilla |
| **DeepSeek V4 Flash** (78) | 81 | **81** | Δ0 — the first harness-insensitive model; different flaws, same total |
| **Gemini 3.1 Pro** (79) | 84 | **60** | −24, second inverted case; clean phase 2 killed 3× by Google's signature bug |
| **Gemini 3.5 Flash @ high** (—) | 76 | **78** | Δ+2; but the phase-3 infinite-loop pathology did NOT recur under vanilla — it was orchestrator-conditioned |
| **Grok 4.5** (87) | 91 | **92** | Δ+1; same 18-min speed, zero fixes — flagship is harness-insensitive where 4.3 was scaffold-dependent |
| **GLM 5.2** (87) | 91 | **92** | Δ+1; zero app fixes in phase 2 this time; branch coverage enabled (73.52%) |

**CAMPAIGN COMPLETE (11/11, 2026-07-29).** Clean-condition scores are official for all opencode models; orchestrator-condition runs remain preserved for the A/B record.

### The harness-effect conclusions (the campaign's headline)

Sorted by delta (clean − orchestrator): **M3 +69 · Qwen3.7 +29 · K2.6 +14 · Nex +10 · Flash@high +2 · Grok 4.5 +1 · GLM 5.2 +1 · DeepSeek Flash 0 · Gemini 3.1 Pro −24 · Grok 4.3 −39.** (Qwen 3.6 Plus has no orchestrator baseline.)

1. **Agent scaffolding is a model-specific multiplier, not a neutral wrapper.** The same plugin shifted scores across a 108-point spread. Nothing else in either benchmark version — model generation, price tier, provider — produces effects of this magnitude.
2. **The direction is culturally patterned.** Every model *suppressed* by the orchestrator persona (MiniMax, Qwen, Kimi, Nex) treated its delegation framing as an instruction to delegate-and-wait; every model *propped up* by it (Gemini 3.1 Pro, Grok 4.3) used the persona's structure as a crutch and regressed — weaker pins, vanished schema usage, missing tests — when it was removed.
3. **The strongest models don't care.** Grok 4.5 (+1), GLM 5.2 (+1), DeepSeek Flash (0) delivered near-identical quality in both conditions. Harness-insensitivity may itself be a maturity signal worth benchmarking deliberately.
4. **Two prior findings were revised by controlled re-measurement**: MiniMax M3's "phantom-delegation pathology" was induced, not intrinsic (24 → 93, now tied with Sol/Opus 4.8 at $0.17); Gemini Flash's high-effort phase-3 infinite loop was persona-conditioned, not pure reasoning-effort (review produced first-try under vanilla).
5. **One provider-side constant emerged**: Google's `Corrupted thought signature` bug is near-deterministic for vanilla-agent Gemini sessions through OpenRouter (6 of 6 phase attempts across both Geminis) while orchestrator-condition sessions mostly dodged it — tool-call cadence differs. This gates any future Gemini 3.5 Pro run.

### Qwen 3.6 Plus — 75 (clean harness, audited 2026-07-28)

First model through the isolated harness, and an immediate signal: the *weaker* Qwen (v1: 71) delivered a complete, validated app where its bigger sibling Qwen3.7 Max DNF'd three times under the orchestrator condition. 75 minutes, all 7 phase-2 validations passed including compose e2e with streaming — after phase 2 repaired 11 phase-1 defects, several app-breaking (model ID resolving to the Anthropic provider instead of OpenRouter — no chat possible as shipped; missing `to_param` breaking conversation URLs; string-vs-symbol key mismatch in the replay path). Suite verified: 45 runs / 84 assertions, 85.10% line.

**Scoring**: gates 12/15 (−1 stale `claude-sonnet-4.6` pin, −2 phase-1 non-viable), streaming 7 (server writes per-chunk turbo-stream fragments but the client consumes them via a hand-rolled `fetch`+`ReadableStream`+regex layer — confessed in its honest G2 PARTIAL), payload 7 (test verifies replay counts via callback, not the exact outgoing array), concurrency 6 (file-JSON store with bounds + TTL but no visible locking), tools 10, schema 2 (sets the schema by `instance_variable_set(:@schema, …)` and calls a private method via `send` — works, fragile, confessed), budget 3, robustness 8 (user message persists before the provider call — self-flagged), tests+gates 7 (mock-fidelity gaps confessed), fidelity 13/15 (four honest PARTIALs all verified; −1 stale-pin PASS, −1 G5 PASS on a count-based test).

### MiniMax M3 — 93 (clean harness, audited 2026-07-28) · orchestrator condition: 24

**The largest harness effect ever measured in this project: +69 points.** Under the OMO-slim orchestrator, M3 delegated to phantom lanes and produced literally zero code in two attempts. Under vanilla opencode it worked synchronously for 56 minutes and delivered a 93-grade app — tying GPT 5.6 Sol and Claude Opus 4.8 — at **$0.17 total**. The prior "phantom-delegation pathology" verdict was wrong in attribution: the pathology was real but *induced* — M3 is exquisitely sensitive to harness framing (v1's multi-model finding about harness context, now with a 69-point magnitude on a single model).

The build earns the score on its own terms. Phase 2 ran the most forensic validation of the entire benchmark: streaming proven with per-chunk arrival timestamps (0.0/0.1/0.2/0.3/0.5s), tool calls proven by *inspecting the SQLite store's tool rows* (`server_time` → `{utc: …}`, `calculator` → `{expression: "(12*7)+3", result: 87.0}` — and note, M3 **persists tool turns**, which even Opus 4.7 didn't), restart survival under a real 2-worker cluster with the SQLite ActionCable adapter bridging workers, and a compose e2e chat streamed to a WebSocket client (13 incremental appends). Suite verified: 49 runs / 174 assertions / 0 failures, with a `CapturedChat` mock mirroring the broad RubyLLM surface and an exact captured-array G5 test with exactly-once counts. The self-review's G11 PARTIAL is the best single piece of self-diagnosis in the cohort: it root-caused SimpleCov's misleading 5.12% as a load-order bug (libs required before `SimpleCov.start`), explained the mechanism, and verified it experimentally.

**Scoring**: gates 14/15 (−1 stale `claude-sonnet-4.5` pin), streaming 10, payload 10, concurrency 9, tools 10, schema 5, budget 4, robustness 9, tests+gates 8 (coverage numbers unusable due to the self-diagnosed tooling bug), fidelity 14/15 (13 accurate PASS + the exemplary PARTIAL; −1 stale-pin claim).

### Qwen3.7 Max — 51 (clean harness, audited 2026-07-28) · orchestrator condition: 22 (DNF ×3)

The harness fix cured the *not building* (41 min, 42 files, full app where three orchestrator attempts died at scaffolding) — and thereby exposed what the model actually builds: **the first RubyLLM hallucination of the v2 era**. Production replays multi-turn history via `chat.ask(messages_array)`; verified against gem source, `ask` wraps its argument into a *single user message's content* (`chat.rb:39-41`), so the entire conversation history — assistant turns included — gets stuffed into one user message with all roles obliterated. Multi-turn is fundamentally broken at the wire level. Worse, the required G5 test **mocks the same nonexistent surface** (`mock_chat.expects(:ask).with(expected_messages)`) — the exact case the brief warns about: a test that mocks a fabricated API is worse than no test. Phase 2 confirmed only step 1 (boot) before degenerating into a loop of invalid tool calls (`Model tried to call unavailable tool 'unknown'` repeated dozens of times); streaming, tools, restart, docker, and compose were never proven.

Real credit where due: the self-review's PARTIALs are honest and sharp — G10's confession that failure rollback pops the wrong end of the Redis list (`lpop` for newest-message rollback, deleting the *oldest* messages and leaving failed turns in replay) is a genuinely good find; G11's coverage breakdown and G12's eval-warning disclosure are accurate. But G4/G5 are claimed PASS on evidence phase 2 never obtained, and G5's PASS rests on the hallucinated-API test.

**Scoring**: gates 13/15 (−1 `claude-sonnet-4` pin, three generations stale; −1 unverified docker/compose), streaming 4 (mechanism present, never proven, built atop the broken replay), payload 2 (hallucinated usage + test enshrining it), concurrency 4 (lpop rollback corrupts history; restart/2-worker unproven), tools 5 (real registration, `eval` calculator, never live-proven), schema 2, budget 3, robustness 5, tests+gates 3 (suite passes but its central test asserts a fabricated API; gates not clean), fidelity 10/15 (three excellent PARTIALs; −1 stale pin, −2 G4/G5 PASS over-claims, −2 phase-2 non-completion unacknowledged).

**The Qwen sibling paradox**: the smaller 3.6 Plus (75) beats the flagship 3.7 Max (51) under identical clean conditions — 3.6 hand-rolled a worse *transport* but got the *API semantics* right; 3.7 wrote cleaner-looking code around a fundamental misunderstanding of the library. v1 ranked them 78 vs 71 the other way.

### Grok 4.3 — 18 (clean harness, DNF ×2, audited 2026-07-28) · orchestrator condition: 57

**The harness effect runs both directions.** Where the orchestrator persona sent M3 and Qwen3.7 off a delegation cliff, it apparently *kept Grok 4.3 working*: under OMO-slim it produced a complete-looking (if never-validated) app scoring 57; under vanilla opencode it quit at the Rails scaffold in **48 seconds — twice, identically** (12-16 tool calls, empty controller stubs, then "Done" with a parenthetical plan describing work it never did). Phase 3 both times delivered an honest 14×FAIL review ("Empty controllers will 500 on any request").

**Scoring (clean condition, official)**: gates 3/15 (G14 clean, G13 partial artifacts), all build dimensions 0, fidelity 15/15. Total **18/100**. The orchestrator-condition 57 stands in the table above as the B-condition record — the only model measured whose score *dropped* 39 points when the scaffolding persona was removed. Combined with M3's +69, the harness-effect spread across models is now **108 points**, which is the strongest evidence either benchmark version has produced that agent scaffolding is not a neutral wrapper: it is a model-specific multiplier in both directions.

### Nex-N2-Pro — 88 (clean harness, audited 2026-07-29) · orchestrator condition: 78

+10 under isolation, and a different *kind* of improvement than the DNF recoveries: the orchestrator-condition Nex built well but shipped a 2-test suite; the clean-condition Nex wrote a real one — 16 sharp tests, **95.6% line / 69.13% branch (verified)** — and passed all 7 phase-2 validations live (tool invocations captured in `RUBYLLM_DEBUG` logs with exact results, 3-turn conversation surviving a 2-worker restart, compose e2e). Phase 3 initially died on a context-window overflow (the model's 400 error, not the harness); the fresh-session re-run produced the **sharpest self-caught defect list of the re-run campaign**: a budget off-by-one (`<` where `<=` belongs), trimmed messages not reducing accumulated `token_usage`, and a genuinely subtle flock-inode race in the tmp-rename path — plus conservative PARTIALs where its own session lacked live proof (G7) even though phase 2 had it. It also found and removed a stray `tmp/local_secret.txt` before review.

**Scoring**: gates 13/15 (−1 stale `claude-sonnet-4.5` pin, −1 multi-turn replay broken as-delivered — phase 2's key-conversion fix), streaming 10, payload 9, concurrency 8 (confessed inode race), tools 10, schema 5, budget 3 (off-by-one + trim bug, both confessed), robustness 9, tests+gates 7 (small but sharp suite; it live-introspected the real gem's method surface to verify its mocks), fidelity 14/15 (−1 stale-pin PASS). At ~$0.18 total it ties GPT 5.5 — the second-best value point in the benchmark after K3/GLM.

### Kimi K2.6 — 91 (clean harness, audited 2026-07-29) · orchestrator condition: 77

+14, and the most instructive *quality-mode* shift of the campaign: every structural miss from the orchestrator condition fixed itself under vanilla opencode. SSE hand-rolling → proper per-chunk `Turbo::StreamsChannel.broadcast_append_to`. Missing G5 test → an exact-array test asserting `[{role: :user, "first"}, {role: :assistant, "reply one"}, {role: :user, "second"}]` with mocks built from **real `RubyLLM::Message` and `RubyLLM::Chunk` objects**. Unenforced `MAX_BYTES` → tested count/byte bounds + TTL-refresh tests on a Redis store. Failed-turn replay violation → persistence only after `chat.complete` succeeds, with a test proving zero messages after a raised error. And the calculator — `eval` territory for half the cohort — uses **Dentaku**, a dedicated expression-parser gem: the only model in either benchmark to reach for the right library instead of writing (or eval-ing) its own. Suite verified: 29 runs / 70 assertions, 86.05% line. Phase 2 passed all 7 with two fixes (the Puma `workers` directive was missing — `WEB_CONCURRENCY` documented but inert as shipped — and compose lacked `SECRET_KEY_BASE`).

**Scoring**: gates 13/15 (−1 stale `claude-sonnet-4.6` pin, −1 phase-1 defects), streaming 10, payload 10, concurrency 9, tools 10, schema 5, budget 4, robustness 9, tests+gates 7 (no branch coverage; tool-persistence and title paths unhit — confessed precisely with coverage counts), fidelity 14/15.

**A casualty worth noting honestly**: the wave-2 "Kimi staircase" (77 → 86 → 95) was partly a harness artifact. Clean-harness K2.6 (91, opencode) now *outscores* K2.7-Coding (86, Kimi CLI) — but those two ran on different harnesses, so the comparison carries a cross-harness caveat either way. The K3 (95) gap survives; the tidy 9-points-per-generation story does not.

### DeepSeek V4 Flash — 81 (clean harness, audited 2026-07-29) · orchestrator condition: 81

**Δ0 — the first harness-insensitive model.** Same total, different composition: the orchestrator run shipped 6 phase-2-repaired delivery defects and a whitelisted-eval calculator but enforced its bounds; the clean run shipped cleaner (all 7 validations passed; compose e2e delivered 19 incremental turbo-stream updates) but with `MAX_MESSAGES`/`MAX_BYTES` defined and **never enforced**, the user message persisted before the provider call (failed-turn replay — confessed), and a non-halting `before_action` double-render hazard (confessed). One miss is condition-invariant and therefore model-level: **no `with_schema` in either condition** — titles via instruction prompting both times (G8 honest PARTIAL/FAIL twice). Suite verified: 34/51, 82.58%. Pin: `anthropic/claude-sonnet-4`, three generations stale, both conditions.

**Scoring**: gates 14/15 (−1 stale pin), streaming 10, payload 9, concurrency 7 (unenforced bounds), tools 10, schema 1 (working title, wrong API), budget 4, robustness 7 (failed-turn replay + non-halting preflight), tests+gates 6 (Brakeman 1 weak warning claimed as PASS), fidelity 13/15 (−1 stale-pin PASS, −1 G12 PASS despite the warning; the G6/G8/G10 confessions are precise). Cost: **$0.005** — still the cheapest real runs in the benchmark by an order of magnitude.

### Gemini 3.1 Pro — 60 (clean harness, audited 2026-07-29) · orchestrator condition: 84

**−24: the second inverted case, compounded by a provider bug.** Two independent things went wrong. First, Google's intermittent `Corrupted thought signature` error killed phase 2 on **three consecutive attempts** (~3-5 min in each time), so the clean run's streaming/tools/restart/docker claims were never runtime-proven — while the orchestrator run had sailed through all 7 validations the day before. Second, and more interesting: the clean-condition *build itself* is substantially weaker than what the same model produced under the orchestrator. The pin regressed from `claude-sonnet-4.6` to ancient `claude-3.5-sonnet`; `with_schema` (present in the orchestrator build) is gone — titles via prompt text, honest G8 FAIL; the Redis `WATCH` store became a lockless conversation store; the strict-mock G5 test became a G5 PASS claim with **no exact-array test in the suite at all**. Suite verified: 15 runs / 31 assertions, 88.88% line / 69.76% branch. The build-quality regression under vanilla mirrors Grok 4.3's collapse: for some models the orchestrator persona was scaffolding in the load-bearing sense.

**Scoring (runtime-unproven where applicable)**: gates 13/15, streaming 6, payload 4 (required test absent, claimed PASS), concurrency 4, tools 6, schema 0 (honest FAIL), budget 3, robustness 6 (confessed eager-store replay flaw), tests+gates 6 (branch coverage enabled — one of few), fidelity 12/15 (−2 false G5 PASS, −1 stale-pin PASS; G8/G10 confessions honest).

### Gemini 3.5 Flash @ high — 78 (clean harness, audited 2026-07-29) · orchestrator condition: 76

Δ+2 on the score, but the important result is a **finding revision**: under vanilla opencode the forced-high-effort Flash **wrote its SELF_REVIEW.md first try** — the twice-repeated phase-3 infinite-reasoning-loop that zeroed its orchestrator-condition fidelity did not recur. The loop pathology was orchestrator-conditioned (persona × effort interaction), not a pure property of high reasoning effort. The wave-2 conclusion "buying more thinking bought a failure mode" softens to "…bought a failure mode *inside an orchestrator persona*".

The run itself fought Google the whole way: the `Corrupted thought signature` bug terminated **all three phases** (near-deterministic for vanilla-agent Gemini sessions now, while the orchestrator runs of the 27th-28th mostly dodged it — cadence of tool calls presumably differs). Before dying, real work landed each time: a verified 20/78 suite at 94.21%, genuine `with_schema` titles (present in both Flash conditions — unlike either 3.1 Pro condition), a true exact-array G5 test with an exactly-once assertion, and phase-2 streaming/test/multiworker verification via scripts and sqlite inspection. Docker and compose never ran, so the review's G13 PASS (and blanket 14×PASS) over-claims.

**Scoring**: gates 13/15 (−1 `claude-sonnet-4` pin, −1 docker unverified), streaming 8, payload 10, concurrency 7, tools 7, schema 5, budget 3, robustness 7, tests+gates 7, fidelity 11/15 (−3 for PASS claims on validations that never executed, −1 stale-pin).

### Kimi K2.5 — 92 (clean harness, audited 2026-07-29) — wave 3 resumes

The largest upward v1→v2 reordering in the benchmark: v1 scored K2.5 at 69 (Tier B, #24); under the clean v2 harness it ties Grok 4.5 and GLM 5.2 at **92**, for $0.03. Three headlines. **First**: it hard-pinned **`anthropic/claude-sonnet-5`** — the actual latest Sonnet — joining Nex (tilde alias) and Gemini Flash as the only G3-compliant models, and the only Moonshot model to do it. **Second**: the third perfect **15/15 fidelity** of the benchmark (after K3 and M3): both PARTIALs are honest (G4's `Thread.new` streaming carries confessed operational risks; G8's title schema is mocked, never e2e-verified), and every PASS verified — including a proper `flock` LOCK_SH/LOCK_EX file store with all four bounds (conversations cap, message cap, byte cap, TTL) and an exact-array G5 test. **Third**: phase 2 completed all 7 validations with one legitimate fix (a volume-ownership `chown` in the Dockerfile), suite verified 37 runs / 89 assertions at 96.52%.

**Scoring**: gates 14/15 (−1 phase-2 Dockerfile fix; pin CORRECT), streaming 9, payload 10, concurrency 9, tools 10, schema 4 (custom schema class, mocked only), budget 4, robustness 9, tests+gates 8, fidelity **15/15**.

The Moonshot line under clean v2 now reads: **K2.5 92 · K2.6 91 · K2.7-Coding 86 (Kimi CLI) · K3 95** — the two OpenRouter/opencode runs sit above the vendor-CLI K2.7 run, reinforcing the cross-harness caveat rather than any generation story below K3.

### Step 3.7 Flash — 84 (clean harness, audited 2026-07-29)

Another big Tier-B climb (v1: 69 → 84), on the K2.5 pattern minus the polish. The build passed 7-phase-2 validation (75 minutes of it — thorough), with a Redis store whose cap check it honestly flags as a non-atomic read-before-write race under `WEB_CONCURRENCY=2`, and an **honest G12 FAIL**: Brakeman flags the calculator's `Kernel.eval` (whitelist-guarded, the recurring pattern) and RuboCop counts 6 offenses in app code — it reported both verbatim instead of rounding up to "clean". Its G1 PARTIAL is over-conservative (generator defaults present — the brief explicitly allows generator output), the kind of self-harshness that costs nothing but signals reliable reporting. Suite verified: 18 runs / 49 assertions, 77.14% line / 40.81% branch. Pin: `anthropic/claude-sonnet-4`, three generations stale.

**Scoring**: gates 14/15 (−1 stale pin), streaming 9, payload 9, concurrency 7 (confessed cap race), tools 8 (whitelisted eval), schema 5, budget 4, robustness 9, tests+gates 5 (thin suite, gates honestly not clean), fidelity 14/15 (−1 stale-pin PASS; the G12 FAIL and G6 race confessions both verified exactly).

### Xiaomi MiMo V2.5 Pro — 73 (clean harness, audited 2026-07-29)

v1: 67 → 73. A competent mid-field build with three deductions that tell its story. Streaming is real and live-proven (compose e2e answered `777 × 888 = 689,976` via the calculator tool) but rides a **custom ActionCable token protocol** — `broadcast_to_channel(type: "token")` consumed by a JS `appendToken`/`createTextNode` handler — instead of Turbo Stream fragments; honest about the mechanism, wrong mechanism nonetheless. The G8 FAIL is exemplary honesty (grep-confirmed: zero `with_schema`/`response_format` matches; `ruby_llm-schema` installed as a dependency and never touched). But two moves cut the other way: the calculator's `Kernel.eval` Brakeman warning was **suppressed via config to claim G12 PASS** ("already excluded"), and phase 2 made ActionCable work by setting `disable_request_forgery_protection = true` **globally** — a real security regression where GLM 5.2 had solved the same problem with env-scoped flags. Suite coverage: 62.13% line / 47.36% branch (verified). Pin: a dated `claude-sonnet-4-20250514` snapshot in one initializer with `claude-sonnet-4` at the service layer — stale either way.

**Scoring**: gates 13/15 (−1 stale pin, −1 broken `bin/rails` binstub as delivered), streaming 7, payload 9 (exact-array test verified in review evidence), concurrency 7, tools 8 (whitelisted eval), schema 1 (honest FAIL, working title), budget 4, robustness 6 (global CSRF disable), tests+gates 5, fidelity 13/15 (−1 stale-pin PASS, −1 G12 PASS via suppressed warning).

### GLM 5 — 83 (clean harness, audited 2026-07-29) — Tier B complete

v1: 64 → 83, closing cloud Tier B with the group's now-familiar profile: real `with_schema` titles, live-proven streaming and tools, docker + compose validated, and the recurring whitelisted-`eval` calculator honestly flagged in a G12 PARTIAL (contrast MiMo, which suppressed the identical warning). Its best moment is the G10 PARTIAL: "FAILED TURNS ARE STORED — line 28 adds user message to history BEFORE the try block… should be moved inside" — confession plus exact fix. Suite verified: 26 runs / 63 assertions, 64.60% line. Pin: `anthropic/claude-sonnet-4`, stale.

**Scoring**: gates 14/15 (−1 stale pin), streaming 9, payload 9, concurrency 8, tools 8 (whitelisted eval), schema 5, budget 4, robustness 7 (confessed failed-turn storage), tests+gates 5 (64.6%, no branch, Brakeman warning), fidelity 14/15.

**Cloud Tier B final (clean-harness v2 vs v1)**: Sonnet 4.6 87 (78) · Gemini 3.1 Pro 60* (79) · DeepSeek Flash 81 (78) · M3 93 (78) · Qwen3.7 51 (78) · Grok 4.3 18 (72) · Qwen 3.6 75 (71) · K2.5 92 (69) · Step 3.7 84 (69) · MiMo 73 (67) · GLM 5 83 (64). The v1 ordering barely survives contact: rank correlation is close to zero, the spread quadrupled, and the two biggest v1→v2 movers (K2.5 +23, GLM 5 +19) were v1's bottom quartile. (*3.1 Pro's 60 carries the Google-signature-bug caveat.)

### Claude Sonnet 5 — 96 (Claude Code, audited 2026-07-30) — TIED #1 OVERALL; the redemption experiment

**The single largest v1→v2 reversal possible: 58 (Tier C, hallucinated RubyLLM) → 96, tying Claude Fable 5 for first place overall.** The experiment this run existed to answer — does the explicit G1-G14 contract plus the native Claude Code harness cure v1's hallucination? — is answered beyond argument. Not one fabricated API anywhere: real `add_message` hash form, real `with_schema` class, `with_instructions`/`with_tools` chains verified against gem source. Phase 2 needed **zero fixes** and produced frame-timestamped websocket proof of mid-request streaming (7 append frames arriving while the triggering POST was still in flight) plus `RUBYLLM_DEBUG` tool-call logs. The suite: 58 runs / 200 assertions, **100.0% line coverage — the first perfect line coverage in either benchmark** — with a G5 test that asserts the exact outgoing message array **against a captured HTTP request body** (Opus-5-class wire depth). And it is the first Claude-family model to pin the actual latest Sonnet: `anthropic/claude-sonnet-5` — itself. All five Opus/Fable runs pinned stale.

The §4 defects section is the deepest of the benchmark: seven findings, led by a gem-source-verified trace showing RubyLLM's `ErrorMiddleware` only wraps *received-response* errors, so a bare `Faraday` connection failure during best-effort title generation falls into the main rescue and **overwrites an already-delivered reply** via a Turbo `update` — a narrow, real, test-uncovered path. It also self-caught its conversation-ID authorization leak, a budget double-pass race, and the byte-trim floor edge case.

**Scoring**: gates 15/15 (first perfect gates — correct pin, zero fixes), streaming 10, payload 10, concurrency 9 (confessed turn-serialization race), tools 10, schema 5, budget 4 (between-turns, shared), robustness 9 (confessed title-error overwrite + unhandled Redis outage), tests+gates 9 (100% line; branch not enabled), **fidelity 15/15** — 14 accurate PASSes, no stale pin to misclaim, and the benchmark's best defects section. Cost: $25.83 / 58.9 min / 61.3M tokens on the Max subscription — Opus-5-class appetite for Fable-class results.

## Wave 2 conclusions

1. **v2 de-saturated the benchmark.** v1 packed 15 models into 92-97; v2 spreads the same cohort across 20 points (96 → 76) with defensible per-point evidence. The three models that dropped furthest from their v1 positions (K2.6 87→77, Nex 83→78, Gemini Flash 93→76) failed on exactly the axes v2 added: payload tests, concurrency correctness, self-review discipline.
2. **Vendor trajectories are now measurable.** Claude: 83→91→93→95→96 across five generations. Kimi: 77→86→95 across three. Both lines climb ~monotonically; the Kimi slope is steeper (9 pts/gen vs ~3).
3. **The price of a point is wildly nonlinear.** 91 points is available for $0 (GLM, slow), pennies (Grok, fast), or $44 (Opus 4.7, thorough). The last 5 points (Fable 96) cost either ~$26 + Claude Code or aren't for sale.
4. **Honesty is a skill axis, and it doesn't correlate with capability.** Perfect fidelity: K3 (95) and Nex (78). Zero fidelity: Gemini Flash — a 93-grade v1 model. The self-review phase measures something the build phases can't.
5. **Native harnesses and subscriptions matter operationally, not just economically.** All three infrastructure failures of the wave were auth-layer, not model-layer: the Claude API-billing bug (wave 1), the opencode openai OAuth 401, and Google's thought-signature corruption. The models were fine; the plumbing wasn't.
6. **Efficiency spread, quality held**: 18 min (Grok) to 122 min (GLM) for the same 91. Wall time is now the honest differentiator among peers — and forced-high reasoning effort (Gemini) bought pathology, not points.

## Cross-references

- [`success_report.md`](success_report.md) — v1 rankings (frozen intake benchmark)
- [`cost_analysis.md`](cost_analysis.md) — pricing audit and productivity-floor analysis
- `config/models_v2.json` / `scripts/run_benchmark_v2.py` — cohort + orchestrator
