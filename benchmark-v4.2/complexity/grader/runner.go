// Command runner exercises a `ds` package on a seeded workload and prints JSON:
// {"n","q","cmp","mismatch","total"}. The grader copies this into an isolated
// workspace alongside harness/ and ONE ds/ package (candidate | reference |
// naive), so the three are measured on identical workloads and their Cmp counts
// are directly comparable. The brute oracle uses native sort (NOT harness.Cmp),
// so verification never pollutes the comparison count.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"sort"

	"v42complexity/ds"
	"v42complexity/harness"
)

func oracleKth(a []int, l, r, k int) int {
	cp := make([]int, r-l+1)
	copy(cp, a[l:r+1])
	sort.Ints(cp)
	return cp[k-1]
}

func main() {
	seed := flag.Int64("seed", 1, "rng seed")
	n := flag.Int("n", 1000, "number of elements")
	q := flag.Int("q", 1000, "number of operations")
	dup := flag.Bool("dup", false, "small value domain (many duplicates)")
	fullRange := flag.Bool("fullrange", false, "bias queries toward wide ranges")
	flag.Parse()

	rng := rand.New(rand.NewSource(*seed))
	valHi := 1_000_000_000
	if *dup {
		valHi = 20
	}
	initial := make([]int, *n)
	oracle := make([]int, *n)
	for i := range initial {
		initial[i] = rng.Intn(valHi + 1)
		oracle[i] = initial[i]
	}

	harness.ResetCmp() // build comparisons count toward quality
	st := ds.New(append([]int(nil), initial...))

	mism, total := 0, 0
	for t := 0; t < *q; t++ {
		if rng.Intn(2) == 0 {
			i := rng.Intn(*n)
			x := rng.Intn(valHi + 1)
			st.Assign(i, x)
			oracle[i] = x
		} else {
			var l, r int
			if *fullRange && rng.Intn(3) == 0 {
				l, r = 0, *n-1
			} else {
				l = rng.Intn(*n)
				r = rng.Intn(*n)
				if l > r {
					l, r = r, l
				}
			}
			k := rng.Intn(r-l+1) + 1
			got := st.RangeKth(l, r, k)
			want := oracleKth(oracle, l, r, k)
			total++
			if got != want {
				mism++
			}
		}
	}

	out := map[string]any{"n": *n, "q": *q, "cmp": harness.CmpCount(), "mismatch": mism, "total": total}
	b, _ := json.Marshal(out)
	fmt.Println(string(b))
}
