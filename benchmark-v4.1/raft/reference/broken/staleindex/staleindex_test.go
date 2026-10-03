// Proven-negative test for the "staleindex" broken variant.
//
// Injected bug: Snapshot trims the log but does NOT advance the base offset
// (lastIncludedIndex), so every offset-aware log helper computes raft indices
// that are off after the first snapshot — replication and commit break.
//
// Expectation: the TestSnapshot* tests FAIL; the non-snapshot controls PASS.
package staleindex

import (
	"testing"

	"v41raft/harness"
	"v41raft/harness/labrpc"

	grader "v41raft/grader"
)

func mk(peers []*labrpc.ClientEnd, me int, persister *harness.Persister,
	applyCh chan harness.ApplyMsg, initial harness.Config) harness.RaftNode {
	return Make(peers, me, persister, applyCh, initial)
}

// TARGETS: anything that compacts the log.
func TestSnapshotBasic(t *testing.T)   { grader.RunSnapshotBasic(t, mk) }
func TestSnapshotInstall(t *testing.T) { grader.RunSnapshotInstall(t, mk) }
func TestSnapshotCrash(t *testing.T)   { grader.RunSnapshotCrash(t, mk) }

// --- controls (no snapshotting): these must still PASS ---
func TestInitialElection(t *testing.T) { grader.RunInitialElection(t, mk) }
func TestBasicAgree(t *testing.T)      { grader.RunBasicAgree(t, mk) }
func TestPersist1(t *testing.T)        { grader.RunPersist1(t, mk) }
