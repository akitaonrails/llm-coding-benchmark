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

## Cross-references

- [`success_report.md`](success_report.md) — v1 rankings (frozen intake benchmark)
- [`cost_analysis.md`](cost_analysis.md) — pricing audit and productivity-floor analysis
- `config/models_v2.json` / `scripts/run_benchmark_v2.py` — cohort + orchestrator
