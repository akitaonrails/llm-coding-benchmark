package grader

import (
	"testing"

	"v41lang/harness"
	"v41lang/reference"
)

// refMk wires the CORRECT reference implementation into the parameterized
// gauntlet (the SOUND check). A model's grader would instead return a handle
// over its own `lang` package here; the broken variants supply their own maker.
var refMk harness.MakeLangFunc = func() harness.Lang { return reference.NewDefault() }

// --- conformance ---
func TestBasicEval(t *testing.T)    { RunBasicEval(t, refMk) }
func TestClosures(t *testing.T)     { RunClosures(t, refMk) }
func TestRecursion(t *testing.T)    { RunRecursion(t, refMk) }
func TestRecords(t *testing.T)      { RunRecords(t, refMk) }
func TestRecordUpdate(t *testing.T) { RunRecordUpdate(t, refMk) }
func TestLists(t *testing.T)        { RunLists(t, refMk) }

// --- type inference ---
func TestLetPolymorphism(t *testing.T) { RunLetPolymorphism(t, refMk) }
func TestOccursCheck(t *testing.T)     { RunOccursCheck(t, refMk) }
func TestValueRestriction(t *testing.T) { RunValueRestriction(t, refMk) }
func TestRowPolymorphism(t *testing.T) { RunRowPolymorphism(t, refMk) }
func TestTypeErrors(t *testing.T)      { RunTypeErrors(t, refMk) }

// --- GC ---
func TestGCNoLeak(t *testing.T)     { RunGCNoLeak(t, refMk) }
func TestGCCycles(t *testing.T)     { RunGCCycles(t, refMk) }
func TestGCStressMixed(t *testing.T) { RunGCStressMixed(t, refMk) }
