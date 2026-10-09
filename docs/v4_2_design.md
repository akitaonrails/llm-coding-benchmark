# v4.2 — the de-saturation suite (density vs harness)

**Goal.** v4.1 saturated: genesys-house = fable = gpt-6-astra = 100/100 on all three problems. A
perfect score proves "frontier-capable" but **cannot rank** the top. v4.2 is built to *not* saturate,
so it can answer the sharper question the user posed:

> Are there programming problems that **only an astra/fable-level frontier model solves**, that
> near-frontier models (Qwen 3.8 Max, GLM-5.x, Kimi K2/K3) and small models (phi-4) **fail** — and
> if so, **where does genesys land**: with the frontier, or with the near-frontier floor?

## The thesis under test

Genesys's own framing (NDA): a ~54–70B hybrid that reaches frontier *programming* results by leaning
on **agentic capability** (web-fetch / tool-use fills knowledge gaps) rather than raw parametric
density. Two prior findings in this repo bear on this:

- **v3 differentiation finding (2026-09-05):** algorithmic difficulty does **not** separate
  frontier-from-frontier — they're at parity on well-scoped coding. (v4.1 re-confirmed.)
- **rails/ai-evals:** the lever that de-saturates quality is **API/library recall** (obscure,
  past-cutoff) — not raw algorithmic hardness.

Today's external evidence (2026) refines the near-frontier gap:

- **GLM-5 collapses on isolated one-shot codegen** (LiveCodeBench ~52 vs Qwen 3.5 ~83.6) — tuned for
  agentic SWE at the expense of cold generation.
- **Qwen3.8-Max ~67.7% SWE-bench Pro** — fails ~1/3 of real multi-file tasks.
- **Near-frontier failure mode = spec-reading + integration**, not codegen (controlled 5-model build).
- **The benchmarks that still de-saturate the *frontier* are long-horizon agentic**: Terminal-Bench 4.0
  (frontier ~31%), DeepSWE, SaaSBench. SWE-bench Verified is saturated.

## The two-track design (and why both)

| Track | Shape | What it isolates | Harness role | Prediction if genesys is truly ~60B |
|---|---|---|---|---|
| **A — long-horizon agentic** | multi-file, spec-dense, accumulating sprints | model+harness coherence over a long horizon | **high** (harness does heavy lifting) | genesys ≈ frontier → *thesis-confirming* |
| **B — isolated one-shot, continuous-scored** | single prompt, single file, no web-fetchable answer | **raw model density** | **neutral** (nothing to fetch/integrate) | genesys **falls toward the near-frontier floor**, below astra/fable → *the discriminator* |

**Track B is the load-bearing experiment.** It is designed so the harness cannot rescue a
less-dense model: one self-contained algorithmic problem, no external APIs, no multi-file integration,
and **continuous scoring** that is mathematically incapable of saturating at 100 for everyone.

Track A exists as the *contrast*: if genesys ties the frontier on A but drops below it on B, that is the
cleanest possible statement of "small model + harness = frontier *agentically*, but not frontier *in
raw density*." If genesys ties the frontier on **both**, the "not as dense" framing is in real tension
and genesys is genuinely frontier-dense.

## Scoring model (the key difference from v4.1)

v4.1 scored pass/fail gauntlets → saturated. v4.2 Track-B scores **continuously**:

```
score = 100 * correctness_fraction * quality_factor
```

- `correctness_fraction` ∈ [0,1] — fraction of hidden conformance + adversarial cases passed.
- `quality_factor` ∈ [0,1] — a **continuous** measure of solution *quality* that the naive-correct
  solution does NOT max out:
  - complexity-bounded problems: fitted growth of a **counted primitive** (comparisons / accesses)
    vs a target asymptotic — a correct-but-O(n²) answer scores high correctness, low quality.
  - optimizer problems: **approximation ratio** to a known/au­thoritative optimum on hidden instances.
  - compiler problems: generated-code **cost** vs an optimal oracle.

A near-frontier model that writes "correct but naive" lands at e.g. 1.0 × 0.4 = **40**; a frontier
model that finds the optimal structure lands near **95**; a small model that is simply wrong lands
near **0–15**. The spread is the measurement.

### Determinism, not wall-clock
Quality is measured by **operation counts through a harness-provided counted primitive**, never by
wall-time (noisy, machine-dependent, non-reproducible — cf. the hermetic-grader lesson). The CONTRACT
requires all comparisons/accesses to route through `harness.Cmp` / instrumented accessors; the grader
counts them and fits the growth curve across a size sweep.

## Track-B problem set (4, built in this order)

1. **complexity** — *Dynamic Range K-th Smallest* (PILOT). Array with point-assign updates +
   `RangeKth(l,r,k)` value queries; all value comparisons via counted `harness.Cmp`. Naive = sort per
   query (correct, O(q·n log n) cmps → low quality). Optimal = merge-sort-tree / BIT-of-sorted-lists /
   wavelet (O((n+q) polylog)). Well-calibrated: large partial-credit band. Fully offline.
2. **optimizer** — an NP-hard problem (bin-packing / interval scheduling with release times) scored by
   **approximation ratio** to an exact/ILP oracle on hidden instances. Continuous by construction.
3. **compiler** — a small optimizing pass (e.g. local register allocation + spill, or a peephole/DCE
   pipeline over a fixed IR) scored by generated-code cost vs an optimal oracle. Heaviest grader.
4. **contest** — past-cutoff competitive problems (Codeforces Div1 E/F dated after Jan 2026), objective
   hidden tests. Strongest novelty guarantee; problems sourced + vetted before use.

## Track-A problem (1)

- **agentic** — a long-horizon, spec-dense, multi-file systems build in the v4.1 accumulating-sprint
  style, but engineered for a Terminal-Bench-4.0-like frontier-<100 regime (deeply interacting
  constraints, buried requirements, a hidden conformance gauntlet). The contrast to Track B.

## Model roster

| Role | Models |
|---|---|
| **Frontier ceiling** | gpt-6-astra (Codex sub), fable-5-1 (Claude Code sub) |
| **Subject** | genesys-pi-house (+ enterprise for reference) |
| **Near-frontier floor (calibration)** | Qwen 3.8 Max (OR), GLM-5.x (z.ai coding), Kimi K2/K3 (Kimi CLI / OR) |
| **Small control** | phi-4 (Strix Halo, local) |

The near-frontier cohort is not decoration — it **calibrates** the claim. "Only astra/fable solve this"
is only true if Qwen/GLM/Kimi measurably fail it. The suite is validated iff, on the pilot:
`astra,fable ≫ Qwen,GLM,Kimi,phi-4`. Only then is "where does genesys land" a meaningful question.

## Integrity (unchanged from v4.1, applies to every run)
Shield the grading key + sibling outputs + CLAUDE.md + docs before every run; git-isolate each
workspace; serial waves only (no concurrent shield writers); analyze only clean runs; verify scores.
Cost claims re-checked against primary pricing at analysis time.

## Build/validate discipline
Each problem's grader is validated **sound** (reference → ~100) **and sensitive** (a deliberately
naive-but-correct variant → high correctness, LOW quality; a wrong variant → low correctness) BEFORE
any model runs. Pilot `complexity` runs the full roster first; the other three problems + Track A
proceed only after the pilot demonstrably de-saturates.
