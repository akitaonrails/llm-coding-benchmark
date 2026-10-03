// Proven-negative variant: let bindings are NOT generalized (monomorphic let).
//
// Injected bug: Options.Generalize = false. A let-bound identifier keeps a
// single monomorphic type, so it cannot be used at two different types.
//
// Expectation under `go test`:
//   - TARGET TestLetPolymorphism FAILS (the grader is sensitive to the bug);
//   - the controls PASS (the breakage is targeted, not blanket).
package monolet

import (
	"testing"

	grader "v41lang/grader"
	"v41lang/harness"
	"v41lang/reference"
)

var mk harness.MakeLangFunc = func() harness.Lang {
	o := reference.Default()
	o.Generalize = false
	return reference.New(o)
}

// TARGET
func TestLetPolymorphism(t *testing.T) { grader.RunLetPolymorphism(t, mk) }

// controls (do not depend on let-generalization)
func TestBasicEval(t *testing.T)   { grader.RunBasicEval(t, mk) }
func TestOccursCheck(t *testing.T) { grader.RunOccursCheck(t, mk) }
