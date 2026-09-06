# v3 Benchmark — Ecosystem Report (2026-09-06)

> **⚠️ v3 is the documented WRONG TURN, kept for the history.** Over-optimizing for
> *de-saturation* led v3 into abstract, synthetic, stdlib-only micro-tasks — the farthest
> thing from grounded reality. It ranks models (and yielded a useful ecosystem cost/speed
> map, below), but it is **not** how real software is built, so it saturates on quality and
> measures the wrong thing. The realistic successor is **v4** (`benchmark-v4/`): one
> cohesive, evolving Rails project with malicious-teammate sabotage — see
> `benchmark-v4/README.md`. Read v3 as the cautionary lesson: chasing a score spread for
> its own sake produces unrealistic benchmarks.

Hidden-graded, objective, contamination-shielded coding benchmark. Companion to the v2
report (`docs/success_report.v2.md`). This report captures the v3 design, the
de-saturation investigation, the frozen suite, and the full ecosystem sweep.

## TL;DR

- **v3 suite (frozen):** task 17 (marketplace app-simulation, 5 feature areas / ~145
  hidden checks) + task 18 (dependency resolver, observation-heavy). Both fully
  deterministic. Grading is objective (hidden runners), so no rubric drift.
- **Baseline:** Claude Opus 4.6 = index 100 (frozen in `benchmark-v3/baseline.json` with
  per-task manifest hashes; `scripts/v3_freeze_baseline.py --verify` detects drift).
- **Headline finding:** frontier models are at **quality parity** on grounded,
  well-scoped coding. 24 of 37 models scored **95–100** across every major lab. The real
  differentiators are **cost and speed** (up to 8× cost / 5× time at equal quality), and
  quality only diverges among **weaker / smaller / older** models.

## Why v3, and the de-saturation investigation

v2 (build a Rails+RubyLLM app, 10-dim rubric) showed a wide score range — but that range
came from **(a)** a wide cohort (local 7B → frontier), **(b)** an unfamiliar-library
knowledge axis (RubyLLM API hallucination = Tier 1/2/3 cliffs), and **(c)** subjective
rubric + completeness variance. v3 removed all three (near-peer frontier, pure-logic
stdlib, exact grading) and the frontier collapsed to parity.

Every de-saturation lever was tried and measured (Fable 5.1 / Opus 4.6 / GPT-6 Astra):

| approach | frontier quality spread |
|---|---|
| continuous scoring / no-hints / latent defects / single-issue | 0 |
| repository-scale (6-module order service, task 16) | 3.4 |
| app simulation (5-feature marketplace, task 17) | 5.0 → 4.8 sharpened |
| observation-heavy, grounded (dependency resolver, task 18) | 0.0 (all wrote correct backtracking) |

**The crux:** you cannot have BOTH "grounded in day-to-day reality" AND a large frontier
quality spread. Anything day-to-day is well-represented in training, so the frontier has
mastered it → it saturates. A quality gap only appears on (a) novel contest puzzles
(ungrounded gotchas) or (b) long-horizon, ambiguous, 10–30-file real-world work
(SWE-bench-Pro scale — huge, hard to grade objectively). The honest, large, comparable
signal is **cost/speed**.

Integrity: each run is isolated (shield moves the grading key + sibling results + all
task hidden/reference out of the tree; `GIT_CEILING_DIRECTORIES` blocks git-history
score leaks). Graders are hermetic (fresh imports per check; per-run temp dirs — no /tmp
pollution) and deterministic (audited via `scripts/v3_audit_tasks.py`, 0.0 spread / 3
runs).

## Ecosystem sweep — QUALITY ranking (37 models, tasks 17+18)

