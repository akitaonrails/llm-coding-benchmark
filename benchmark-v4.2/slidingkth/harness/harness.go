// Package harness — provided scaffold (do NOT modify; do NOT read grader/ or
// reference/). Counted comparison primitive + the streaming interface.
package harness

var cmp uint64

func ResetCmp() { cmp = 0 }

func CmpCount() uint64 { return cmp }

// Cmp is the ONLY sanctioned way to order two stored values (-1/0/+1). Every
// ordering decision over stored values MUST go through it; it counts one
// comparison per call. Native <,>,<=,>= on stored values is a CONTRACT
// violation. Arithmetic on values is allowed and not counted.
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

// Stream is the sliding-window structure your package `ds` implements and
// returns from ds.New(w).
type Stream interface {
	// Push appends value x to the stream. The current window is the most
	// recently pushed w values (or all pushed so far, if fewer than w).
	Push(x int)
	// Kth returns the k-th smallest value (1-based, duplicates with
	// multiplicity) among the current window. Called only when the window is
	// non-empty and 1 <= k <= current window size.
	Kth(k int) int
}
