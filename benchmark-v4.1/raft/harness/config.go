package harness

import (
	"fmt"
	"reflect"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"v41raft/harness/labgob"
	"v41raft/harness/labrpc"
)

// ---------------------------------------------------------------------------
// Shared types (used by the reference raft, the broken variants and the grader)
// ---------------------------------------------------------------------------

// ApplyMsg is delivered on the apply channel when a log entry is committed
// (CommandValid) or a snapshot is installed (SnapshotValid). The snapshot
// fields are present for later sprints; the foundation reference only sends
// CommandValid messages.
type ApplyMsg struct {
	CommandValid bool
	Command      interface{}
	CommandIndex int
	CommandTerm  int

	SnapshotValid bool
	Snapshot      []byte
	SnapshotTerm  int
	SnapshotIndex int
}

// Config is the cluster membership a peer is created with: a set of voting
// members and a set of non-voting learners. For the foundation sprint every
// peer is a voter and Learners is empty.
type Config struct {
	Voters   []int
	Learners []int
}

// RaftNode is the slice of a raft implementation the cluster manager needs to
// drive it. The RPC handlers (RequestVote/AppendEntries/...) are discovered
// separately by labrpc via reflection on the concrete type.
type RaftNode interface {
	Start(command interface{}) (index int, term int, isLeader bool)
	GetState() (term int, isLeader bool)
	Kill()
}

// MakeRaftFunc constructs a raft peer. The grader wires the reference (or a
// broken variant) here; the cluster manager itself is implementation-agnostic.
type MakeRaftFunc func(peers []*labrpc.ClientEnd, me int, persister *Persister,
	applyCh chan ApplyMsg, initial Config) RaftNode

// ---------------------------------------------------------------------------
// Cluster manager
// ---------------------------------------------------------------------------

var seedCounter int64

// Cluster manages a simulated cluster of raft peers for a test.
type Cluster struct {
	mu          sync.Mutex
	t           *testing.T
	net         *labrpc.Network
	n           int
	mk          MakeRaftFunc
	initial     Config
	rafts       []RaftNode
	connected   []bool
	saved       []*Persister
	logs        []map[int]interface{} // per-server: applied index -> command
	lastApplied []int
	applyErr    []string
	maxIndex    int
	start       time.Time
	t0          time.Time
	finished    int32
}

// RaftElectionTimeout is the reference timescale the tests sleep against. The
// reference's own election timeout is a randomized fraction of this.
const RaftElectionTimeout = 1000 * time.Millisecond

// MakeConfig builds and starts an n-node cluster. reliable=false turns on
// drop/delay/reorder on links that are up.
func MakeConfig(t *testing.T, n int, reliable bool, mk MakeRaftFunc) *Cluster {
	labgob.Register(0)

	seed := atomic.AddInt64(&seedCounter, 1)*1_000_003 + int64(n)
	cfg := &Cluster{
		t:           t,
		net:         labrpc.MakeNetwork(seed),
		n:           n,
		mk:          mk,
		rafts:       make([]RaftNode, n),
		connected:   make([]bool, n),
		saved:       make([]*Persister, n),
		logs:        make([]map[int]interface{}, n),
		lastApplied: make([]int, n),
		applyErr:    make([]string, n),
		start:       time.Now(),
	}
	cfg.net.SetReliable(reliable)

	voters := make([]int, n)
	for i := range voters {
		voters[i] = i
	}
	cfg.initial = Config{Voters: voters}

	for i := 0; i < n; i++ {
		cfg.logs[i] = map[int]interface{}{}
		cfg.Start1(i)
	}
	for i := 0; i < n; i++ {
		cfg.Connect(i)
	}
	return cfg
}

// Start1 (re)starts peer i. On a restart it reuses the peer's durable state.
// The peer is created disconnected; callers Connect it afterwards.
func (cfg *Cluster) Start1(i int) {
	cfg.crash1(i)

	ends := make([]*labrpc.ClientEnd, cfg.n)
	for j := 0; j < cfg.n; j++ {
		ends[j] = cfg.net.MakeEnd(i, j)
	}

	cfg.mu.Lock()
	if cfg.saved[i] != nil {
		cfg.saved[i] = cfg.saved[i].Copy()
	} else {
		cfg.saved[i] = MakePersister()
	}
	persister := cfg.saved[i]
	cfg.lastApplied[i] = 0
	if cfg.logs[i] == nil {
		cfg.logs[i] = map[int]interface{}{}
	}
	cfg.mu.Unlock()

	applyCh := make(chan ApplyMsg)
	go cfg.applier(i, applyCh)

	rf := cfg.mk(ends, i, persister, applyCh, cfg.initial)

	cfg.mu.Lock()
	cfg.rafts[i] = rf
	cfg.mu.Unlock()

	svc := labrpc.MakeService(rf)
	srv := labrpc.MakeServer()
	srv.AddService(svc)
	cfg.net.AddServer(i, srv)
}

