// Package grader holds the foundation-sprint grader tests.
//
// The test LOGIC lives here as exported Run* functions parameterized by a
// harness.MakeRaftFunc, so it can be run against either the correct reference
// (the SOUND check, in raft_fdn_test.go) or a deliberately-broken variant (the
// SENSITIVE / proven-negative checks, in reference/broken/*). This keeps a
// single source of truth for each scenario.
package grader

import (
	"math/rand"
	"sync"
	"testing"
	"time"

	"v41raft/harness"
)

const electionTimeout = harness.RaftElectionTimeout

// deterministic per-test command source, so command values are reproducible.
func newRand(tag int64) *rand.Rand { return rand.New(rand.NewSource(0x5eed*tag + 1)) }

// RunInitialElection: exactly one leader, stable, with a settled term.
func RunInitialElection(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: initial election")

	cfg.CheckOneLeader()

	time.Sleep(50 * time.Millisecond)
	term1 := cfg.CheckTerms()
	if term1 < 1 {
		t.Fatalf("term is %d, should be at least 1", term1)
	}

	// With a stable leader the term should not keep advancing.
	time.Sleep(2 * electionTimeout)
	term2 := cfg.CheckTerms()
	if term1 != term2 {
		t.Logf("warning: term changed even though there were no failures (%d -> %d)", term1, term2)
	}

	cfg.CheckOneLeader()
}

// RunReElection: a new leader appears when the old one fails, and no leader
// exists without a quorum.
func RunReElection(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: re-election after leader failure")

	leader1 := cfg.CheckOneLeader()

	cfg.Disconnect(leader1)
	cfg.CheckOneLeader()

	// old leader rejoins; must not disturb the new leader
	cfg.Connect(leader1)
	leader2 := cfg.CheckOneLeader()

	// no quorum => no leader
	cfg.Disconnect(leader2)
	cfg.Disconnect((leader2 + 1) % 3)
	time.Sleep(2 * electionTimeout)
	cfg.CheckNoLeader()

	// quorum restored => a leader returns
	cfg.Connect((leader2 + 1) % 3)
	cfg.CheckOneLeader()

	cfg.Connect(leader2)
	cfg.CheckOneLeader()
}

// RunPreVote: isolate a follower (its term would inflate WITHOUT PreVote);
// when it rejoins it must NOT depose the stable leader nor bump the term.
func RunPreVote(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: PreVote - rejoining node must not disrupt a stable leader")

	leader := cfg.CheckOneLeader()
	term := cfg.CheckTerms()

	follower := (leader + 1) % 3
	cfg.Disconnect(follower)

	// Let the isolated node sit for several election timeouts. Without PreVote
	// it would repeatedly time out and inflate its term.
	time.Sleep(4 * electionTimeout)

	if l := cfg.CheckOneLeader(); l != leader {
		t.Fatalf("leader changed (%d -> %d) while a follower was merely isolated", leader, l)
	}

	cfg.Connect(follower)
	time.Sleep(2 * electionTimeout)

	l2 := cfg.CheckOneLeader()
	if l2 != leader {
		t.Fatalf("PreVote failed: a rejoining node deposed the leader (%d -> %d)", leader, l2)
	}
	term2 := cfg.CheckTerms()
	if term2 != term {
		t.Fatalf("PreVote failed: term advanced on rejoin (%d -> %d) => the rejoining node disrupted the cluster", term, term2)
	}
}

// RunCheckQuorum: a leader partitioned into a minority must step down, and the
// majority must elect a replacement.
func RunCheckQuorum(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 5, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: CheckQuorum - minority-partitioned leader steps down")

	leader := cfg.CheckOneLeader()

	minorityPeer := (leader + 1) % 5
	minority := []int{leader, minorityPeer}
	majority := []int{}
	for i := 0; i < 5; i++ {
		if i != leader && i != minorityPeer {
			majority = append(majority, i)
		}
	}
	cfg.Partition([][]int{minority, majority})

	deadline := time.Now().Add(4 * electionTimeout)
	stepped := false
	for time.Now().Before(deadline) {
		if _, isLeader := cfg.RaftState(leader); !isLeader {
			stepped = true
			break
		}
		time.Sleep(50 * time.Millisecond)
	}
	if !stepped {
		t.Fatalf("CheckQuorum failed: minority-partitioned leader %d did not step down", leader)
	}

	// the majority side must have a (single) leader
	time.Sleep(2 * electionTimeout)
	cfg.CheckOneLeader()

	cfg.Partition(nil)
	cfg.CheckOneLeader()
}

// RunBasicAgree: simple replication with everyone up.
func RunBasicAgree(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: basic agreement")

	iters := 3
	for index := 1; index <= iters; index++ {
		nd, _ := cfg.NCommitted(index)
		if nd > 0 {
			t.Fatalf("some peers committed before Start()")
		}
		xindex := cfg.One(index*100, 3, false)
		if xindex != index {
			t.Fatalf("got index %d but expected %d", xindex, index)
		}
	}
}

