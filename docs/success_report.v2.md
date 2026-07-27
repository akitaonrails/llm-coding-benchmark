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
| 9 | **Claude Opus 4.6** | **83** | **39.5 min** | 16.8M | $12.83 | Max sub |

Queue: K2.7-Coding (running) → GLM 5.2 → K2.6 → Grok 4.5 → Nex-N2-Pro → Gemini 3.5 Flash @ high effort (Pro-slot fallback; Pro still allowlist-only via Antigravity/Vertex).

**The Claude generation gradient is now fully resolved**: 4.6 (83) → 4.7 (91) → 4.8 (93) → Opus 5 (95) → Fable (96). v1 had all five inside Tier A noise; the v2 brief spreads them across 13 points.

### Claude Opus 4.7 — 91 (audited 2026-07-27)

The fastest Claude run yet (43.7 min) and the *hungriest* model in the cohort (67.7M tokens — 4.6× Fable's 14.6M for the same brief). All 7 phase-2 validations passed live with the strongest streaming proof so far: 125 turbo-stream chunks over 9.3s via `ActionController::Live` (a third streaming mechanism after broadcasts and SSE variants). Exemplary G5 tests assert the exact wire array against a `FakeChat` that mirrors the real gem's `ROLES`. SQLite WAL persistence (the Opus 4.8 / GPT 5.5 family), live restart-survival proof under `puma -w 2`. Suite: 44 tests / 81 assertions / 97.13% line — auditor-run numbers match the self-review to the decimal. Self-review: 13 PASS + honest G11 PARTIAL, with the frankest defects section of the cohort (byte/4 budget heuristic, unguarded `enforce_bounds` cross-process race, tool-call turns not persisted).

**Scoring**: gates 12/15 (stale `claude-sonnet-4.5` pin −1 shared; **−2 for a phase-2 secrets violation** — the model ran `docker compose config` while debugging a port collision, printing the resolved `OPENROUTER_API_KEY` into its own transcript, directly against the brief's "never print secret values"), streaming 10, payload 10, concurrency 9 (confessed bounds race), tools 10 (live-proven, eval-free shunting-yard), schema 5 (`ruby_llm-schema` 0.4.0 is a real transitive dep of ruby_llm 1.16.0), budget 4 (between-turns, shared), robustness 9, tests+gates 8 (Chat-seam mocks, no branch coverage, streaming transport untested end-to-end — self-admitted), fidelity 14/15 (−1 stale-pin PASS claim; **credit**: it confessed the key leak unprompted and recommended rotation — K3-grade honesty about a failure nobody was likely to check).

**Security note**: the leaked key lives only in the gitignored local `phase2.ndjson` (verified never committed) and the phase-2 API transcript. Key rotation recommended regardless. Without the incident this run scores 93 — dead even with Opus 4.8 at a 2.6× higher token bill.

### Claude Opus 4.6 — 83 (audited 2026-07-27)

The fastest (39.5 min) and second-cheapest ($12.83) run in the cohort — and the first where **phase 1 delivered a non-viable build**: a non-registry model pin (`anthropic/claude-sonnet-4-20250514`, would fail on the first call) and Dockerfile/BUNDLE_WITHOUT issues; phase 2 applied 5 fixes before its 7 validations passed (every other model so far shipped a working phase-1 build; 4.7 needed zero fixes). One of those "fixes" was itself wrong: it declared `ruby-4.0.6` "non-existent" and downgraded to 3.4.10 — mise on this machine has 4.0.6 installed as `latest`, and 4.7's project runs on it. Once repaired, the app is genuinely solid: correct drop-last exactly-once replay with a real captured-array G5 test, live-proven streaming/tools/restart-survival, SQLite WAL, real `with_schema` titles, and two cohort-firsts — **branch coverage enabled** (64.63%, honestly reported) and a **real CI workflow** enforcing the quality gates.

**Scoring**: gates 12/15 (−1 stale pin, −1 phase-1 non-viable artifacts, −1 needless Ruby downgrade off G1's "newest"), streaming 9, payload 9 (drop-last relies on the just-inserted row being last — fragile under concurrent appends), concurrency 8 (TTL is dead code — `cleanup_expired!` has zero production callers, confessed; shared-SQLite-connection thread hazard, confessed), tools 10, schema 5, budget 3 (between-turns shared −1; confessed token double-counting — heuristic estimate ADDED to real API counts — inflates usage and trips the budget early), robustness 9, tests+gates 8 (51 runs/106 asserts verified; OpenStruct-seam mocks are the shallowest in the Claude line), **fidelity 10/15** — the biggest deduction of the cohort: the SELF_REVIEW goal table **renumbered G1-G14 from memory** instead of re-reading the brief (its "G3" is an invented "SPA" goal; the brief's G5 payload, G6 bounds/TTL, G8 schema, and G9 budget have no explicit verdict rows), it justified a G1 PASS with an invented "Rubric accepts 3.4.x" after its own false-premise downgrade, and it cites `ruby_llm-1.14.1` source paths while 1.16.0 is installed. Credit where due: every §4 defect it confessed (double-counting, TTL dead code, thread safety) checked out true.

## Cross-references

- [`success_report.md`](success_report.md) — v1 rankings (frozen intake benchmark)
- [`cost_analysis.md`](cost_analysis.md) — pricing audit and productivity-floor analysis
- `config/models_v2.json` / `scripts/run_benchmark_v2.py` — cohort + orchestrator
