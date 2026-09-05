# Benchmark v3 — a frontier-discriminating coding benchmark

## Why v3 exists

v2 saturates: frontier models cluster at 95–96 because v2 measures **completeness**
("are the 14 features present and working on the happy path"), a solved skill at the
frontier. The only axis that ever separated models was *knowing the real RubyLLM API
vs hallucinating it* — a grounding test that no longer discriminates now that the API
is well known. v2 also lets the model **write its own tests**, so "writes good tests"
inflates the score instead of measuring correctness.

v3 changes what is measured, from **completeness** to **correctness depth** — the axes
where frontier models genuinely still differ: root-cause debugging, edge-case
correctness, invariant maintenance across a long horizon, performance under a hard
gate, safe refactoring, and judgment under ambiguity.

## The core mechanism: hidden held-out verification

The model **never sees the tests it is graded on.** Each task ships:

- `TASK.md` — the problem statement the model receives (plus a few *visible* example
  cases so it can self-check the happy path).
- `workspace/` — the starter state the model works in (brownfield code, a stub to
  implement, or code to refactor). Copied into the run; the model edits it in place.
- `hidden/` — the held-out grader: an **adversarial** test suite, weighted toward
  edges (empty / overflow / unicode / concurrent / malformed / boundary), plus —
  where applicable — a **variant-bug** re-trigger, a **regression** suite, and a
  **performance** harness. Never copied into the run; never shown to the model.
- `reference/` — a known-correct solution used only to *validate the hidden suite*
  (the reference must score 100%; a plausible naive solution must score clearly < 100%
  — that gap is the task's discriminating power, recorded in `meta.json`).
- `meta.json` — grading config: language, category, weights, gates, and the recorded
  reference-vs-naive spread.

The model's own tests do **not** count toward the score. Its output is graded solely
by `hidden/`. This turns a saturated pass/fail into a **continuous correctness score**
that spreads the frontier.

## Categories (one flagship task each)

| # | Category | What it measures | Lang |
|---|---|---|---|
| 01 | Root-cause debugging (brownfield) | fixes the *cause*, not the symptom | Ruby |
| 02 | Edge-case correctness (hidden suite) | correctness on adversarial edges | Go |
| 03 | Long-horizon invariant | consistency under replay / out-of-order / redelivery | Python |
| 04 | Performance under a hard gate | right complexity within time+memory | Rust |
| 05 | Safe refactor (behavior preservation) | no regressions under a hidden characterization suite | Ruby |
| 06 | Ambiguity / judgment trap | recognizing the non-obvious-correct interpretation | Python |

## Scoring (per task → 0–100, then averaged)

- **correctness** (primary): hidden-suite pass rate, **edge-weighted** (edge cases
  count more than happy-path examples). Continuous.
- **root-cause gate** (debug tasks): a *variant* of the planted bug must also be fixed;
  failing it caps correctness (a symptom patch cannot score full marks).
- **regression gate** (brownfield / refactor): the pre-existing hidden characterization
  tests must still pass; any regression is a hard penalty.
- **performance gate** (perf tasks): hard wall-time + memory ceiling, pass/fail.
- **honesty** (kept from v2, lightweight): does the self-review's claimed status match
  the hidden-suite reality? Over-claiming ("all edge cases handled" while failing them)
  is penalized; accurate disclosure is not.

A task's score is `weighted(correctness) × gates`. The benchmark score is the mean
across the six tasks. Because correctness is continuous and edge-weighted, two models
that both "build the feature" separate by *how correct* they actually are.

## Anti-gaming / integrity

- `hidden/` and `reference/` are **never** placed in the model's workspace and are
  shielded like all grading material (see CLAUDE.md "Benchmark-integrity").
- Each run's workspace is git-sandboxed (isolated `.git`, `GIT_CEILING_DIRECTORIES`)
  so the model cannot read the benchmark repo's history.
- Every hidden suite is **self-validated**: `grade.py --validate <task>` runs the
  reference (must be 100%) and the recorded naive solution (must be < 100%) before the
  task is considered admissible. A task that both solutions pass equally is not
  discriminating and is rejected.

## Layout

```
benchmark-v3/
  README.md                 (this file)
  grade.py                  (the hidden-suite grader + --validate)
  tasks/
    01-debug-<name>/
      TASK.md  meta.json  workspace/  hidden/  reference/
    02-edge-<name>/ ...
```
