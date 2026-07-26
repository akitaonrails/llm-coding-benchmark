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

## Wave 1 results

*(pending — filled per run as they complete: goal-gate table, efficiency table, self-review fidelity analysis, per-model sections)*

## Cross-references

- [`success_report.md`](success_report.md) — v1 rankings (frozen intake benchmark)
- [`cost_analysis.md`](cost_analysis.md) — pricing audit and productivity-floor analysis
- `config/models_v2.json` / `scripts/run_benchmark_v2.py` — cohort + orchestrator
