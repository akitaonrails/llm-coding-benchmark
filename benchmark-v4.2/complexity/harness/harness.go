// Package harness provides the counted comparison primitive and the interface
// your solution implements. It is part of the provided scaffold — do NOT modify
// it, and do NOT try to read the grader/ or reference/ directories.
package harness

// cmp counts ordering decisions over stored values. The grader resets it before
// each measured workload and reads it afterwards. It is deliberately a plain
// package global (single-threaded grading); do not rely on concurrency here.
var cmp uint64

// ResetCmp zeroes the comparison counter. (Used by the grader.)
func ResetCmp() { cmp = 0 }

// CmpCount returns the number of comparisons performed since the last ResetCmp.
func CmpCount() uint64 { return cmp }

// Cmp is the ONLY sanctioned way to order two stored values. It returns -1 if
// a<b, 0 if a==b, +1 if a>b — and counts one comparison every call.
//
// Your solution MUST route every ordering decision over stored values through
// Cmp. Arithmetic on raw values (e.g. computing a midpoint for a
// binary-search-on-answer) is permitted and is NOT counted; only ordering is
// counted. Using Go's native <, >, <=, >= operators to order stored values
// instead of Cmp is a CONTRACT violation and is checked for.
func Cmp(a, b int) int {
	cmp++
	switch {
	case a < b:
		return -1
	case a > b:
		return 1
	default:
		return 0
	}
}

// Structure is the data structure your package `ds` must implement and return
// from `ds.New`.
type Structure interface {
	// Assign sets the value at index i (0-based) to x. 0 <= i < n.
	Assign(i, x int)

	// RangeKth returns the k-th smallest value (k is 1-based) among the values
	// currently at indices l..r inclusive. Duplicates count with multiplicity
	// (so in [3,1,3] the 1st smallest is 1, the 2nd is 3, the 3rd is 3).
	// Behavior is required only for 0 <= l <= r < n and 1 <= k <= r-l+1.
	RangeKth(l, r, k int) int
}
