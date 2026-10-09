// Package ds — REFERENCE implementation (the quality==1.0 baseline). Not shown
// to models. Sqrt-decomposition: each block keeps a sorted copy of its values;
// RangeKth is a binary-search-on-answer that counts "values <= mid" over the
// range using Cmp (full blocks via binary search in the sorted copy, partial
// blocks by scan). Point update rebuilds one block's sorted copy.
//
// Per query: O(log V * (sqrt(n) * log(sqrt n) + sqrt(n))) comparisons.
// Per update: O(sqrt(n) * log(sqrt n)) comparisons. Both strictly sub-linear,
// vs the naive sort-per-query O(n log n) comparisons per query.
package ds

import (
	"sort"

	"v42complexity/harness"
)

const valMax = 1_000_000_000

type structure struct {
	raw    []int
	block  int     // block size
	sorted [][]int // sorted copy per block
}

func New(initial []int) harness.Structure {
	n := len(initial)
	b := 1
	for b*b < n {
		b++
	}
	s := &structure{raw: make([]int, n), block: b}
	copy(s.raw, initial)
	nb := (n + b - 1) / b
	s.sorted = make([][]int, nb)
	for bi := 0; bi < nb; bi++ {
		s.rebuild(bi)
	}
	return s
}

// rebuild recomputes the sorted copy of block bi using Cmp for ordering.
func (s *structure) rebuild(bi int) {
	lo := bi * s.block
	hi := lo + s.block
	if hi > len(s.raw) {
		hi = len(s.raw)
	}
	cp := make([]int, hi-lo)
	copy(cp, s.raw[lo:hi])
	sort.Slice(cp, func(i, j int) bool { return harness.Cmp(cp[i], cp[j]) < 0 })
	s.sorted[bi] = cp
}

func (s *structure) Assign(i, x int) {
	if s.raw[i] == x {
		return
	}
	s.raw[i] = x
	s.rebuild(i / s.block)
}

// countLE returns the number of indices j in [l,r] with value <= v, using Cmp.
func (s *structure) countLE(l, r, v int) int {
	cnt := 0
	bl := l / s.block
	br := r / s.block
	if bl == br {
		for j := l; j <= r; j++ {
			if harness.Cmp(s.raw[j], v) <= 0 {
				cnt++
			}
		}
		return cnt
	}
	// left partial block
	leftEnd := (bl+1)*s.block - 1
	for j := l; j <= leftEnd; j++ {
		if harness.Cmp(s.raw[j], v) <= 0 {
			cnt++
		}
	}
	// full blocks: binary search upper_bound in sorted copy
	for bi := bl + 1; bi < br; bi++ {
		cnt += upperBound(s.sorted[bi], v)
	}
	// right partial block
	rightStart := br * s.block
	for j := rightStart; j <= r; j++ {
		if harness.Cmp(s.raw[j], v) <= 0 {
			cnt++
		}
	}
	return cnt
}

// upperBound returns the count of elements in sorted slice a that are <= v.
func upperBound(a []int, v int) int {
	lo, hi := 0, len(a)
	for lo < hi {
		mid := (lo + hi) / 2
		if harness.Cmp(a[mid], v) <= 0 {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	return lo
}

func (s *structure) RangeKth(l, r, k int) int {
	lo, hi := 0, valMax
	for lo < hi {
		mid := lo + (hi-lo)/2
		if s.countLE(l, r, mid) >= k {
			hi = mid
		} else {
			lo = mid + 1
		}
	}
	return lo
}
