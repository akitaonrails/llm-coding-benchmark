package grader

import (
	"testing"

	"v41raft/harness"
	"v41raft/harness/labrpc"
	"v41raft/reference"
)

// refMake adapts the concrete reference.Make into a harness.MakeRaftFunc. The
// returned *reference.Raft satisfies harness.RaftNode, and labrpc discovers its
// RPC handlers (RequestVote/AppendEntries/...) by reflection on the concrete
// type, so the interface need only expose Start/GetState/Kill.
func refMake(peers []*labrpc.ClientEnd, me int, persister *harness.Persister,
	applyCh chan harness.ApplyMsg, initial harness.Config) harness.RaftNode {
	return reference.Make(peers, me, persister, applyCh, initial)
}

func TestInitialElection(t *testing.T)  { RunInitialElection(t, refMake) }
func TestReElection(t *testing.T)       { RunReElection(t, refMake) }
func TestPreVote(t *testing.T)          { RunPreVote(t, refMake) }
func TestCheckQuorum(t *testing.T)      { RunCheckQuorum(t, refMake) }
func TestBasicAgree(t *testing.T)       { RunBasicAgree(t, refMake) }
func TestFailAgree(t *testing.T)        { RunFailAgree(t, refMake) }
func TestFailNoAgree(t *testing.T)      { RunFailNoAgree(t, refMake) }
func TestConcurrentStarts(t *testing.T) { RunConcurrentStarts(t, refMake) }
func TestRejoin(t *testing.T)           { RunRejoin(t, refMake) }
func TestBackup(t *testing.T)           { RunBackup(t, refMake) }
func TestPersist1(t *testing.T)         { RunPersist1(t, refMake) }
func TestPersist2(t *testing.T)         { RunPersist2(t, refMake) }
func TestPersist3(t *testing.T)         { RunPersist3(t, refMake) }
