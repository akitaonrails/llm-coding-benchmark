// Proven-negative variant: a GC that NEVER frees.
//
// Injected bug: Options.GCCollect = false. The collector traces but reclaims
// nothing, so the live set grows with total allocations and the VM's hard heap
// cap trips (surfaced as a runtime error).
//
// Expectation under `go test`:
//   - TARGETS TestGCNoLeak and TestGCCycles FAIL (unbounded heap / error);
//   - the control PASSES (small programs never approach the cap).
package gcleak

import (
	"testing"

	grader "v41lang/grader"
	"v41lang/harness"
	"v41lang/reference"
)

var mk harness.MakeLangFunc = func() harness.Lang {
	o := reference.Default()
	o.GCCollect = false
	return reference.New(o)
}

// TARGETS
func TestGCNoLeak(t *testing.T) { grader.RunGCNoLeak(t, mk) }
func TestGCCycles(t *testing.T) { grader.RunGCCycles(t, mk) }

// control (no sustained allocation)
func TestBasicEval(t *testing.T) { grader.RunBasicEval(t, mk) }