| # | model | quality | cost $ | time s |
|---|-------|---------|--------|--------|
| 1 | GPT-6 Astra (High) | 100.0 | 3.13 | 910 |
| 2 | Claude Fable 5.1 | 99.7 | 3.60 | 1075 |
| 3 | Claude Opus 5 | 99.7 | 5.55 | 1235 |
| 4 | Gemini 3.7 Flash @high | 99.7 | 1.15 | 432 |
| 5 | Gemini 3.8 Flash @high | 99.7 | 2.15 | 837 |
| 6 | GPT 5.5 (xHigh) | 99.7 | 5.29 | 1449 |
| 7 | GPT 5.6 Luna (xHigh) | 99.7 | 0.72 | 1002 |
| 8 | GPT 5.6 Sol (xHigh) | 99.7 | 4.27 | 1348 |
| 9 | GPT 5.6 Terra (xHigh) | 99.7 | 1.47 | 1020 |
| 10 | Kimi K3 | 99.7 | 1.30 | 959 |
| 11 | Muse Spark 1.3 | 99.7 | 1.00 | 1218 |
| 12 | Kimi K2.7 Coding | 99.3 | 0.53 | 1602 |
| 13 | Claude Opus 4.8 | 99.0 | 2.25 | 532 |
| 14 | Claude Sonnet 5 | 99.0 | 0.93 | 426 |
| 15 | DeepSeek V4 Pro 0813 | 99.0 | 1.08 | 2219 |
| 16 | Grok 4.6 (opencode) | 99.0 | 1.25 | 722 |
| 17 | Grok 4.6 (grok CLI) | 99.0 | — | 2015 |
| 18 | Claude Fable 5 | 98.3 | 5.62 | 636 |
| 19 | MiniMax M3 | 98.3 | 1.03 | 1742 |
| 20 | Grok 4.5 (opencode) | 98.0 | 0.83 | 476 |
| 21 | Claude Opus 4.6 (baseline) | 97.6 | 1.56 | 466 |
| 22 | DeepSeek V4 Pro | 96.2 | 0.29 | 958 |
| 23 | Claude Sonnet 4.6 | 95.5 | 1.23 | 589 |
| 24 | Gemini 3.1 Pro | 95.5 | 1.16 | 400 |
| 25 | Qwen 3.7 Max | 94.2 | 0.98 | 1029 |
| 26 | Kimi K2.6 | 93.8 | 1.41 | 729 |
| 27 | Step 3.7 Flash | 93.5 | 0.12 | 310 |
| 28 | Devstral 2512 | 93.1 | 0.24 | 305 |
| 29 | Xiaomi MiMo V2.5 Pro | 91.7 | 0.04 | 572 |
| 30 | NVIDIA Nemotron 3 Super 120B | 91.7 | 0.05 | 2242 |
| 31 | DeepSeek V4 Flash | 90.3 | 0.05 | 476 |
| 32 | DeepSeek V4 Flash 0731 | 63.8 | 0.01 | 371 |
| 33 | GLM 5.3 Flash | 63.8 | 0.02 | 2365 |
| 34 | GPT-OSS 120B | 63.8 | 0.00* | 76 |
| 35 | Mistral Large 3 | 55.0 | 0.07 | 127 |
| 36 | Llama 4 Maverick | 31.2 | 0.00* | 46 |
| 37 | Codestral 2508 | 15.8 | 0.01 | 19 |

\* near-zero / unmetered cost — these are fast FAILURES, not efficiency; excluded from the value table.

**Quality tiers:** Frontier (95–100): 24 models, indistinguishable on quality, spanning
Anthropic, OpenAI, Google, Moonshot, DeepSeek, xAI, MiniMax. Strong (90–95): Qwen 3.7
Max, Kimi K2.6, Step 3.7 Flash, Devstral, MiMo, Nemotron, DeepSeek Flash. Weak (the real
divergence): DeepSeek Flash 0731 / GLM 5.3 Flash / gpt-oss 120B (63.8), Mistral Large 3
(55), Llama 4 Maverick (31), Codestral (16).

## FRONTIER VALUE (quality ≥ 95 — cost/speed is the differentiator here)

