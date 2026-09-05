# Task 08 — Performance: range-sum queries at scale (scored by speed)

**Category:** performance · **Language:** Python · **Scoring:** continuous (0–100)

`rangesum.py` answers range-sum queries over timestamped values. You are given `N`
events, each `(timestamp, value)`, and `Q` queries, each an inclusive range
`(lo, hi)`. For every query, return the **sum of the values of all events whose
timestamp is in `[lo, hi]`**.

The starter is **correct but slow** — it rescans every event for every query, so it
is `O(N*Q)`. On the hidden input `N` and `Q` are large, and that approach will not
finish in time.

## Scoring

You are graded on a **speed spectrum**, not pass/fail. A hidden runner times your
`solve` against an efficient reference **on the same machine, in the same run**, so
the score is hardware-independent:

- **Correctness is a gate** — checked on many small random inputs and on the big
  input (edge cases: empty events, duplicate timestamps, `hi < lo`, negative
  values). A wrong answer scores near zero regardless of speed.
- Among correct solutions, your score rises smoothly as your running time approaches
  the reference's. Matching the reference's asymptotic efficiency scores ~100; a
  correct-but-`O(N*Q)` solution is capped by a hard time budget and lands near 0;
  something in between lands in between.

## Constraints

- Keep the signature: `solve(events, queries) -> list[int]`.
- Timestamps, values, and range bounds are arbitrary integers; **values may be
  negative**; many events may share a timestamp; a query with `hi < lo` sums to `0`.
- Standard library only. Edit `rangesum.py` in place.
