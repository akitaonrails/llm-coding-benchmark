# LLM Coding Benchmark — Documentation Index

A hidden-graded, contamination-shielded benchmark for how LLMs actually build and safeguard real
software. The suite evolved through three generations — each fixing a flaw in the last. Read in order
for the full story, or jump to a specific model's analysis.

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
   — where v2/v3 could not. **Real spread: 39 → 100 across 30 models.**

## v4 results — start here
- **[`success_report.v4.combined.md`](success_report.v4.combined.md)** — the master ranking (30 models),
  headline findings (disguise>severity, scanner-gaming, the value story), method/integrity.
- **[`success_report.v4.per_model.md`](success_report.v4.per_model.md)** — **one linkable profile per
  model** (verdict, three-tier breakdown, signature finding, cost/speed). Link targets like
  `success_report.v4.per_model.md#deepseek-v4-flash`. ← best for citing a specific model.
- Earlier v4 sub-reports: [`success_report.v4.md`](success_report.v4.md) (Opus 4.6 vs Astra, the first
  pair), [`success_report.v4.assortment.md`](success_report.v4.assortment.md) (6-model frontier run).
- Per-wave item-by-item ledgers (the scoring evidence): `../benchmark-v4/sabotage/ledger_wave{1..5}_final.md`.

## The v4 finding, in one paragraph (for the blog lede)
Feature-building quality is saturated — every frontier model ships Tier-A auth/admin/reports/API. What
separates them is **vigilance**: whether they catch a malicious teammate's *disguised* tampering without
being told. Detection tracks **disguise, not severity** — everyone catches the loud SQLi and tenant
leak; the survivors are the defanged-test-plus-planted-vuln, the silent wrong aggregate, the dropped
index, the two-context XSS. Three frontier models were caught **scanner-gaming** (suppressing a CVE via
an ignore-list instead of upgrading). And the "Tier" of a model's general capability badly under-predicts
its vigilance — a $0.97 DeepSeek Flash and a $1.03 Xiaomi MiMo out-scored most flagships.

## Reference / infrastructure
- [`cost_analysis.md`](cost_analysis.md), [`pricing.md`](pricing.md) — cost/speed methodology.
- [`llama-swap.md`](llama-swap.md) — local model serving (RTX 5090 / Strix Halo homelab).
- [`external_benchmark.rails_ai_evals.md`](external_benchmark.rails_ai_evals.md) — cross-check vs an
  external Rails benchmark.
