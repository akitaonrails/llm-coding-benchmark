// Proven-negative test for the "nodedup" broken KV variant.
//
// Injected bug: the KV server applies every Put/Append with no at-most-once
// (client-id, seq) filtering. When a client retries an Append whose reply was
// lost, the value is appended twice, which no linearization can explain.
//
// Expectation: TestKVLinearizable FAILS; the reliable-network controls PASS.
package nodedup

import (
	"testing"

	"v41raft/harness"
	"v41raft/harness/labrpc"

	grader "v41raft/grader"
)

var impl = grader.KVImpl{
	MakeServer: func(servers []*labrpc.ClientEnd, me int, persister *harness.Persister,
		maxraftstate int, initial harness.Config) grader.KVServerHandle {
		return StartKVServer(servers, me, persister, maxraftstate, initial)
	},
	MakeClerk: func(ends []*labrpc.ClientEnd) grader.KVClerk {
		return MakeClerk(ends)
	},
}

// TARGET: duplicate Appends under an unreliable network are non-linearizable.
func TestKVLinearizable(t *testing.T) { grader.RunKVLinearizable(t, impl) }

// --- controls (reliable network, no retries -> no duplicates): must PASS ---
func TestKVBasic(t *testing.T)      { grader.RunKVBasic(t, impl) }
func TestKVConcurrent(t *testing.T) { grader.RunKVConcurrent(t, impl) }
