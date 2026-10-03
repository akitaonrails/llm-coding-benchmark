package plainsi

import (
	"testing"

	grader "v41store/grader"
)

// TARGETS: plain SI lets write skew through and produces non-serializable fuzz
// histories.
func TestWriteSkew(t *testing.T)        { grader.RunWriteSkew(t, maker()) }
func TestSerializableFuzz(t *testing.T) { grader.RunSerializableFuzz(t, maker()) }

// CONTROLS: must still PASS (the bug is targeted, not a blanket breakage).
func TestBasicPutGet(t *testing.T)       { grader.RunBasicPutGet(t, maker()) }
func TestSnapshotIsolation(t *testing.T) { grader.RunSnapshotIsolation(t, maker()) }
func TestLostUpdate(t *testing.T)        { grader.RunLostUpdate(t, maker()) }