Value = 50% cost-efficiency + 50% speed, relative to the cheapest/fastest in the band.

| # | model | quality | cost $ | time s | q/$ | q/min | value |
|---|-------|---------|--------|--------|-----|-------|-------|
| 1 | DeepSeek V4 Pro | 96.2 | 0.29 | 958 | 329 | 6.0 | 70.9 |
| 2 | Claude Sonnet 5 | 99.0 | 0.93 | 426 | 107 | 13.9 | 62.7 |
| 3 | Gemini 3.1 Pro | 95.5 | 1.16 | 400 | 82 | 14.3 | 62.6 |
| 4 | Grok 4.5 | 98.0 | 0.83 | 476 | 118 | 12.4 | 59.6 |
| 5 | Gemini 3.7 Flash @high | 99.7 | 1.15 | 432 | 86 | 13.8 | 59.0 |
| 6 | Claude Opus 4.6 | 97.6 | 1.56 | 466 | 63 | 12.6 | 52.3 |
| 7 | Claude Sonnet 4.6 | 95.5 | 1.23 | 589 | 77 | 9.7 | 45.8 |
| 8 | Claude Opus 4.8 | 99.0 | 2.25 | 532 | 44 | 11.2 | 44.1 |
| 9 | GPT 5.6 Luna | 99.7 | 0.72 | 1002 | 138 | 6.0 | 40.3 |
| 10 | Kimi K2.7 Coding | 99.3 | 0.53 | 1602 | 187 | 3.7 | 40.1 |

(Full 23-row band in `scripts/v3_ecosystem_report.py` output.)

## Notable findings

- **Cost/speed spread at equal quality is enormous.** GPT 5.6 Luna delivers 99.7 for
  **$0.72**; Opus 5 and Fable 5 cost **$5.55–5.62** for the same tier — an ~8× range.
  Sonnet 5 (426s) is ~5× faster than DeepSeek Pro 0813 (2219s) at similar quality.
- **Newest-vs-previous within a family is ~flat on quality, differing mostly in cost/speed.**
  Opus 5 (99.7) / 4.8 (99.0) / 4.6 (97.6); GPT 5.6 all three variants + 5.5 all 99.7;
  Kimi K3 99.7 / K2.7 99.3 (K2.6 dips to 93.8). Generational "improvement" on grounded
  coding is now largely an efficiency story, not a capability one.
- **Mistral is weak** (user-predicted): Codestral 15.8 (worst overall), Mistral Large 3
  55.0; only the coding-specialized Devstral (93.1) is competitive.
- **Llama 4 Maverick (31.2)** confirms Meta's frontier-coding lag.
- **"Flash" / small models fall off the multi-file app:** DeepSeek Flash 0731 and GLM 5.3
  Flash and gpt-oss 120B all land at 63.8 — they handle the resolver but not the
  5-feature app at depth.
- **Best value overall:** DeepSeek V4 Pro (96.2 quality, $0.29, 958s) and Claude Sonnet 5
  (99.0, $0.93, 426s) dominate the value frontier.

## Failed / needs retry (infra, not capability)

GLM 5.3, GLM 5.2 (Z.ai endpoint), Qwen 3.8 Max, Qwen 3.8 Flash (OpenRouter), Tencent
Hunyuan A13B, local Qwen 3.8 27B (5090 server down). These are infrastructure failures,
not model results — to be retried. A true-local 5090 session (gpt-oss / Devstral / newest
Qwen served locally) is a separate manual task.

## Reproduce

- `python3 scripts/v3_ecosystem_report.py --tasks 17,18` — the tables above.
- `python3 scripts/run_v3.py --model <slug> --tasks 17,18` — score one model.
- `python3 scripts/v3_audit_tasks.py --tasks 17,18` — determinism/hermeticity gate.
- `python3 scripts/v3_freeze_baseline.py --verify` — confirm the frozen suite hasn't drifted.
