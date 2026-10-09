// Command runner drives a ds.Stream on a seeded sliding-window workload and
// prints {"n","w","q","cmp","mismatch","total"}. Oracle uses native sort (no
// harness.Cmp) so verification never pollutes the comparison count.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"sort"

	"v42slidingkth/ds"
	"v42slidingkth/harness"
)

func main() {
	seed := flag.Int64("seed", 1, "")
	n := flag.Int("n", 2000, "number of pushes")
	w := flag.Int("w", 1000, "window size")
	q := flag.Int("q", 2000, "number of queries (evenly spaced after warmup)")
	dup := flag.Bool("dup", false, "small value domain")
	flag.Parse()

	rng := rand.New(rand.NewSource(*seed))
	valHi := 1_000_000_000
	if *dup {
		valHi = 20
	}
	// query indices: evenly spaced in [w-1, n-1]
	qset := make(map[int]bool)
	if *n > *w {
		step := (*n - *w) / *q
		if step < 1 {
			step = 1
		}
		for i := *w - 1; i < *n; i += step {
			qset[i] = true
		}
	} else {
		qset[*n-1] = true
	}

	st := ds.New(*w)
	window := make([]int, 0, *w)
	harness.ResetCmp()
	mism, total := 0, 0
	for i := 0; i < *n; i++ {
		x := rng.Intn(valHi + 1)
		st.Push(x)
		window = append(window, x)
		if len(window) > *w {
			window = window[1:]
		}
		if qset[i] {
			k := rng.Intn(len(window)) + 1
			got := st.Kth(k)
			cp := make([]int, len(window))
			copy(cp, window)
			sort.Ints(cp)
			total++
			if got != cp[k-1] {
				mism++
			}
		}
	}
	out := map[string]any{"n": *n, "w": *w, "q": *q, "cmp": harness.CmpCount(), "mismatch": mism, "total": total}
	b, _ := json.Marshal(out)
	fmt.Println(string(b))
}
