// Proven-negative test for the "noprevote" broken variant.
//
// Injected bug: the PreVote round is skipped; a real election bumps the term.
//
// Expectation when run with `go test`:
//   - the targeted test(s) below FAIL (the grader is SENSITIVE to this bug);
//   - the control tests PASS (the bug is targeted, not a blanket breakage).
package noprevote

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

// TARGET: with no PreVote an isolated node inflates its term and deposes the
// stable leader on rejoin -> TestPreVote fails.
func TestPreVote(t *testing.T) { grader.RunPreVote(t, mk) }

// --- controls: these must still PASS, proving the bug is targeted ---
func TestInitialElection(t *testing.T) { grader.RunInitialElection(t, mk) }
func TestBasicAgree(t *testing.T)      { grader.RunBasicAgree(t, mk) }
