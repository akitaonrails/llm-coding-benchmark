package grader

import (
	"testing"
	"time"

	"v41raft/harness"
)

// ---------------------------------------------------------------------------
// snapshot / compaction
// ---------------------------------------------------------------------------

// RunSnapshotBasic: with snapshotting enabled the log is compacted (persisted
// raft state stays bounded) while agreement keeps working.
func RunSnapshotBasic(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfigEx(t, 3, true, mk, harness.Config{Voters: []int{0, 1, 2}}, 10)
	defer cfg.Cleanup()
	cfg.Begin("Test: snapshot - log compaction keeps raft state bounded")
	rnd := newRand(11)

	for i := 0; i < 60; i++ {
		cfg.One(rnd.Int(), 3, true)
	}

	leader := cfg.CheckOneLeader()
	sz := cfg.RaftStateSize(leader)
	// 60 commands at interval 10 means the leader snapshots repeatedly and the
	// live log never holds more than a handful of entries; the persisted state
	// must be far smaller than it would be with no trimming.
	if sz > 8000 {
		t.Fatalf("snapshot did not compact the log: raft state size %d bytes after 60 commands", sz)
	}
	// agreement still works after all the snapshotting
	cfg.One(rnd.Int(), 3, true)
}

// RunSnapshotInstall: a follower disconnected across many commits (so the
// leader snapshots past its log) must catch up via InstallSnapshot on rejoin.
func RunSnapshotInstall(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfigEx(t, 3, true, mk, harness.Config{Voters: []int{0, 1, 2}}, 10)
	defer cfg.Cleanup()
	cfg.Begin("Test: snapshot - laggard catches up via InstallSnapshot")
	rnd := newRand(12)

	cfg.One(rnd.Int(), 3, true)

	leader := cfg.CheckOneLeader()
	victim := (leader + 1) % 3
	cfg.Disconnect(victim)

	// commit a lot with only the 2-server majority; the leader compacts past
	// where the victim's log ended.
	for i := 0; i < 50; i++ {
		cfg.One(rnd.Int(), 2, true)
	}

	cfg.Connect(victim)

	// the victim must now catch up (InstallSnapshot + tail) and the next command
	// must commit on all three.
	idx := cfg.One(rnd.Int(), 3, true)

	deadline := time.Now().Add(5 * electionTimeout)
	for time.Now().Before(deadline) {
		if cfg.AppliedIndex(victim) >= idx {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
	t.Fatalf("victim %d did not catch up via snapshot (applied %d, wanted >= %d)",
		victim, cfg.AppliedIndex(victim), idx)
}

// RunSnapshotCrash: committed state survives crash/restart when the durable
// state is a snapshot plus a tail (not a full log).
func RunSnapshotCrash(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfigEx(t, 3, true, mk, harness.Config{Voters: []int{0, 1, 2}}, 10)
	defer cfg.Cleanup()
	cfg.Begin("Test: snapshot - committed state survives crash/restart from snapshot")
	rnd := newRand(13)

	for i := 0; i < 30; i++ {
		cfg.One(rnd.Int(), 3, true)
	}

	// restart each peer in turn (restoring from its snapshot), keeping a
	// majority alive throughout.
	for i := 0; i < 3; i++ {
		cfg.Start1(i)
		cfg.Connect(i)
		cfg.One(rnd.Int(), 3, true)
	}

	// a committed entry from before the restarts is still agreed everywhere
	cfg.One(rnd.Int(), 3, true)
}

// ---------------------------------------------------------------------------
// joint-consensus membership change
// ---------------------------------------------------------------------------

// RunMembershipJoint: reconfigure (remove two voters, add two) while a
// partition is active. Joint consensus must prevent split-brain and
// committed-entry loss: the side holding only an OLD-config majority may make
// progress, but the leader that issued the change (lacking its old-config
// majority) must NOT commit, so the two sides never diverge.
func RunMembershipJoint(t *testing.T, mk harness.MakeRaftFunc) {
	// servers 0,1,2 are the initial voters; 3,4 start as spares that we add as
	// learners and promote, so the new configuration is {0,3,4}.
	cfg := harness.MakeConfigEx(t, 5, true, mk, harness.Config{Voters: []int{0, 1, 2}}, 0)
	defer cfg.Cleanup()
	cfg.Begin("Test: joint-consensus membership change under an active partition")
	rnd := newRand(14)

	// make leadership deterministic: drive the leader to server 0.
	ensureLeader(t, cfg, 0)

	// baseline committed on the old voter set {0,1,2}
	cfg.One(rnd.Int(), 3, true)

	// add 3,4 as learners and wait for them to catch up (so they already hold
	// the committed log when the real reconfiguration happens).
	if _, ok := cfg.ChangeMembershipOn(0, []int{0, 1, 2}, []int{3, 4}); !ok {
		t.Fatalf("failed to add learners 3,4")
	}
	idx := cfg.One(rnd.Int(), 3, true)
	waitApplied(t, cfg, []int{3, 4}, idx, 5*electionTimeout, "learners before reconfig")

	// Partition {1,2} | {0,3,4}; leader 0 is still (briefly) leader of the old
	// config and immediately issues the reconfiguration to {0,3,4}, removing
	// 1,2. The partition is ACTIVE during the change.
	cfg.Partition([][]int{{1, 2}, {0, 3, 4}})
	cfg.ChangeMembershipOn(0, []int{0, 3, 4}, []int{})

	// The old-config majority {1,2} keeps the cluster alive under C_old and
	// commits. (With a correct joint implementation the {0,3,4} side cannot
	// commit, because 0 lacks its OLD-config majority, so nothing diverges. A
	// non-joint implementation lets BOTH sides commit -> the harness detects a
	// conflicting commit.)
	for i := 0; i < 5; i++ {
		cfg.One(rnd.Int(), 2, true) // only {1,2} can reach agreement
	}

	// heal and make sure the whole cluster converges and keeps making progress
	cfg.Partition(nil)
	cfg.One(rnd.Int(), 2, true)
	cfg.CheckOneLeader()
}

// ---------------------------------------------------------------------------
// learners
// ---------------------------------------------------------------------------

// RunLearnerCatchup: a far-behind node added as a learner receives a snapshot,
// catches up without stalling commits, and after promotion commits continue.
// A learner must NOT be counted toward quorum before promotion.
func RunLearnerCatchup(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfigEx(t, 5, true, mk, harness.Config{Voters: []int{0, 1, 2}}, 10)
	defer cfg.Cleanup()
	cfg.Begin("Test: learner catches up via snapshot, then is promoted")
	rnd := newRand(15)

	ensureLeader(t, cfg, 0)

	// commit a lot on {0,1,2} so the leader snapshots well past index 0.
	for i := 0; i < 40; i++ {
		cfg.One(rnd.Int(), 3, true)
	}

	// add server 3 as a far-behind learner.
	if _, ok := cfg.ChangeMembershipOn(0, []int{0, 1, 2}, []int{3}); !ok {
		t.Fatalf("failed to add learner 3")
	}

	// commits must continue (the learner is not part of the quorum) while the
	// learner catches up via InstallSnapshot.
	idx := cfg.One(rnd.Int(), 3, true)
	waitApplied(t, cfg, []int{3}, idx, 6*electionTimeout, "learner catchup")

	// A learner must be EXCLUDED from quorum. Disconnect one real voter AND the
	// learner: the remaining voter majority {0,1} (of voters {0,1,2}) must
	// still commit. If the learner were counted toward quorum, the leader would
	// need three of {0,1,2,3} and stall here.
	cfg.Disconnect(2)
	cfg.Disconnect(3)
	cfg.One(rnd.Int(), 2, true)
	cfg.One(rnd.Int(), 2, true)
	cfg.Connect(2)
	cfg.Connect(3)

	// promote the learner to a voter; commits continue over the 4-voter set.
	if _, ok := cfg.ChangeMembershipOn(0, []int{0, 1, 2, 3}, []int{}); !ok {
		t.Fatalf("failed to promote learner 3")
	}
	cfg.One(rnd.Int(), 4, true)
	cfg.One(rnd.Int(), 4, true)
}

// ---------------------------------------------------------------------------
// leadership transfer
// ---------------------------------------------------------------------------

// RunLeadershipTransfer: TransferLeadership hands leadership to a named target
// via TimeoutNow, and the cluster keeps committing.
func RunLeadershipTransfer(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfigEx(t, 3, true, mk, harness.Config{Voters: []int{0, 1, 2}}, 0)
	defer cfg.Cleanup()
	cfg.Begin("Test: leadership transfer")
	rnd := newRand(16)

	cfg.One(rnd.Int(), 3, true)

	leader := cfg.CheckOneLeader()
	target := (leader + 1) % 3
	if !cfg.TransferLeadershipOn(leader, target) {
		t.Fatalf("TransferLeadership(%d -> %d) returned false", leader, target)
	}

	deadline := time.Now().Add(3 * electionTimeout)
	moved := false
	for time.Now().Before(deadline) {
		if _, isLeader := cfg.RaftState(target); isLeader {
			moved = true
			break
		}
		time.Sleep(20 * time.Millisecond)
	}
	if !moved {
		t.Fatalf("leadership did not transfer to %d", target)
	}
	if l := cfg.CheckOneLeader(); l != target {
		t.Fatalf("after transfer the leader is %d, wanted %d", l, target)
	}

	cfg.One(rnd.Int(), 3, true)
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

// ensureLeader drives leadership to want using TransferLeadership (retrying
// across elections).
func ensureLeader(t *testing.T, cfg *harness.Cluster, want int) {
	t.Helper()
	deadline := time.Now().Add(6 * electionTimeout)
	for time.Now().Before(deadline) {
		leader := cfg.CheckOneLeader()
		if leader == want {
			return
		}
		cfg.TransferLeadershipOn(leader, want)
		time.Sleep(200 * time.Millisecond)
	}
	if l := cfg.CheckOneLeader(); l != want {
		t.Fatalf("could not make %d the leader (it is %d)", want, l)
	}
}

// waitApplied waits until every server in peers has applied at least index.
func waitApplied(t *testing.T, cfg *harness.Cluster, peers []int, index int, timeout time.Duration, what string) {
	t.Helper()
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		done := true
		for _, p := range peers {
			if cfg.AppliedIndex(p) < index {
				done = false
			}
		}
		if done {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
	for _, p := range peers {
		if cfg.AppliedIndex(p) < index {
			t.Fatalf("%s: server %d did not apply index %d (at %d)", what, p, index, cfg.AppliedIndex(p))
		}
	}
}
