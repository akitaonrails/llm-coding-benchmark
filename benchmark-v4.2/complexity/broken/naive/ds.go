// Package ds — SENSITIVITY FIXTURE: correct but naive (sort each range on
// demand). Expect: correctness ~= 1.0, quality ~= 0 (defines the naive
// baseline). Used only to validate the grader de-saturates.
package ds

import (
	"sort"

	"v42complexity/harness"
)

type naive struct{ raw []int }

func New(initial []int) harness.Structure {
	r := make([]int, len(initial))
	copy(r, initial)
	return &naive{raw: r}
}

func (s *naive) Assign(i, x int) { s.raw[i] = x }

func (s *naive) RangeKth(l, r, k int) int {
	cp := make([]int, r-l+1)
	copy(cp, s.raw[l:r+1])
	sort.Slice(cp, func(i, j int) bool { return harness.Cmp(cp[i], cp[j]) < 0 })
	return cp[k-1]
}
