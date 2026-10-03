package lostupdate

import (
	"testing"

	grader "v41store/grader"
)

// TARGET: with no conflict detection, two concurrent read-modify-writes both
// commit and one update is lost.
func TestLostUpdate(t *testing.T) { grader.RunLostUpdate(t, maker()) }

// CONTROLS: must still PASS.
func TestBasicPutGet(t *testing.T)       { grader.RunBasicPutGet(t, maker()) }
func TestSnapshotIsolation(t *testing.T) { grader.RunSnapshotIsolation(t, maker()) }
