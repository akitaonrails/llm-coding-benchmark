// Proven-negative test for the "nomajority" broken variant.
//
// Injected bug: the leader commits as soon as an entry is local (no majority).
//
// Expectation when run with `go test`:
//   - the targeted test(s) below FAIL (the grader is SENSITIVE to this bug);
//   - the control tests PASS (the bug is targeted, not a blanket breakage).
package nomajority

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

// TARGET: committing without a majority lets a minority leader "commit"
// unsafe entries -> TestFailNoAgree fails.
func TestFailNoAgree(t *testing.T) { grader.RunFailNoAgree(t, mk) }

// --- controls: these must still PASS, proving the bug is targeted ---
func TestInitialElection(t *testing.T) { grader.RunInitialElection(t, mk) }
func TestBasicAgree(t *testing.T)      { grader.RunBasicAgree(t, mk) }
