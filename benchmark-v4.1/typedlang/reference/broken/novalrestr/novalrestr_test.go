// Proven-negative variant: generalization WITHOUT the value restriction.
//
// Injected bug: Options.ValueRestriction = false. A non-value let binding (a ref
// cell) is generalized, so the one mutable cell can be used at two element
// types — the classic unsound case.
//
// Expectation under `go test`:
//   - TARGET TestValueRestriction FAILS (the unsound program is accepted);
//   - the controls PASS (sound generalization of real values still works).
package novalrestr

import (
	"testing"

	grader "v41lang/grader"
	"v41lang/harness"
	"v41lang/reference"
)

var mk harness.MakeLangFunc = func() harness.Lang {
	o := reference.Default()
	o.ValueRestriction = false
	return reference.New(o)
}

// TARGET
func TestValueRestriction(t *testing.T) { grader.RunValueRestriction(t, mk) }

// controls
func TestLetPolymorphism(t *testing.T) { grader.RunLetPolymorphism(t, mk) }
func TestOccursCheck(t *testing.T)     { grader.RunOccursCheck(t, mk) }
func TestBasicEval(t *testing.T)       { grader.RunBasicEval(t, mk) }
