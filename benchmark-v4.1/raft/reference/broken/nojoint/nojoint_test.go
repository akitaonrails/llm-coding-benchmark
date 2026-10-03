// Proven-negative test for the "nojoint" broken variant.
//
// Injected bug: ChangeMembership performs an instant single-configuration
// switch (no joint C_old,new phase) and takes agreement over the NEW voter set
// only. Under a partition this allows split-brain / committed-entry loss.
//
// Expectation: TestMembershipJoint FAILS; the controls PASS.
package nojoint

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

// TARGET: a non-joint reconfiguration under partition is unsafe.
func TestMembershipJoint(t *testing.T) { grader.RunMembershipJoint(t, mk) }

// --- controls: these must still PASS ---
func TestInitialElection(t *testing.T) { grader.RunInitialElection(t, mk) }
func TestBasicAgree(t *testing.T)      { grader.RunBasicAgree(t, mk) }
func TestLearnerCatchup(t *testing.T)  { grader.RunLearnerCatchup(t, mk) }
