// Proven-negative variant: a reference-COUNTING GC that cannot reclaim cycles.
//
// Injected bug: Options.GCCycles = false. Acyclic garbage is freed (refcount
// reaches zero), but unreachable CYCLES keep each other alive and leak, so the
// heap grows without bound on cyclic churn.
//
// Expectation under `go test`:
//   - TARGET TestGCCycles FAILS (cyclic garbage leaks -> heap cap error);
//   - the controls PASS: TestGCNoLeak and TestGCStressMixed allocate only
//     ACYCLIC garbage, which a refcount collector reclaims — proving the cycle
//     test is specifically about cycle reclamation.
package gccycle

import (
	"testing"

	grader "v41lang/grader"
	"v41lang/harness"
	"v41lang/reference"
)

var mk harness.MakeLangFunc = func() harness.Lang {
	o := reference.Default()
	o.GCCycles = false
	return reference.New(o)
}

// TARGET
func TestGCCycles(t *testing.T) { grader.RunGCCycles(t, mk) }

// controls (acyclic garbage; refcount handles it)
func TestGCNoLeak(t *testing.T)     { grader.RunGCNoLeak(t, mk) }
func TestGCStressMixed(t *testing.T) { grader.RunGCStressMixed(t, mk) }
func TestBasicEval(t *testing.T)     { grader.RunBasicEval(t, mk) }
