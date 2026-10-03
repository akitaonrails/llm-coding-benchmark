package nofsync

import (
	"testing"

	grader "v41store/grader"
)

// TARGETS: without an fsync on the WAL, a crash discards the just-committed
// (un-fsynced) bytes, so durability and crash-mid-commit atomicity break.
func TestCommitDurable(t *testing.T)        { grader.RunCommitDurable(t, maker()) }
func TestCrashMidCommitAtomic(t *testing.T) { grader.RunCrashMidCommitAtomic(t, maker()) }

// CONTROLS: must still PASS (they never crash).
func TestBasicPutGet(t *testing.T)       { grader.RunBasicPutGet(t, maker()) }
func TestSnapshotIsolation(t *testing.T) { grader.RunSnapshotIsolation(t, maker()) }