// RunFailAgree: agreement continues while a minority is disconnected.
func RunFailAgree(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: agreement despite a follower disconnect")

	cfg.One(101, 3, false)

	leader := cfg.CheckOneLeader()
	cfg.Disconnect((leader + 1) % 3)

	// the remaining majority (2 of 3) must still agree
	cfg.One(102, 2, false)
	cfg.One(103, 2, false)
	time.Sleep(electionTimeout)
	cfg.One(104, 2, false)
	cfg.One(105, 2, false)

	cfg.Connect((leader + 1) % 3)

	cfg.One(106, 3, true)
	time.Sleep(electionTimeout)
	cfg.One(107, 3, true)
}

// RunFailNoAgree: no progress without a majority; the local proposal must NOT
// commit.
func RunFailNoAgree(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 5, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: no agreement without a majority")

	cfg.One(10, 5, false)

	leader := cfg.CheckOneLeader()
	cfg.Disconnect((leader + 1) % 5)
	cfg.Disconnect((leader + 2) % 5)
	cfg.Disconnect((leader + 3) % 5)

	index, _, ok := cfg.SubmitTo(leader, 20)
	if !ok {
		t.Fatalf("leader rejected Start()")
	}
	if index != 2 {
		t.Fatalf("expected index 2, got %d", index)
	}

	time.Sleep(2 * electionTimeout)

	n, _ := cfg.NCommitted(index)
	if n > 0 {
		t.Fatalf("%d committed without a majority", n)
	}

	cfg.Connect((leader + 1) % 5)
	cfg.Connect((leader + 2) % 5)
	cfg.Connect((leader + 3) % 5)

	leader2 := cfg.CheckOneLeader()
	index2, _, ok2 := cfg.SubmitTo(leader2, 30)
	if !ok2 {
		t.Fatalf("leader2 rejected Start()")
	}
	if index2 < 2 || index2 > 3 {
		t.Fatalf("unexpected index %d", index2)
	}

	cfg.One(1000, 5, true)
}

// RunConcurrentStarts: many concurrent proposals under one leader all commit
// at distinct, consistent indices.
func RunConcurrentStarts(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: concurrent Start()s")

	success := false
loop:
	for try := 0; try < 5; try++ {
		if try > 0 {
			time.Sleep(3 * time.Second)
		}

		leader := cfg.CheckOneLeader()
		_, term, ok := cfg.SubmitTo(leader, 1)
		if !ok {
			continue // leader moved; retry
		}

		iters := 5
		var wg sync.WaitGroup
		is := make(chan int, iters)
		for ii := 0; ii < iters; ii++ {
			wg.Add(1)
			go func(ii int) {
				defer wg.Done()
				i, term1, ok := cfg.SubmitTo(leader, 100+ii)
				if term1 != term || !ok {
					return
				}
				is <- i
			}(ii)
		}
		wg.Wait()
		close(is)

		for j := 0; j < cfg.N(); j++ {
			if t2, _ := cfg.RaftState(j); t2 != term {
				continue loop // term changed; retry
			}
		}

		cmds := []int{}
		for index := range is {
			cmd := cfg.Wait(index, cfg.N(), term)
			if cmd == nil {
				continue loop // term moved on during Wait; retry
			}
			if ci, ok := cmd.(int); ok {
				cmds = append(cmds, ci)
			} else {
				t.Fatalf("value %v is not an int", cmd)
			}
		}

		for ii := 0; ii < iters; ii++ {
			x := 100 + ii
			found := false
			for _, c := range cmds {
				if c == x {
					found = true
				}
			}
			if !found {
				t.Fatalf("cmd %d missing from committed set %v", x, cmds)
			}
		}
		success = true
		break
	}
	if !success {
		t.Fatalf("term changed too often to test concurrent Start()s")
	}
}

// RunRejoin: a deposed leader's uncommitted tail is overwritten on rejoin.
func RunRejoin(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: rejoin of a partitioned leader")

	cfg.One(101, 3, true)

	leader1 := cfg.CheckOneLeader()
	cfg.Disconnect(leader1)

	// these go only to the old, isolated leader and must never commit
	cfg.SubmitTo(leader1, 102)
	cfg.SubmitTo(leader1, 103)
	cfg.SubmitTo(leader1, 104)

	cfg.One(103, 2, true)

	leader2 := cfg.CheckOneLeader()
	cfg.Disconnect(leader2)

	cfg.Connect(leader1)
	cfg.One(104, 2, true)

	cfg.Connect(leader2)
	cfg.One(105, 3, true)
}

