// Proven-negative test for the "nopersist" broken variant.
//
// Injected bug: persist() is a no-op (currentTerm/votedFor/log never saved).
//
// Expectation when run with `go test`:
//   - the targeted test(s) below FAIL (the grader is SENSITIVE to this bug);
//   - the control tests PASS (the bug is targeted, not a blanket breakage).
package nopersist

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

// TARGET: durable state is never written, so committed entries vanish across a
// crash/restart -> TestPersist1 fails.
func TestPersist1(t *testing.T) { grader.RunPersist1(t, mk) }

// --- controls: these must still PASS, proving the bug is targeted ---
func TestInitialElection(t *testing.T) { grader.RunInitialElection(t, mk) }
func TestBasicAgree(t *testing.T)      { grader.RunBasicAgree(t, mk) }
