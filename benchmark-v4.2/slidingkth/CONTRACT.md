# CONTRACT — Sliding-Window K-th Smallest (v4.2 / slidingkth)

One-shot problem. Implement package `ds` (in `ds/ds.go`) in module `v42slidingkth`:

    func New(w int) harness.Stream

backed by harness.Stream:
  - Push(x int)   // append x; the current window is the most recent w values (fewer until filled)
  - Kth(k int) int // k-th smallest (1-based, duplicates with multiplicity) in the current window

Graded continuously: `score = 100 * correctness * quality`.
  * correctness = fraction of hidden conformance + adversarial workloads matching a brute-force oracle.
  * quality = log-position of your total value-comparison count between a naive baseline (sort the
    whole window on each Kth -> quality 0) and a sub-linear reference (quality 1), at the largest
    sweep size where you are correct and complete in the time budget.

So sorting the window per query earns correctness~1 but quality~0. To score you must maintain an
indexed order-statistics structure under Push eviction (e.g. an order-statistics BST/treap or a
balanced multiset), answering Kth in O(log w) comparisons.

MANDATORY: order stored values ONLY via `harness.Cmp(a,b int) int` (counted; -1/0/+1). Native
<,>,<=,>= on stored values is a violation and is audited. Arithmetic on values is allowed/uncounted.

Bounds: pushes and window up to ~2e5; values in [0,1e9]; queries always valid. `go build ./...` and
`go vet ./...` must pass. Do NOT read grader/ or reference/. Commit with git when done.
