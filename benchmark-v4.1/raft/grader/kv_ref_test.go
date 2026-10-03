package grader

import (
	"testing"

	"v41raft/harness"
	"v41raft/harness/labrpc"
	"v41raft/kvraft"
)

// refKVImpl wires the reference KV server + clerk into the parameterized KV
// suite (the SOUND check). The broken variants supply their own KVImpl.
var refKVImpl = KVImpl{
	MakeServer: func(servers []*labrpc.ClientEnd, me int, persister *harness.Persister,
		maxraftstate int, initial harness.Config) KVServerHandle {
		return kvraft.StartKVServer(servers, me, persister, maxraftstate, initial)
	},
	MakeClerk: func(ends []*labrpc.ClientEnd) KVClerk {
		return kvraft.MakeClerk(ends)
	},
}

func TestKVBasic(t *testing.T)        { RunKVBasic(t, refKVImpl) }
func TestKVConcurrent(t *testing.T)   { RunKVConcurrent(t, refKVImpl) }
func TestKVPartition(t *testing.T)    { RunKVPartition(t, refKVImpl) }
func TestKVSnapshotSize(t *testing.T) { RunKVSnapshotSize(t, refKVImpl) }
func TestKVLinearizable(t *testing.T) { RunKVLinearizable(t, refKVImpl) }
