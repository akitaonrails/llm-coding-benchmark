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
| **Gemini 3.1 Pro** (79/B) | **84** | 26.5 min | ~$0.16³ | Beats Opus 4.6 (83, v1 Tier A) |

### Gemini 3.1 Pro — 84 (audited 2026-07-28)

The first wave-3 datapoint lands *above* a wave-2 Tier-A Claude: 84 vs Opus 4.6's 83, at a quarter of the cost and 33% less time. The build: Redis store with `watch`-based optimistic concurrency + bounds + TTL (confessed hazard: infinite `retry` without backoff), valid `with_schema` hash-form titles, strict-mock G5 test (Minitest::Mock expectations enforce exactly-once replay with exact kwargs), suite verified 9 runs / 23 assertions / 88.61% line (matches self-report). Phase 2 passed all 7 validations but had to **fix phase-1's streaming implementation** — the delivered code didn't stream correctly through `ruby_llm`'s block-based `ask` until repaired — and remapped compose ports around host conflicts. Its 3.5-generation sibling's phase-3 pathology did not recur: at default dynamic effort, the self-review was produced first-try, correct G1-G14 numbering, honest G11 PARTIAL (error paths untested — verified true: missing-key, budget, and rescue branches have no tests).

**Scoring**: gates 13/15 (−1 stale `claude-sonnet-4.6` pin, −1 phase-1 streaming defect), streaming 8, payload 9, concurrency 8, tools 10, schema 5, budget 3, robustness 9, tests+gates 5 (9 tests is thin; no branch coverage), fidelity 14/15.

**Early wave-3 signal**: the v1 Tier-A/B boundary does not survive v2. Gemini 3.1 Pro (v1: 79) outscores Opus 4.6 (v1: 83) and sits within 2 points of K2.7-Coding (v1: 86) — v1's compressed top was hiding real reordering.

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
