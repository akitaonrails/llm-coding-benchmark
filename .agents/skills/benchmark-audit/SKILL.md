---
name: benchmark-audit
description: >
  Automatically evaluates an LLM coding benchmark result using a standardized
  0-100 rubric across 8 dimensions. Use when a benchmark finishes, when the user
  asks to evaluate a model, analyze a run's quality, or generate a score for a
  result. Also activates for 'score', 'evaluate benchmark', 'audit model', or
  'analyze result'.
compatibility: Requires Python 3.10+ and access to the project's filesystem.
metadata:
  author: llm-coding-benchmark
  version: "1.0"
---

# Benchmark Audit Skill

Evaluates a model's benchmark output using a 0-100 rubric across 8 dimensions.

**Reference material:** Load `references/rubric.md` for the full scoring rubric
and RubyLLM API verification table (penalty amounts, valid vs hallucinated API
calls, Golden Rules). Load it when scoring dimensions 1-8.

## Workflow

### 1. Identify the model

The user may provide a slug (e.g. `claude_opus_4_6`), a results directory, or
ask to evaluate all pending. If not specified, list available models in
`results/` and ask.

### 2. Load run metadata

Read `results/<slug>/result.json` and extract `status`, `project_summary.present`
(9-artifact checklist), `file_count`, `elapsed_seconds`, phase tokens/time, and
phase 2 validation results when available.

If `status != "completed"`:
- **Do not auto-disqualify.** Evaluate generated code anyway.
- Apply a **structural penalty of -5 to -15 in Deliverable Completeness**
  (timeout phase 1 = -15, failed phase 2 = -5, missing compose/broken Docker = -5).
- Document phase 2 outcome explicitly.

### 3. Run structural scan

```bash
python scripts/benchmark_audit_scan.py results/<slug>
```

*(Script lives at `scripts/benchmark_audit_scan.py` inside this skill.)*

Returns JSON with: test counts, Gemfile gems, artifacts, RubyLLM patterns,
mocks/stubs, and common issues.

### 4. Evaluate the 8 dimensions

See `references/rubric.md` for the full scoring rules. Use data from steps 2+3
and manual reading of key files. **Never invent scores** — justify each rating
with a file:line reference.

- **1. Deliverable Completeness** (0-25) — artifacts per prompt checklist
- **2. RubyLLM Correctness** (0-20) — verify against API table in rubric
- **3. Test Quality** (0-15) — quality over quantity, read actual test files
- **4. Error Handling** (0-10) — rescue blocks, API key preflight, degraded UI
- **5. Persistence / Multi-turn** (0-10) — session/cache vs singleton/none
- **6. Hotwire / Turbo / Stimulus** (0-10) — Turbo Streams, Stimulus, partials
- **7. Architecture** (0-5) — service objects, partial decomposition
- **8. Production Readiness** (0-5) — XSS, secrets, CSRF, AR cleanup

### 5. Classify Runtime Tier

| Tier | Score | Meaning |
|---:|---:|---|
| A | 80-100 | Ship as-is or <30 min patches |
| B | 60-79 | 1-2 hrs to ship, sound architecture |
| C | 40-59 | Major rework, core bugs |
| D | 0-39 | Throw away or architectural inspiration only |

### 6. Generate the Audit Report

MUST contain these sections (800 word limit):

- **A.** Quick summary line (1 sentence)
- **B.** Scores by dimension with 1-line justification (file:line refs)
- **C.** Total score / 100
- **D.** Practical tier (A/B/C/D)
- **E.** Verification section — for each claimed hallucination, show gem source
  grep proof. If unprovable, mark "unverified, likely correct."
- **F.** One killer strength + one killer weakness
- **G.** Final recommendation — worth using for greenfield Rails with RubyLLM?

No speculation — code excerpts + gem source proofs only.

### 7. Update the Success Report (if requested)

- AMD/cloud profile → `docs/success_report.md`
- NVIDIA workstation profile → `docs/success_report.nvidia.md`

Add model row to comparison tables, add failure analysis paragraph for Tier B/C/D,
update runtime viability summary.

## Activation Examples

User: "Evaluate the kimi_k2_5 result"
→ Activate skill → run scanner → read rubric → score 8 dimensions → report

User: "Score the deepseek_v3_2 benchmark"
→ Activate skill → follow full workflow

User: "Benchmark finished, evaluate everything"
→ Activate skill → iterate over all slugs in results/ → consolidated report
