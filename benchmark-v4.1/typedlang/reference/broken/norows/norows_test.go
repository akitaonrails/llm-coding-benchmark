// Proven-negative variant: records WITHOUT row polymorphism (closed records).
//
// Injected bug: Options.Rows = false. Field access demands a CLOSED record with
// exactly the accessed field, so a function `\r -> r.a` cannot accept both
// {a,b} and {a,c}.
//
// Expectation under `go test`:
//   - TARGET TestRowPolymorphism FAILS;
//   - the controls PASS (they do not rely on open records).
package norows

import (
	"testing"

	grader "v41lang/grader"
	"v41lang/harness"
	"v41lang/reference"
)

var mk harness.MakeLangFunc = func() harness.Lang {
	o := reference.Default()
	o.Rows = false
	return reference.New(o)
}

// TARGET
func TestRowPolymorphism(t *testing.T) { grader.RunRowPolymorphism(t, mk) }

// controls (no row polymorphism needed)
func TestBasicEval(t *testing.T)       { grader.RunBasicEval(t, mk) }
func TestLetPolymorphism(t *testing.T) { grader.RunLetPolymorphism(t, mk) }
func TestOccursCheck(t *testing.T)     { grader.RunOccursCheck(t, mk) }
