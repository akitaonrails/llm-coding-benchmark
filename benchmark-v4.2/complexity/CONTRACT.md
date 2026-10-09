# CONTRACT — Dynamic Range K-th Smallest (v4.2 / complexity)

You are implementing a single Go data structure. This is a **one-shot** problem: there is one task,
one package, one file is enough. You are graded on **correctness AND efficiency**, and efficiency is
measured objectively — read the scoring section carefully, because a correct-but-naive solution scores
only a fraction of the points.

## Module & package

- Module is `v42complexity` (see `go.mod`). Go 1.22.
- Implement **package `ds`** in a directory `ds/` at the module root (e.g. `ds/ds.go`).
- Expose exactly one constructor:

  ```go
  package ds

  import "v42complexity/harness"

  // New returns a Structure initialized over the given values. initial[i] is the
  // value at index i; n = len(initial), fixed for the lifetime of the structure.
  func New(initial []int) harness.Structure { ... }
  ```

- `harness.Structure` (see `harness/harness.go`) requires:
  - `Assign(i, x int)` — point update: set the value at index i to x.
  - `RangeKth(l, r, k int) int` — return the k-th smallest value among indices l..r inclusive
    (k is 1-based; duplicates count with multiplicity).

## The counted comparison primitive — MANDATORY

All ordering of stored values MUST go through `harness.Cmp(a, b int) int` (−1 / 0 / +1). This is the
*only* way you are permitted to compare two values for ordering. The grader counts every `Cmp` call.

- Arithmetic on raw values (addition, computing a midpoint for binary-search-on-answer, etc.) is
  allowed and is not counted — only **ordering** is counted.
- Using Go's native `<`, `>`, `<=`, `>=` to order stored values instead of `harness.Cmp` is a
  CONTRACT violation; the grader audits source for it and flags implausibly low comparison counts.

## Input bounds (you may rely on these)

- `n` up to ~2·10⁵; number of operations up to ~2·10⁵.
- Values are integers in `[0, 1_000_000_000]`.
- All queries are in-range as defined above; you need not validate inputs.

## How you are graded (continuous, 0–100)

```
score = 100 * correctness * quality
```

- **correctness** ∈ [0,1]: fraction of hidden conformance + adversarial workloads whose every
  `RangeKth` answer matches a brute-force oracle. (Adversarial = many duplicates, skewed ranges,
  updates interleaved with queries, worst-case k.)
- **quality** ∈ [0,1]: a continuous measure of efficiency. On a size sweep (n growing geometrically to
  the bound), the grader counts your total `Cmp` calls on a fixed workload and places you on a **log
  scale between two baselines it computes on the identical workload**:
  - the *naive* baseline — sort each queried range on demand (`O(q·n log n)` comparisons) → quality 0;
  - the *reference* baseline — a sub-linear-per-query structure → quality 1.
  - `quality = clamp( (log(naive_cmps) − log(your_cmps)) / (log(naive_cmps) − log(ref_cmps)), 0, 1 )`,
    evaluated at the largest n at which your structure is still correct and within the time budget.

Implication: a correct solution that sorts each range on demand earns correctness ≈ 1 but quality ≈ 0
(≈ 0–15/100). To score well you must support `RangeKth` in **sub-linear comparisons per query** under
point updates — i.e. a real indexed structure (e.g. a merge-sort tree / Fenwick-of-sorted-lists /
wavelet-style / sqrt-decomposition approach), not a scan-and-sort.

## Rules

- Work only in this workspace. Do NOT read `grader/` or `reference/` (they are not present in your
  copy) and do NOT create `*_test.go` files that import a `grader` package.
- `go build ./...` and `go vet ./...` must pass. Writing your own tests under `ds/` is encouraged.
- Commit your work with git when done.
