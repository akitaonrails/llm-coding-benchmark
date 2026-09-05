# Task 15 — Count subarrays by median

**Category:** algorithm · **Language:** Python · **Scoring:** continuous (0–100)

Implement `count_subarrays_median_at_least(a, k)`: given a list of integers `a` and an
integer `k`, return how many contiguous, non-empty subarrays have a **median >= k**.

The median of a subarray of length `L` is the element at index `(L - 1) // 2` of the
sorted subarray (i.e. the **lower** median when `L` is even).

Example: `a = [5, 1, 5]`, `k = 3` → the subarrays `[5]`, `[5,1,5]`, `[5]` have median
`>= 3`, so the answer is `3`.

Constraints: values and `k` may be any integers (including negatives, duplicates). `a`
can be **large** (up to ~1e5 elements), so an `O(n^2)` approach will be too slow.

Standard library only. Keep the signature. Edit `median.py` in place. Graded on a
spectrum: correctness is required, and among correct solutions the score rises as your
running time approaches an efficient reference — a correct-but-slow solution scores low.
