package grader

import (
	"fmt"
	"testing"

	"v41lang/harness"
)

// boundedHeapCap is the live-heap ceiling a correct collector stays under on the
// gauntlet programs. A non-collecting / cycle-leaking runtime blows past it (and
// the reference VM's own hard cap trips, surfacing as a runtime error).
const boundedHeapCap = 32 << 20 // 32 MiB

// gcProgram runs src under the timeout, asserts no error and the exact output,
// and — when the handle exposes the RunInstrumented reflection hook — asserts
// the language's own peak live heap stayed under boundedHeapCap. Without the
// hook it falls back to "completes within the timeout with the right output",
// which a leaking runtime cannot do at these allocation counts.
func gcProgram(t *testing.T, mk harness.MakeLangFunc, name, src, wantOut string) {
	t.Run(name, func(t *testing.T) {
		withTimeout(t, defaultTimeout, func() {
			l := mk()
			r := tryInstrumented(l, src)
			if r.ok {
				if r.err != nil {
					t.Fatalf("Run error (peak=%d, numGC=%d): %v", r.peak, r.ngc, r.err)
				}
				if r.out != wantOut {
					t.Fatalf("output = %q, want %q", r.out, wantOut)
				}
				if r.peak > boundedHeapCap {
					t.Fatalf("peak live heap %d bytes exceeds bound %d (heap not bounded under sustained allocation)", r.peak, boundedHeapCap)
				}
				if r.ngc == 0 {
					t.Fatalf("no collections ran (numGC=0) — the collector never fired under sustained allocation")
				}
				t.Logf("ok: peak=%d bytes, numGC=%d", r.peak, r.ngc)
				return
			}
			// fallback: no instrumentation hook exposed.
			out, err := l.Run(src)
			if err != nil {
				t.Fatalf("Run error (no instrumentation hook): %v", err)
			}
			if out != wantOut {
				t.Fatalf("output = %q, want %q", out, wantOut)
			}
		})
	})
}

// RunGCNoLeak: millions of short-lived, ACYCLIC allocations in a tight loop.
// Must complete with a bounded heap (the live set is O(1) per iteration).
func RunGCNoLeak(t *testing.T, mk harness.MakeLangFunc) {
	const src = `let rec loop = \n ->
	  if n == 0 then 0
	  else
	    let tmp = cons n (cons (n + 1) (cons (n + 2) [])) in
	    let s = {a = n, b = tmp, c = "x"} in
	    let _ = head (tail tmp) in
	    loop (n - 1)
	in print (loop 2000000)`
	gcProgram(t, mk, "millions_short_lived", src, "0\n")
}

// RunGCCycles: each iteration builds a self-referential `let rec` closure (a
// closure whose captured environment points back at the closure — a genuine
// heap cycle) and drops it. A tracing collector reclaims the cyclic garbage; a
// reference-count-only collector leaks it and the heap grows without bound.
func RunGCCycles(t *testing.T, mk harness.MakeLangFunc) {
	const src = `let rec spin = \n ->
	  if n == 0 then 0
	  else
	    let rec self = \x -> if x == 0 then 0 else self (x - 1) in
	    let _ = self 1 in
	    spin (n - 1)
	in print (spin 1000000)`
	gcProgram(t, mk, "unreachable_cycles_reclaimed", src, "0\n")
}

// RunGCStressMixed: a long-lived retained structure coexisting with heavy
// short-lived churn. Correct result AND bounded heap (bounded by the live set,
// not the total allocated).
func RunGCStressMixed(t *testing.T, mk harness.MakeLangFunc) {
	const churn = 1000000
	total := int64(churn) * int64(churn+1) / 2 // sum 1..churn
	want := fmt.Sprintf("false\n%d\n", total)
	const src = `let rec build = \acc -> \n -> if n == 0 then acc else build (cons n acc) (n - 1) in
	let keep = build [] 20000 in
	let rec churn = \n -> \s ->
	  if n == 0 then s
	  else
	    let tmp = cons n (cons n []) in
	    churn (n - 1) (s + head tmp)
	in
	let total = churn 1000000 0 in
	let _ = print (null keep) in
	print total`
	gcProgram(t, mk, "longlived_plus_churn", src, want)
}
