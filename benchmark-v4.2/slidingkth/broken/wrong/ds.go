// Package ds — SENSITIVITY: incorrect (never evicts; answers over the WHOLE
// stream, not the window). Expect correctness < 1 once the window slides.
package ds

import (
	"sort"

	"v42slidingkth/harness"
)

type wrong struct{ all []int }

func New(w int) harness.Stream { return &wrong{} }

func (s *wrong) Push(x int) { s.all = append(s.all, x) }

func (s *wrong) Kth(k int) int {
	cp := make([]int, len(s.all))
	copy(cp, s.all)
	sort.Slice(cp, func(i, j int) bool { return harness.Cmp(cp[i], cp[j]) < 0 })
	return cp[k-1] // BUG: whole stream, ignores window eviction
}