// crash1 stops peer i (if running), preserving its durable state.
func (cfg *Cluster) crash1(i int) {
	cfg.Disconnect(i)
	cfg.net.DeleteServer(i)

	cfg.mu.Lock()
	if cfg.saved[i] != nil {
		cfg.saved[i] = cfg.saved[i].Copy()
	}
	rf := cfg.rafts[i]
	cfg.rafts[i] = nil
	cfg.mu.Unlock()

	if rf != nil {
		rf.Kill()
	}
}

// Crash1 is the exported crash hook used by tests.
func (cfg *Cluster) Crash1(i int) {
	cfg.crash1(i)
}

// Connect attaches peer i to the network.
func (cfg *Cluster) Connect(i int) {
	cfg.mu.Lock()
	cfg.connected[i] = true
	cfg.mu.Unlock()
	cfg.net.Enable(i, true)
}

// Disconnect detaches peer i from the network.
func (cfg *Cluster) Disconnect(i int) {
	cfg.mu.Lock()
	cfg.connected[i] = false
	cfg.mu.Unlock()
	cfg.net.Enable(i, false)
}

// Partition splits the (enabled) peers into groups that can only talk within
// their group. Pass nil to heal.
func (cfg *Cluster) Partition(groups [][]int) {
	cfg.net.Partition(groups)
}

// SetReliable toggles link reliability mid-test.
func (cfg *Cluster) SetReliable(yes bool) {
	cfg.net.SetReliable(yes)
}

// SubmitTo calls Start on peer i (if it exists).
func (cfg *Cluster) SubmitTo(i int, cmd interface{}) (int, int, bool) {
	cfg.mu.Lock()
	rf := cfg.rafts[i]
	cfg.mu.Unlock()
	if rf == nil {
		return -1, -1, false
	}
	return rf.Start(cmd)
}

// RaftState returns peer i's (term, isLeader).
func (cfg *Cluster) RaftState(i int) (int, bool) {
	cfg.mu.Lock()
	rf := cfg.rafts[i]
	cfg.mu.Unlock()
	if rf == nil {
		return 0, false
	}
	return rf.GetState()
}

// N returns the cluster size.
func (cfg *Cluster) N() int { return cfg.n }

// Cleanup kills all peers and tears down the network.
func (cfg *Cluster) Cleanup() {
	atomic.StoreInt32(&cfg.finished, 1)
	cfg.mu.Lock()
	rafts := make([]RaftNode, cfg.n)
	copy(rafts, cfg.rafts)
	cfg.mu.Unlock()
	for _, rf := range rafts {
		if rf != nil {
			rf.Kill()
		}
	}
	cfg.net.Cleanup()
}

// Begin logs the start of a named test phase.
func (cfg *Cluster) Begin(description string) {
	cfg.t.Logf("%s ...", description)
	cfg.t0 = time.Now()
}

// applier records committed entries for peer i and checks cross-server
// consistency. Errors are recorded (not fatal from this goroutine); they are
// surfaced by NCommitted, which runs on the test goroutine.
func (cfg *Cluster) applier(i int, applyCh chan ApplyMsg) {
	for m := range applyCh {
		if !m.CommandValid {
			continue
		}
		cfg.mu.Lock()
		errMsg := ""
		for j := 0; j < cfg.n; j++ {
			if old, ok := cfg.logs[j][m.CommandIndex]; ok && !reflect.DeepEqual(old, m.Command) {
				errMsg = fmt.Sprintf("apply error: commit index=%v server=%v command=%v != server=%v command=%v",
					m.CommandIndex, i, m.Command, j, old)
			}
		}
		if m.CommandIndex != cfg.lastApplied[i]+1 {
			errMsg = fmt.Sprintf("apply error: server %v applied index %v out of order (expected %v)",
				i, m.CommandIndex, cfg.lastApplied[i]+1)
		}
		cfg.logs[i][m.CommandIndex] = m.Command
		cfg.lastApplied[i] = m.CommandIndex
		if m.CommandIndex > cfg.maxIndex {
			cfg.maxIndex = m.CommandIndex
		}
		if errMsg != "" && cfg.applyErr[i] == "" {
			cfg.applyErr[i] = errMsg
		}
		cfg.mu.Unlock()
	}
}

// NCommitted returns how many peers have applied index, plus the command. It
// fails the test if peers disagree about the command at that index.
func (cfg *Cluster) NCommitted(index int) (int, interface{}) {
	cfg.mu.Lock()
	defer cfg.mu.Unlock()
	count := 0
	var cmd interface{}
	for i := 0; i < cfg.n; i++ {
		if cfg.applyErr[i] != "" {
			cfg.t.Fatalf("%s", cfg.applyErr[i])
		}
		c, ok := cfg.logs[i][index]
		if ok {
			if count > 0 && !reflect.DeepEqual(c, cmd) {
				cfg.t.Fatalf("committed values do not match: index %v, %v != %v", index, cmd, c)
			}
			count++
			cmd = c
		}
	}
	return count, cmd
}

