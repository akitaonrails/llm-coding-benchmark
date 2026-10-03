// Package harness is PROVIDED scaffold (seeded to models alongside SPEC.md and
// go.mod). It defines the concrete handle the grader drives and the maker type
// that produces it. The model implements package `lang` and wires a maker in a
// grader `_test.go`, exactly like reference/ does.
//
// INTEGRATION RULE (from P1/P2): the handle exposes ONLY the two contract entry
// points. Any extra accessor the grader wants (e.g. a hook that reports the
// language's own heap counters for the GC gauntlet) is fetched by REFLECTION in
// the grader, never by widening this interface — widening it would silently
// break a model whose method set differs.
package harness

// Lang is the concrete evaluator handle. A model satisfies it with a thin
// adapter over its package-level TypeCheck / Run, e.g.:
//
//	type langHandle struct{}
//	func (langHandle) TypeCheck(src string) error            { return lang.TypeCheck(src) }
//	func (langHandle) Run(src string) (string, error)        { return lang.Run(src) }
//	var mk harness.MakeLangFunc = func() harness.Lang { return langHandle{} }
type Lang interface {
	// TypeCheck infers types for the whole program. It returns a non-nil error
	// for ill-typed programs (with a stable, greppable message) and nil for
	// well-typed ones. It must NOT execute the program.
	TypeCheck(source string) error

	// Run type-checks then executes the program on the VM, returning everything
	// the program wrote via `print` (see SPEC.md for the exact output format).
	// A type error is returned via err with empty output; a runtime error
	// (rare in a well-typed program: only explicit failures such as integer
	// division by zero, or exhausting the VM heap limit) is returned via err.
	Run(source string) (output string, err error)
}

// MakeLangFunc constructs a fresh, independent Lang handle. The grader calls it
// once per test so tests never share mutable state.
type MakeLangFunc func() Lang

// ---------------------------------------------------------------------------
// OPTIONAL instrumentation hook (fetched by the grader via reflection; NOT part
// of the Lang interface). A model that wants to be graded on bounded-heap via
// its own allocator counters (rather than the wall-clock / process-memory
// fallback) may expose, on the concrete type its maker returns, a method with
// this exact shape:
//
//	RunInstrumented(source string) (output string, peakHeapBytes uint64, numCollections int64, err error)
//
// where peakHeapBytes is the high-water mark of the LANGUAGE's own live heap
// (its managed allocator), summed in bytes, observed across the whole run. The
// grader asserts this stays bounded while a non-collecting runtime would blow
// past it. The signature lives here only as documentation; the grader never
// imports it.
