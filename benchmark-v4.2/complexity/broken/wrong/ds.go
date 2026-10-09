// Package ds — SENSITIVITY FIXTURE: incorrect (ignores the l,r range and
// answers k-th smallest of the WHOLE array). Expect: correctness < 1.0 (passes
// only when the query happens to span the whole array). Used only to validate
// the grader catches wrong answers.
package ds

import (
	"sort"

	"v42complexity/harness"
)

type wrong struct{ raw []int }

func New(initial []int) harness.Structure {
	r := make([]int, len(initial))
	copy(r, initial)
	return &wrong{raw: r}
}

func (s *wrong) Assign(i, x int) { s.raw[i] = x }

func (s *wrong) RangeKth(l, r, k int) int {
	cp := make([]int, len(s.raw))
	copy(cp, s.raw)
	sort.Slice(cp, func(i, j int) bool { return harness.Cmp(cp[i], cp[j]) < 0 })
	return cp[k-1] // BUG: ignores l, r
}
