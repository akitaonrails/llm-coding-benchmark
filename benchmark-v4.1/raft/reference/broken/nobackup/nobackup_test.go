// Proven-negative test for the "nobackup" broken variant.
//
// Injected bug: AppendEntries rejection does not back up nextIndex (no retry).
//
// Expectation when run with `go test`:
//   - the targeted test(s) below FAIL (the grader is SENSITIVE to this bug);
//   - the control tests PASS (the bug is targeted, not a blanket breakage).
package nobackup

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

// TARGET: the leader never backs up nextIndex on rejection, so a diverged
// follower is never repaired and agreement that needs it stalls -> TestRejoin
// fails.
func TestRejoin(t *testing.T) { grader.RunRejoin(t, mk) }

// --- controls: these must still PASS, proving the bug is targeted ---
func TestInitialElection(t *testing.T) { grader.RunInitialElection(t, mk) }
func TestBasicAgree(t *testing.T)      { grader.RunBasicAgree(t, mk) }
