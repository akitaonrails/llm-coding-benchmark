package nosnapshot

import (
	"testing"

	grader "v41store/grader"
)

// TARGET: reads follow the latest committed value, not the snapshot, so a
// transaction's repeated read changes under a concurrent commit.
func TestSnapshotIsolation(t *testing.T) { grader.RunSnapshotIsolation(t, maker()) }

// CONTROL: single-transaction correctness is unaffected.
func TestBasicPutGet(t *testing.T) { grader.RunBasicPutGet(t, maker()) }
