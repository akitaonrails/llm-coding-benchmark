// Proven-negative variant: unification WITHOUT the occurs check.
//
// Injected bug: Options.OccursCheck = false. Unifying a variable with a type
// that contains it (a = a -> b) silently succeeds, so self-application is
// wrongly accepted as well-typed.
//
// Expectation under `go test`:
//   - TARGET TestOccursCheck FAILS (self-application is accepted; if a broken
//     impl instead looped, the per-test timeout in the suite would catch it);
//   - the controls PASS.
package noccurs

import (
	"testing"

	grader "v41lang/grader"
	"v41lang/harness"
	"v41lang/reference"
)

var mk harness.MakeLangFunc = func() harness.Lang {
	o := reference.Default()
	o.OccursCheck = false
	return reference.New(o)
}

// TARGET
func TestOccursCheck(t *testing.T) { grader.RunOccursCheck(t, mk) }

// controls (no infinite types involved)
func TestLetPolymorphism(t *testing.T) { grader.RunLetPolymorphism(t, mk) }
func TestRowPolymorphism(t *testing.T) { grader.RunRowPolymorphism(t, mk) }
func TestBasicEval(t *testing.T)       { grader.RunBasicEval(t, mk) }
