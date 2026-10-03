// Proven-negative test for the "learnervote" broken variant.
//
// Injected bug: learners are folded into the voter set, so they are counted
// toward quorum (and may vote). A disconnected/behind learner then blocks
// commits that the real voter majority should still be able to make.
//
// Expectation: TestLearnerCatchup FAILS; the controls PASS.
package learnervote

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

// TARGET: once a learner is counted toward quorum, losing one real voter plus
// the learner stalls commits the voter majority should still make.
func TestLearnerCatchup(t *testing.T) { grader.RunLearnerCatchup(t, mk) }

// --- controls (no learners): these must still PASS ---
func TestInitialElection(t *testing.T) { grader.RunInitialElection(t, mk) }
func TestBasicAgree(t *testing.T)      { grader.RunBasicAgree(t, mk) }
func TestSnapshotBasic(t *testing.T)   { grader.RunSnapshotBasic(t, mk) }
