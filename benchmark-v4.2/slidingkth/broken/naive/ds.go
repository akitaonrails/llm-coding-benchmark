// Package ds — SENSITIVITY: correct but naive (sort the whole window per Kth).
// Expect correctness ~= 1, quality ~= 0 (defines the naive baseline).
package ds

import (
	"sort"

	"v42slidingkth/harness"
)

type naive struct {
	w    int
	ring []int
	head int
	cnt  int
}

func New(w int) harness.Stream { return &naive{w: w, ring: make([]int, w)} }

func (s *naive) Push(x int) {
	if s.cnt == s.w {
		s.ring[s.head] = x
		s.head = (s.head + 1) % s.w
	} else {
		s.ring[(s.head+s.cnt)%s.w] = x
		s.cnt++
	}
}

func (s *naive) Kth(k int) int {
	cp := make([]int, s.cnt)
	for i := 0; i < s.cnt; i++ {
		cp[i] = s.ring[(s.head+i)%s.w]
	}
	sort.Slice(cp, func(i, j int) bool { return harness.Cmp(cp[i], cp[j]) < 0 })
	return cp[k-1]
}
