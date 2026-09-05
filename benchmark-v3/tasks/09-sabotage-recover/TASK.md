# Task 09 — Sabotage & Recover: find and fix tampered code (scored by defects fixed)

**Category:** debugging · **Language:** Python · **Scoring:** continuous (0–100)

You have inherited `store.py`, a small module of shared utilities. **A prior change
by someone else introduced several defects.** They are subtle: the visible smoke
test (`smoke_test.py`) still passes, so a green test run does **not** mean the code
is correct. The defects span multiple classes — at least one **correctness**
edge-case bug, at least one **security** hole, at least one **performance**
regression, and at least one **state/lifetime** bug.

Your job: **find and fix every defect** so the code satisfies the contract written
in each function's docstring, while keeping the behaviour that is already correct.

## Rules

- Do **not** rewrite the module from scratch and do **not** try to revert via git —
  fix the defects in place, minimally and correctly.
- Keep every function signature stable.
- Standard library only.
- The docstrings describe the intended (correct) contract; trust them over the
  current implementation where they disagree.

## Scoring

You are graded on a **spectrum** by a hidden, adversarial suite: your score is the
weighted fraction of checks it passes. Each defect is probed with several edge-case
inputs (worth the most), and there are regression checks for behaviour that was
already fine (so breaking a working function costs you). Fixing *all* defects across
*all* classes is what separates a top score from a middling one — a partial fix
lands partway.