// RunBackup: heavy log divergence that forces the backup/conflict optimization
// to resolve quickly.
func RunBackup(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 5, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: leader backs up quickly over incorrect follower logs")
	rnd := newRand(7)

	cfg.One(rnd.Int(), 5, true)

	// leader1 + one follower vs the other three (isolated)
	leader1 := cfg.CheckOneLeader()
	cfg.Disconnect((leader1 + 2) % 5)
	cfg.Disconnect((leader1 + 3) % 5)
	cfg.Disconnect((leader1 + 4) % 5)

	// pile up entries on the minority side: they cannot commit
	for i := 0; i < 50; i++ {
		cfg.SubmitTo(leader1, rnd.Int())
	}
	time.Sleep(electionTimeout / 2)

	cfg.Disconnect((leader1 + 0) % 5)
	cfg.Disconnect((leader1 + 1) % 5)

	// the other three form a majority and make real progress
	cfg.Connect((leader1 + 2) % 5)
	cfg.Connect((leader1 + 3) % 5)
	cfg.Connect((leader1 + 4) % 5)
	for i := 0; i < 50; i++ {
		cfg.One(rnd.Int(), 3, true)
	}

	// now a new minority partition with lots of uncommitted entries
	leader2 := cfg.CheckOneLeader()
	other := (leader1 + 2) % 5
	if leader2 == other {
		other = (leader1 + 3) % 5
	}
	cfg.Disconnect(other)
	for i := 0; i < 50; i++ {
		cfg.SubmitTo(leader2, rnd.Int())
	}
	time.Sleep(electionTimeout / 2)

	// bring the whole cluster back to a majority that holds the committed log
	for i := 0; i < 5; i++ {
		cfg.Disconnect(i)
	}
	cfg.Connect((leader1 + 0) % 5)
	cfg.Connect((leader1 + 1) % 5)
	cfg.Connect(other)
	for i := 0; i < 50; i++ {
		cfg.One(rnd.Int(), 3, true)
	}

	for i := 0; i < 5; i++ {
		cfg.Connect(i)
	}
	cfg.One(rnd.Int(), 5, true)
}

// RunPersist1: committed entries survive a crash/restart of the whole cluster.
func RunPersist1(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: basic persistence")

	cfg.One(11, 3, true)

	for i := 0; i < 3; i++ {
		cfg.Start1(i)
	}
	for i := 0; i < 3; i++ {
		cfg.Disconnect(i)
		cfg.Connect(i)
	}

	cfg.One(12, 3, true)

	leader1 := cfg.CheckOneLeader()
	cfg.Disconnect(leader1)
	cfg.Start1(leader1)
	cfg.Connect(leader1)

	cfg.One(13, 3, true)

	leader2 := cfg.CheckOneLeader()
	cfg.Disconnect(leader2)
	cfg.One(14, 2, true)
	cfg.Start1(leader2)
	cfg.Connect(leader2)

	cfg.Wait(4, 3, -1) // wait for leader2 to rejoin before killing the next one

	i3 := (cfg.CheckOneLeader() + 1) % 3
	cfg.Disconnect(i3)
	cfg.One(15, 2, true)
	cfg.Start1(i3)
	cfg.Connect(i3)

	cfg.One(16, 3, true)
}

// RunPersist2: repeated crash/restart cycles with rotating partitions.
func RunPersist2(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 5, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: more persistence")

	index := 1
	for iters := 0; iters < 5; iters++ {
		cfg.One(10+index, 5, true)
		index++

		leader1 := cfg.CheckOneLeader()

		cfg.Disconnect((leader1 + 1) % 5)
		cfg.Disconnect((leader1 + 2) % 5)

		cfg.One(10+index, 3, true)
		index++

		cfg.Disconnect((leader1 + 0) % 5)
		cfg.Disconnect((leader1 + 3) % 5)
		cfg.Disconnect((leader1 + 4) % 5)

		cfg.Start1((leader1 + 1) % 5)
		cfg.Start1((leader1 + 2) % 5)
		cfg.Connect((leader1 + 1) % 5)
		cfg.Connect((leader1 + 2) % 5)

		time.Sleep(electionTimeout)

		cfg.Start1((leader1 + 3) % 5)
		cfg.Connect((leader1 + 3) % 5)

		cfg.Connect((leader1 + 0) % 5)
		cfg.Connect((leader1 + 4) % 5)
	}

	cfg.One(1000, 5, true)
}

// RunPersist3: crash of two of three while a disconnect is in effect.
func RunPersist3(t *testing.T, mk harness.MakeRaftFunc) {
	cfg := harness.MakeConfig(t, 3, true, mk)
	defer cfg.Cleanup()
	cfg.Begin("Test: partitioned leader and one follower crash, leader restarts")

	cfg.One(101, 3, true)

	leader := cfg.CheckOneLeader()
	cfg.Disconnect((leader + 2) % 3)

	cfg.One(102, 2, true)

	cfg.Crash1((leader + 0) % 3)
	cfg.Crash1((leader + 1) % 3)
	cfg.Connect((leader + 2) % 3)
	cfg.Start1((leader + 0) % 3)
	cfg.Connect((leader + 0) % 3)

	cfg.One(103, 2, true)

	cfg.Start1((leader + 1) % 3)
	cfg.Connect((leader + 1) % 3)

	cfg.One(104, 3, true)
}