// One submits cmd, drives it to agreement on at least expected peers, and
// returns the committing index. With retry=false it fails on the first
// 2-second stall; with retry=true it keeps looking for a fresh leader.
func (cfg *Cluster) One(cmd interface{}, expected int, retry bool) int {
	t0 := time.Now()
	starts := 0
	for time.Since(t0) < 10*time.Second && atomic.LoadInt32(&cfg.finished) == 0 {
		index := -1
		for range cfg.n {
			starts = (starts + 1) % cfg.n
			cfg.mu.Lock()
			rf := cfg.rafts[starts]
			connected := cfg.connected[starts]
			cfg.mu.Unlock()
			if rf != nil && connected {
				idx, _, ok := rf.Start(cmd)
				if ok {
					index = idx
					break
				}
			}
		}

		if index != -1 {
			t1 := time.Now()
			for time.Since(t1) < 2*time.Second {
				nd, cmd1 := cfg.NCommitted(index)
				if nd >= expected && reflect.DeepEqual(cmd1, cmd) {
					return index
				}
				time.Sleep(20 * time.Millisecond)
			}
			if !retry {
				cfg.t.Fatalf("one(%v) failed to reach agreement", cmd)
			}
		} else {
			time.Sleep(50 * time.Millisecond)
		}
	}
	if atomic.LoadInt32(&cfg.finished) == 0 {
		cfg.t.Fatalf("one(%v) failed to reach agreement", cmd)
	}
	return -1
}

// Wait blocks until at least n peers have applied index (or the term moves
// past startTerm, if startTerm >= 0, in which case it returns nil). It fails
// the test if agreement is never reached.
func (cfg *Cluster) Wait(index int, n int, startTerm int) interface{} {
	to := 10 * time.Millisecond
	for iters := 0; iters < 30; iters++ {
		nd, _ := cfg.NCommitted(index)
		if nd >= n {
			break
		}
		time.Sleep(to)
		if to < time.Second {
			to *= 2
		}
		if startTerm > -1 {
			for i := 0; i < cfg.n; i++ {
				if t, _ := cfg.RaftState(i); t > startTerm {
					return nil
				}
			}
		}
	}
	nd, cmd := cfg.NCommitted(index)
	if nd < n {
		cfg.t.Fatalf("only %d decided for index %d; wanted %d", nd, index, n)
	}
	return cmd
}

// CheckOneLeader returns the id of the single current leader (highest term),
// failing if there are two leaders in one term or none at all.
func (cfg *Cluster) CheckOneLeader() int {
	for iters := 0; iters < 10; iters++ {
		time.Sleep(450 * time.Millisecond)
		leaders := make(map[int][]int)
		for i := 0; i < cfg.n; i++ {
			cfg.mu.Lock()
			connected := cfg.connected[i]
			rf := cfg.rafts[i]
			cfg.mu.Unlock()
			if connected && rf != nil {
				if term, isLeader := rf.GetState(); isLeader {
					leaders[term] = append(leaders[term], i)
				}
			}
		}
		lastTermWithLeader := -1
		for term, ls := range leaders {
			if len(ls) > 1 {
				cfg.t.Fatalf("term %d has %d (>1) leaders", term, len(ls))
			}
			if term > lastTermWithLeader {
				lastTermWithLeader = term
			}
		}
		if len(leaders) != 0 {
			return leaders[lastTermWithLeader][0]
		}
	}
	cfg.t.Fatalf("expected one leader, got none")
	return -1
}

// CheckTerms returns the term all connected peers agree on, failing if they
// disagree.
func (cfg *Cluster) CheckTerms() int {
	term := -1
	for i := 0; i < cfg.n; i++ {
		cfg.mu.Lock()
		connected := cfg.connected[i]
		rf := cfg.rafts[i]
		cfg.mu.Unlock()
		if connected && rf != nil {
			xterm, _ := rf.GetState()
			if term == -1 {
				term = xterm
			} else if term != xterm {
				cfg.t.Fatalf("servers disagree on term")
			}
		}
	}
	return term
}

// CheckNoLeader fails if any connected peer believes it is the leader.
func (cfg *Cluster) CheckNoLeader() {
	for i := 0; i < cfg.n; i++ {
		cfg.mu.Lock()
		connected := cfg.connected[i]
		rf := cfg.rafts[i]
		cfg.mu.Unlock()
		if connected && rf != nil {
			if _, isLeader := rf.GetState(); isLeader {
				cfg.t.Fatalf("expected no leader among connected servers, but %d claims to be leader", i)
			}
		}
	}
}
