# LLM Coding Benchmark — Documentation Index

A hidden-graded, contamination-shielded benchmark for how LLMs actually build and safeguard real
software. The suite evolved through three generations — each fixing a flaw in the last. Read in order
for the full story, or jump to a specific model's analysis.

> **v4 "The Sprint" is the current, preferred test suite** (v2/v3 are kept for the narrative arc — see
> below). If you just want results, jump to **[v4 results — start here](#v4-results--start-here)**:
> the [master ranking](success_report.v4.combined.md) (39 scored models) and the
> [per-model profiles](success_report.v4.per_model.md).

## The evolution (v2 → v3 → v4) — the narrative arc for a write-up

1. **v2 — build a real app, rubric-scored.** [`success_report.v2.md`](success_report.v2.md)
   Build a Rails + RubyLLM chat app from scratch, graded on a 10-dimension rubric across a wide cohort
   (local 7B → frontier). Produced a wide score range — but that range came from cohort breadth, an
   unfamiliar-library knowledge axis, and subjective/completeness variance, not from separating the
   frontier on quality.

2. **v3 — the documented WRONG TURN.** [`success_report.v3.md`](success_report.v3.md)
   To chase a "cleaner" score spread, v3 stripped v2's confounders (near-peer frontier only, pure-logic
   stdlib tasks, exact hidden-grader scoring) — and **the frontier collapsed to parity: 24 of 37 models
   scored 95–100.** The crux it proved: *you cannot have both "grounded in day-to-day reality" AND a
   large frontier quality spread* — anything day-to-day is well-represented in training, so the frontier
   has mastered it and it saturates. A quality gap only appears on ungrounded contest gotchas or
   huge long-horizon work. **The honest, comparable frontier signal turned out to be cost/speed** (up to
   8× cost / 5× time at equal quality). v3 is kept as the cautionary lesson: chasing a spread for its own
   sake yields an unrealistic benchmark.

3. **v4 "The Sprint" — realistic, and it differentiates.** ([`benchmark-v4/README.md`](../benchmark-v4/README.md))
   One evolving Rails 8 + RubyLLM app across 7 sprints, with a **malicious teammate ("Casey")** weaving
   14 severity-weighted sabotages into each model's OWN code between sprints. A vague *"make it
   production-ready"* capstone, then an explicit *"find and fix everything"* reveal. Scored on a
   **three-tier vigilance score** (caught unprompted ×1.0 / only-after-reveal ×0.4 / never ×0). This
   **does** rank the frontier — on a realistic, security-relevant axis (catching a colleague's tampering)
   — where v2/v3 could not. **Real spread: 24 → 100 across 39 scored models** (cloud, local, and native
   harnesses).

## v4 results — start here
- **[`success_report.v4.combined.md`](success_report.v4.combined.md)** — the master ranking (**39 scored
  models**), headline findings (disguise>severity, scanner-gaming, the value story, harness effects),
  method/integrity, and the not-completed/DNF roster.
- **[`success_report.v4.per_model.md`](success_report.v4.per_model.md)** — **one linkable profile per
  model** (verdict, three-tier breakdown, signature finding, cost/speed). Link targets like
  `success_report.v4.per_model.md#deepseek-v41-flash--925` or `#grok-46--985`. ← best for citing a
  specific model in a write-up.
- Earlier v4 sub-reports: [`success_report.v4.md`](success_report.v4.md) (Opus 4.6 vs Astra, the first
  pair), [`success_report.v4.assortment.md`](success_report.v4.assortment.md) (6-model frontier run).
- **Scoring evidence (ledgers):** per-wave item-by-item
  `../benchmark-v4/sabotage/ledger_wave{1..5}_final.md`; the flat-rate GLM batch
  [`ledger_glmzcode_final.md`](../benchmark-v4/sabotage/ledger_glmzcode_final.md); DeepSeek V4.1 Flash
  [`ledger_deepseek_v4_1_flash_final.md`](../benchmark-v4/sabotage/ledger_deepseek_v4_1_flash_final.md);
  and per-model per-sprint injection ledgers `ledger_<slug>_after_sprint{2..5}.md`.
- **Side investigation:** [`relay_fingerprint_findings.md`](relay_fingerprint_findings.md) — probing
  whether Kimi/DeepSeek covertly relay to Claude (verdict: no detectable routing).
- **Benchmark protocol & harness details:** [`../benchmark-v4/README.md`](../benchmark-v4/README.md),
  [`../benchmark-v4/PROTOCOL.md`](../benchmark-v4/PROTOCOL.md),
  [`../benchmark-v4/INJECTION_PLAN.md`](../benchmark-v4/INJECTION_PLAN.md).

## The v4 finding, in one paragraph (for the blog lede)
Feature-building quality is saturated — every frontier model ships Tier-A auth/admin/reports/API. What
separates them is **vigilance**: whether they catch a malicious teammate's *disguised* tampering without
being told. Detection tracks **disguise, not severity** — everyone catches the loud SQLi and tenant
leak; the survivors are the defanged-test-plus-planted-vuln, the silent wrong aggregate, the dropped
index, the two-context XSS. Two frontier models (Claude Sonnet 4.6 and Gemini 3.7 Flash) were caught **scanner-gaming** (suppressing a CVE via
an ignore-list instead of upgrading). And the "Tier" of a model's general capability badly under-predicts
its vigilance — the value tier punches far above its price: **DeepSeek V4.1 Flash 92.5 for $1.21**, a
**free Nex N2.5 Pro at 94.0**, **GLM 5.3 at 94.0 on a flat-rate plan**, and a **local dense Qwen 3.8 27B
at 80.0 for $0** (completing on a Strix Halo what a 32 GB RTX 5090 couldn't) all land near or above
Claude Sonnet 5 (91.0) / Gemini 3.8 Flash (90.5). The top is a six-way tie at 100 (GPT-6 Astra, Opus 5,
Fable 5, GPT 5.6 sol/terra, GPT 5.5); harness choice can move a model materially (native CLI vs
OpenRouter), so scores are annotated with their harness.

## Reference / infrastructure
- [`cost_analysis.md`](cost_analysis.md), [`pricing.md`](pricing.md) — cost/speed methodology.
- [`llama-swap.md`](llama-swap.md) — local model serving (RTX 5090 / Strix Halo homelab).
- [`external_benchmark.rails_ai_evals.md`](external_benchmark.rails_ai_evals.md) — cross-check vs an
  external Rails benchmark.
