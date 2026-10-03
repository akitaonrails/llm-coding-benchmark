// Package reference is a correct Raft implementation for the v4.1 benchmark.
//
// It implements, on top of the validated foundation (leader election with
// PreVote, log replication with the conflict-backup optimization, CheckQuorum
// step-down, and persistence of currentTerm/votedFor/log via the harness
// Persister):
//
//   - Snapshot / log compaction with a lastIncludedIndex base offset and
//     offset-aware log helpers;
//   - the InstallSnapshot RPC (bringing laggards and learners current);
//   - joint-consensus membership changes (C_old,new then C_new; quorum over
//     BOTH configurations while joint; safe under partition);
//   - learners (non-voting members that catch up via snapshot before being
//     promoted and are excluded from quorum);
//   - leadership transfer (TransferLeadership + the TimeoutNow RPC).
//
// It is the grader's "sound" reference: wired into the grader it must pass the
// entire gauntlet under -race, repeatably.
package staleindex

import (
	"bytes"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"

	"v41raft/harness"
	"v41raft/harness/labgob"
	"v41raft/harness/labrpc"
)

type raftState int

const (
	follower raftState = iota
	candidate
	leader
)

// Timing. The reference election timeout is a randomized fraction of the
// harness RaftElectionTimeout so distinct peers rarely time out together.
const (
	tickInterval         = 20 * time.Millisecond
	heartbeatInterval    = 100 * time.Millisecond
	electionTimeoutMinMS = 400
	electionTimeoutMaxMS = 800
	// A leader that has not heard from a majority within this window steps
	// down (CheckQuorum). It is comfortably larger than a heartbeat and on the
	// order of one election timeout.
	quorumCheckTimeout = 1000 * time.Millisecond
	// A leader is considered "still alive" (and pre-votes against it refused)
	// if we heard from it within this window.
	leaderAliveWindow = electionTimeoutMinMS * time.Millisecond
)

// ConfigState is a cluster configuration recorded in the log by a membership
// change. During a joint-consensus transition Joint is true and OldVoters holds
// the outgoing voter set; agreement then requires a majority of BOTH Voters and
// OldVoters. It is also delivered to the application as the Command of a
// configuration log entry (so every server observes the transition at the same
// log index) and is stored as the base configuration of a snapshot.
type ConfigState struct {
	Voters    []int
	OldVoters []int
	Learners  []int
	Joint     bool
}

// LogEntry is one replicated command. If Config is non-nil the entry is a
// membership-change entry (its Command is still delivered, carrying the
// ConfigState, so the application's apply bookkeeping stays contiguous).
type LogEntry struct {
	Term    int
	Command interface{}
	Config  *ConfigState
}

// Raft is a single peer.
type Raft struct {
	mu        sync.Mutex
	peers     []*labrpc.ClientEnd
	persister *harness.Persister
	me        int
	dead      int32

	// persistent state
	currentTerm int
	votedFor    int // -1 == none
	// log uses slice-index == (raft-index - lastIncludedIndex). log[0] is a
	// sentinel whose Term is lastIncludedTerm and whose raft-index is
	// lastIncludedIndex. Entries strictly after the snapshot follow.
	log               []LogEntry
	lastIncludedIndex int
	lastIncludedTerm  int
	baseConfig        ConfigState // configuration as of lastIncludedIndex
	snapshot          []byte      // the application snapshot bytes (mirrors persister)

	// volatile state
	state       raftState
	commitIndex int
	lastApplied int // highest index delivered on applyCh

	// leader volatile state
	nextIndex   []int
	matchIndex  []int
	lastContact []time.Time // last time a reply was received from each peer

	// active membership (recomputed from baseConfig + log)
	voters    []int
	oldVoters []int // non-nil while joint
	learners  []int
	joint     bool
	isVoter   map[int]bool
	isLearner map[int]bool

	// in-flight joint transition the leader must finalize (jointIndex is the
	// log index of the C_old,new entry; -1 when none is pending).
	jointIndex int

	// leadership transfer target (-1 == none)
	transferee int

	// election timing
	electionDeadline time.Time
	lastHeartbeat    time.Time
	// lastLeaderContact is updated ONLY by a successful AppendEntries, so a
	// node that is itself campaigning will still grant a pre-vote to a peer.
	lastLeaderContact time.Time

	applyCh         chan harness.ApplyMsg
	applyCond       *sync.Cond
	snapshotToApply *harness.ApplyMsg // a snapshot waiting to be delivered in order
	killedCh        chan struct{}
	killOnce        sync.Once

	rng *rand.Rand
}

var makeCounterMu sync.Mutex
var makeCounter int64

// Make creates a peer. It returns immediately; background goroutines drive
// elections, replication and application.
func Make(peers []*labrpc.ClientEnd, me int, persister *harness.Persister,
	applyCh chan harness.ApplyMsg, initial harness.Config) *Raft {

	labgob.Register(0)
	labgob.Register(ConfigState{})

	makeCounterMu.Lock()
	makeCounter++
	seed := int64(me)*2_654_435_761 + makeCounter*1_000_003
	makeCounterMu.Unlock()

	rf := &Raft{
		peers:       peers,
		persister:   persister,
		me:          me,
		currentTerm: 0,
		votedFor:    -1,
		log:         []LogEntry{{Term: 0}},
		state:       follower,
		applyCh:     applyCh,
		killedCh:    make(chan struct{}),
		rng:         rand.New(rand.NewSource(seed)),
		isVoter:     map[int]bool{},
		isLearner:   map[int]bool{},
		jointIndex:  -1,
		transferee:  -1,
	}
	rf.applyCond = sync.NewCond(&rf.mu)

	// Seed the base configuration from the initial membership. If no voters are
	// specified every peer is a voter (foundation behaviour).
	bv := append([]int(nil), initial.Voters...)
	if len(bv) == 0 {
		for i := range peers {
			bv = append(bv, i)
		}
	}
	rf.baseConfig = ConfigState{Voters: bv, Learners: append([]int(nil), initial.Learners...)}

	rf.nextIndex = make([]int, len(peers))
	rf.matchIndex = make([]int, len(peers))
	rf.lastContact = make([]time.Time, len(peers))

	rf.readPersist(persister.ReadRaftState())
	rf.snapshot = persister.ReadSnapshot()
	rf.commitIndex = rf.lastIncludedIndex
	rf.lastApplied = rf.lastIncludedIndex
	rf.recomputeConfigLocked()
	rf.resetElectionTimer()

	go rf.ticker()
	go rf.applier()

	return rf
}

// ---------------------------------------------------------------------------
// persistence
// ---------------------------------------------------------------------------

func (rf *Raft) encodeStateLocked() []byte {
	buf := new(bytes.Buffer)
	enc := labgob.NewEncoder(buf)
	_ = enc.Encode(rf.currentTerm)
	_ = enc.Encode(rf.votedFor)
	_ = enc.Encode(rf.lastIncludedIndex)
	_ = enc.Encode(rf.lastIncludedTerm)
	_ = enc.Encode(rf.log)
	_ = enc.Encode(rf.baseConfig)
	return buf.Bytes()
}

// persist writes raft state and the current snapshot atomically. Normal state
// changes re-save the existing snapshot bytes unchanged.
func (rf *Raft) persist() {
	rf.persister.SaveStateAndSnapshot(rf.encodeStateLocked(), rf.snapshot)
}

func (rf *Raft) readPersist(data []byte) {
	if len(data) == 0 {
		return
	}
	dec := labgob.NewDecoder(bytes.NewBuffer(data))
	var currentTerm, votedFor, lii, lit int
	var log []LogEntry
	var base ConfigState
	if dec.Decode(&currentTerm) != nil || dec.Decode(&votedFor) != nil ||
		dec.Decode(&lii) != nil || dec.Decode(&lit) != nil ||
		dec.Decode(&log) != nil || dec.Decode(&base) != nil {
		return
	}
	rf.currentTerm = currentTerm
	rf.votedFor = votedFor
	rf.lastIncludedIndex = lii
	rf.lastIncludedTerm = lit
	rf.log = log
	rf.baseConfig = base
}

// ---------------------------------------------------------------------------
// offset-aware log helpers (caller holds rf.mu)
// ---------------------------------------------------------------------------

func (rf *Raft) lastLogIndex() int { return rf.lastIncludedIndex + len(rf.log) - 1 }
func (rf *Raft) lastLogTerm() int  { return rf.log[len(rf.log)-1].Term }

// termAt returns the term of the entry at raft-index i (which must be >=
// lastIncludedIndex and <= lastLogIndex), or -1 if out of range.
func (rf *Raft) termAt(i int) int {
	pos := i - rf.lastIncludedIndex
	if pos < 0 || pos >= len(rf.log) {
		return -1
	}
	return rf.log[pos].Term
}

// entriesFrom returns a fresh copy of the entries at raft-index i onward. i must
// be > lastIncludedIndex.
func (rf *Raft) entriesFrom(i int) []LogEntry {
	pos := i - rf.lastIncludedIndex
	out := make([]LogEntry, len(rf.log)-pos)
	copy(out, rf.log[pos:])
	return out
}

// ---------------------------------------------------------------------------
// membership
// ---------------------------------------------------------------------------

// recomputeConfigLocked derives the active configuration from the base config
// (as of the snapshot) plus the last configuration entry in the log.
func (rf *Raft) recomputeConfigLocked() {
	cfg := rf.baseConfig
	for i := 1; i < len(rf.log); i++ {
		if rf.log[i].Config != nil {
			cfg = *rf.log[i].Config
		}
	}
	rf.applyConfigLocked(cfg)
}

func (rf *Raft) applyConfigLocked(cfg ConfigState) {
	rf.voters = append([]int(nil), cfg.Voters...)
	rf.oldVoters = append([]int(nil), cfg.OldVoters...)
	rf.learners = append([]int(nil), cfg.Learners...)
	rf.joint = cfg.Joint
	rf.isVoter = map[int]bool{}
	for _, v := range rf.voters {
		rf.isVoter[v] = true
	}
	if rf.joint {
		for _, v := range rf.oldVoters {
			rf.isVoter[v] = true // old voters still vote/count while joint
		}
	}
	rf.isLearner = map[int]bool{}
	for _, l := range rf.learners {
		rf.isLearner[l] = true
	}
}

// configAsOfLocked returns the active configuration as of raft-index idx.
func (rf *Raft) configAsOfLocked(idx int) ConfigState {
	cfg := rf.baseConfig
	for i := 1; i < len(rf.log); i++ {
		if rf.lastIncludedIndex+i > idx {
			break
		}
		if rf.log[i].Config != nil {
			cfg = *rf.log[i].Config
		}
	}
	return cfg
}

// replicationTargetsLocked is every peer the leader must replicate to: the
// union of the (new and old) voter sets and the learner set, excluding self.
func (rf *Raft) replicationTargetsLocked() []int {
	seen := map[int]bool{rf.me: true}
	out := []int{}
	add := func(s []int) {
		for _, p := range s {
			if !seen[p] {
				seen[p] = true
				out = append(out, p)
			}
		}
	}
	add(rf.voters)
	add(rf.oldVoters)
	add(rf.learners)
	return out
}

// isAgreedLocked reports whether pred holds for a majority of the current voter
// set — and, while joint, also for a majority of the old voter set.
func (rf *Raft) isAgreedLocked(pred func(int) bool) bool {
	major := func(set []int) bool {
		c := 0
		for _, p := range set {
			if pred(p) {
				c++
			}
		}
		return c >= len(set)/2+1
	}
	if !rf.joint {
		return major(rf.voters)
	}
	return major(rf.voters) && major(rf.oldVoters)
}

// ---------------------------------------------------------------------------
// public API
// ---------------------------------------------------------------------------

// GetState returns the peer's current term and whether it believes it is leader.
func (rf *Raft) GetState() (int, bool) {
	rf.mu.Lock()
	defer rf.mu.Unlock()
	return rf.currentTerm, rf.state == leader
}

// Start proposes a command. If this peer is not the leader it returns false.
func (rf *Raft) Start(command interface{}) (int, int, bool) {
	rf.mu.Lock()
	if rf.state != leader || rf.killed() {
		term := rf.currentTerm
		rf.mu.Unlock()
		return -1, term, false
	}
	index := rf.appendEntryLocked(LogEntry{Term: rf.currentTerm, Command: command})
	term := rf.currentTerm
	rf.mu.Unlock()

	rf.broadcastAppendEntries()
	return index, term, true
}

// appendEntryLocked appends one entry, updates leader bookkeeping, recomputes
// membership if it is a config entry, and persists. Returns the new index.
func (rf *Raft) appendEntryLocked(e LogEntry) int {
	rf.log = append(rf.log, e)
	index := rf.lastLogIndex()
	rf.matchIndex[rf.me] = index
	rf.nextIndex[rf.me] = index + 1
	if e.Config != nil {
		rf.recomputeConfigLocked()
	}
	rf.persist()
	return index
}

// Snapshot trims the log up to (and including) index, keeping index as the new
// base. snapshot is the application state as of index.
func (rf *Raft) Snapshot(index int, snapshot []byte) {
	rf.mu.Lock()
	defer rf.mu.Unlock()
	if index <= rf.lastIncludedIndex || index > rf.lastLogIndex() {
		return
	}
	newBaseTerm := rf.termAt(index)
	newBase := rf.configAsOfLocked(index)

	suffix := rf.entriesFrom(index + 1) // entries strictly after index
	newLog := make([]LogEntry, 1, 1+len(suffix))
	newLog[0] = LogEntry{Term: newBaseTerm}
	newLog = append(newLog, suffix...)

	rf.log = newLog
	// BUG (staleindex): the log is trimmed but the base offset is NOT advanced
	// (rf.lastIncludedIndex stays behind). Every offset-aware helper
	// (lastLogIndex/termAt/entriesFrom) now computes raft indices that are off
	// by the number of trimmed entries, so replication and commit break after
	// the first snapshot. A correct implementation advances lastIncludedIndex
	// to index here.
	// rf.lastIncludedIndex = index  // <-- the missing base-offset fix
	rf.lastIncludedTerm = newBaseTerm
	rf.baseConfig = newBase
	rf.snapshot = snapshot
	rf.persist()
}

// Kill permanently stops the peer's goroutines.
func (rf *Raft) Kill() {
	atomic.StoreInt32(&rf.dead, 1)
	rf.killOnce.Do(func() { close(rf.killedCh) })
	rf.mu.Lock()
	rf.applyCond.Broadcast()
	rf.mu.Unlock()
}

func (rf *Raft) killed() bool {
	return atomic.LoadInt32(&rf.dead) == 1
}

// ---------------------------------------------------------------------------
// election timing helpers (caller holds rf.mu)
// ---------------------------------------------------------------------------

func (rf *Raft) randomTimeout() time.Duration {
	ms := electionTimeoutMinMS + rf.rng.Intn(electionTimeoutMaxMS-electionTimeoutMinMS)
	return time.Duration(ms) * time.Millisecond
}

func (rf *Raft) resetElectionTimer() {
	rf.electionDeadline = time.Now().Add(rf.randomTimeout())
}

// becomeFollower converts to follower, adopting term if it is higher.
func (rf *Raft) becomeFollower(term int) {
	rf.state = follower
	rf.transferee = -1
	if term > rf.currentTerm {
		rf.currentTerm = term
		rf.votedFor = -1
		rf.persist()
	}
	rf.resetElectionTimer()
}

// upToDate reports whether a candidate's log is at least as up-to-date as ours.
func (rf *Raft) upToDate(lastIndex, lastTerm int) bool {
	myTerm := rf.lastLogTerm()
	myIndex := rf.lastLogIndex()
	if lastTerm != myTerm {
		return lastTerm > myTerm
	}
	return lastIndex >= myIndex
}

// ---------------------------------------------------------------------------
// RequestVote (two-phase: PreVote then real vote)
// ---------------------------------------------------------------------------

type RequestVoteArgs struct {
	Term         int
	CandidateId  int
	LastLogIndex int
	LastLogTerm  int
	PreVote      bool
	Force        bool // leadership transfer: bypass the leader-alive pre-vote gate
}

type RequestVoteReply struct {
	Term        int
	VoteGranted bool
}

// RequestVote is the RPC handler.
func (rf *Raft) RequestVote(args *RequestVoteArgs, reply *RequestVoteReply) {
	rf.mu.Lock()
	defer rf.mu.Unlock()

	reply.VoteGranted = false
	reply.Term = rf.currentTerm

	if args.Term < rf.currentTerm {
		return
	}

	if args.PreVote {
		// A live leader never grants a pre-vote: it knows it is still serving,
		// so it must quench a disruptive campaign rather than help depose
		// itself. (A leader does not receive AppendEntries, so its own
		// lastLeaderContact is always stale; without this guard a rejoining
		// node could win a pre-vote on the leader's own grant.)
		if rf.state == leader {
			return
		}
		// Otherwise grant a pre-vote only if the prospective term is not behind
		// us, the candidate's log is up-to-date, AND (unless this is a forced
		// transfer probe) we have not heard from a leader within an election
		// timeout.
		if args.Term >= rf.currentTerm &&
			rf.upToDate(args.LastLogIndex, args.LastLogTerm) &&
			(args.Force || time.Since(rf.lastLeaderContact) >= leaderAliveWindow) {
			reply.VoteGranted = true
		}
		return
	}

	if args.Term > rf.currentTerm {
		rf.currentTerm = args.Term
		rf.votedFor = -1
		rf.state = follower
		rf.transferee = -1
		rf.persist()
		reply.Term = rf.currentTerm
	}

	if (rf.votedFor == -1 || rf.votedFor == args.CandidateId) &&
		rf.upToDate(args.LastLogIndex, args.LastLogTerm) {
		rf.votedFor = args.CandidateId
		rf.persist()
		reply.VoteGranted = true
		rf.resetElectionTimer()
	}
}

func (rf *Raft) sendRequestVote(peer int, args *RequestVoteArgs, reply *RequestVoteReply) bool {
	return rf.peers[peer].Call("Raft.RequestVote", args, reply)
}

// ---------------------------------------------------------------------------
// elections
// ---------------------------------------------------------------------------

func (rf *Raft) ticker() {
	for !rf.killed() {
		time.Sleep(tickInterval)

		rf.mu.Lock()
		switch rf.state {
		case leader:
			rf.lastContact[rf.me] = time.Now()
			// A leader removed from the configuration steps down.
			if !rf.isVoter[rf.me] {
				rf.becomeFollower(rf.currentTerm)
				rf.mu.Unlock()
				continue
			}
			doHeartbeat := time.Since(rf.lastHeartbeat) >= heartbeatInterval
			if doHeartbeat {
				rf.lastHeartbeat = time.Now()
			}
			if !rf.hasQuorumContactLocked() {
				// CheckQuorum: a leader that cannot reach a majority relinquishes
				// leadership so a minority partition cannot keep a stale leader.
				rf.becomeFollower(rf.currentTerm)
				rf.mu.Unlock()
				continue
			}
			rf.maybeFinalizeJointLocked()
			rf.mu.Unlock()
			if doHeartbeat {
				rf.broadcastAppendEntries()
			}
		default:
			timedOut := time.Now().After(rf.electionDeadline)
			canVote := rf.isVoter[rf.me]
			rf.mu.Unlock()
			if timedOut && canVote {
				rf.startElection(false)
			}
		}
	}
}

// hasQuorumContactLocked reports whether the leader has heard from a majority
// of voters (itself included) within quorumCheckTimeout.
func (rf *Raft) hasQuorumContactLocked() bool {
	now := time.Now()
	return rf.isAgreedLocked(func(p int) bool {
		if p == rf.me {
			return true
		}
		return !rf.lastContact[p].IsZero() && now.Sub(rf.lastContact[p]) < quorumCheckTimeout
	})
}

// startElection runs a PreVote round (unless forced) and, if it wins, a real
// election.
func (rf *Raft) startElection(forced bool) {
	rf.mu.Lock()
	if rf.state == leader || rf.killed() || !rf.isVoter[rf.me] {
		rf.mu.Unlock()
		return
	}
	rf.resetElectionTimer()
	prospectiveTerm := rf.currentTerm + 1
	startTerm := rf.currentTerm
	lastIndex := rf.lastLogIndex()
	lastTerm := rf.lastLogTerm()
	rf.mu.Unlock()

	if !forced {
		won, higher := rf.collectVotes(true, false, prospectiveTerm, lastIndex, lastTerm)
		rf.mu.Lock()
		if higher > rf.currentTerm {
			rf.becomeFollower(higher)
			rf.mu.Unlock()
			return
		}
		if !won || rf.state == leader || rf.currentTerm != startTerm || rf.killed() {
			rf.mu.Unlock()
			return
		}
		rf.mu.Unlock()
	}

	// --- real election ---
	rf.mu.Lock()
	if rf.state == leader || rf.killed() || rf.currentTerm != startTerm {
		rf.mu.Unlock()
		return
	}
	rf.currentTerm++
	rf.state = candidate
	rf.votedFor = rf.me
	rf.persist()
	rf.resetElectionTimer()
	term := rf.currentTerm
	lastIndex = rf.lastLogIndex()
	lastTerm = rf.lastLogTerm()
	rf.mu.Unlock()

	won, higher := rf.collectVotes(false, forced, term, lastIndex, lastTerm)
	rf.mu.Lock()
	defer rf.mu.Unlock()
	if higher > rf.currentTerm {
		rf.becomeFollower(higher)
		return
	}
	if won && rf.state == candidate && rf.currentTerm == term && !rf.killed() {
		rf.becomeLeaderLocked()
	}
}

// collectVotes sends RequestVote to every other voter and reports whether a
// (joint-aware) majority granted, plus the highest term seen in any reply.
func (rf *Raft) collectVotes(preVote, force bool, term, lastIndex, lastTerm int) (bool, int) {
	rf.mu.Lock()
	peers := []int{}
	seen := map[int]bool{rf.me: true}
	for _, set := range [][]int{rf.voters, rf.oldVoters} {
		for _, v := range set {
			if !seen[v] {
				seen[v] = true
				peers = append(peers, v)
			}
		}
	}
	rf.mu.Unlock()

	type res struct {
		peer  int
		ok    bool
		reply RequestVoteReply
	}
	ch := make(chan res, len(peers))
	for _, p := range peers {
		go func(p int) {
			args := &RequestVoteArgs{
				Term:         term,
				CandidateId:  rf.me,
				LastLogIndex: lastIndex,
				LastLogTerm:  lastTerm,
				PreVote:      preVote,
				Force:        force,
			}
			var reply RequestVoteReply
			ok := rf.sendRequestVote(p, args, &reply)
			ch <- res{p, ok, reply}
		}(p)
	}

	granted := map[int]bool{rf.me: true}
	higher := 0
	for range peers {
		r := <-ch
		if !r.ok {
			continue
		}
		if r.reply.VoteGranted {
			granted[r.peer] = true
		} else if r.reply.Term > higher {
			higher = r.reply.Term
		}
	}

	rf.mu.Lock()
	won := rf.isAgreedLocked(func(p int) bool { return granted[p] })
	rf.mu.Unlock()
	return won, higher
}

// becomeLeaderLocked initializes leader state and fires an immediate heartbeat.
func (rf *Raft) becomeLeaderLocked() {
	rf.state = leader
	rf.transferee = -1
	last := rf.lastLogIndex()
	now := time.Now()
	for i := range rf.peers {
		rf.nextIndex[i] = last + 1
		rf.matchIndex[i] = 0
		rf.lastContact[i] = now // grace period before any CheckQuorum step-down
	}
	rf.matchIndex[rf.me] = last
	rf.lastHeartbeat = now
	// If we inherited an unfinished joint transition, remember to finalize it.
	rf.jointIndex = -1
	if rf.joint {
		for i := len(rf.log) - 1; i >= 1; i-- {
			if rf.log[i].Config != nil {
				if rf.log[i].Config.Joint {
					rf.jointIndex = rf.lastIncludedIndex + i
				}
				break
			}
		}
	}
	go rf.broadcastAppendEntries()
}

// ---------------------------------------------------------------------------
// membership change (joint consensus) + leadership transfer
// ---------------------------------------------------------------------------

// ChangeMembership begins a joint-consensus transition to the given voter and
// learner sets. It appends a C_old,new entry immediately; once that commits the
// leader appends the final C_new entry. Returns the joint entry's index.
func (rf *Raft) ChangeMembership(newVoters []int, newLearners []int) (int, bool) {
	rf.mu.Lock()
	defer rf.mu.Unlock()
	if rf.state != leader || rf.killed() {
		return -1, false
	}
	if rf.joint || rf.jointIndex >= 0 {
		return -1, false // a transition is already in progress
	}
	joint := &ConfigState{
		Voters:    append([]int(nil), newVoters...),
		OldVoters: append([]int(nil), rf.voters...),
		Learners:  append([]int(nil), newLearners...),
		Joint:     true,
	}
	index := rf.appendEntryLocked(LogEntry{Term: rf.currentTerm, Command: *joint, Config: joint})
	rf.jointIndex = index
	go rf.broadcastAppendEntries()
	return index, true
}

// maybeFinalizeJointLocked appends the final C_new entry once the joint entry
// has committed.
func (rf *Raft) maybeFinalizeJointLocked() {
	if rf.state != leader || rf.jointIndex < 0 || rf.commitIndex < rf.jointIndex {
		return
	}
	// read the joint entry's target configuration
	if rf.jointIndex <= rf.lastIncludedIndex || rf.jointIndex > rf.lastLogIndex() {
		rf.jointIndex = -1
		return
	}
	jc := rf.log[rf.jointIndex-rf.lastIncludedIndex].Config
	if jc == nil {
		rf.jointIndex = -1
		return
	}
	final := &ConfigState{
		Voters:   append([]int(nil), jc.Voters...),
		Learners: append([]int(nil), jc.Learners...),
		Joint:    false,
	}
	rf.appendEntryLocked(LogEntry{Term: rf.currentTerm, Command: *final, Config: final})
	rf.jointIndex = -1
	go rf.broadcastAppendEntries()
}

type TimeoutNowArgs struct {
	Term     int
	LeaderId int
}
type TimeoutNowReply struct {
	Term int
}

// TransferLeadership makes target the leader: it catches target up and then
// sends it a TimeoutNow so it immediately starts a (forced) election.
func (rf *Raft) TransferLeadership(target int) bool {
	rf.mu.Lock()
	if rf.state != leader || rf.killed() || target == rf.me || !rf.isVoter[target] {
		rf.mu.Unlock()
		return false
	}
	rf.transferee = target
	rf.mu.Unlock()

	deadline := time.Now().Add(3 * harness.RaftElectionTimeout)
	for time.Now().Before(deadline) {
		rf.mu.Lock()
		if rf.state != leader || rf.killed() {
			rf.mu.Unlock()
			return false
		}
		caught := rf.matchIndex[target] >= rf.lastLogIndex()
		term := rf.currentTerm
		rf.mu.Unlock()
		if caught {
			args := &TimeoutNowArgs{Term: term, LeaderId: rf.me}
			var reply TimeoutNowReply
			if rf.peers[target].Call("Raft.TimeoutNow", args, &reply) {
				return true
			}
			return false
		}
		go rf.sendAppendEntriesTo(target)
		time.Sleep(20 * time.Millisecond)
	}
	return false
}

// TimeoutNow forces the recipient to start an immediate election (bypassing the
// PreVote leader-alive gate), used for leadership transfer.
func (rf *Raft) TimeoutNow(args *TimeoutNowArgs, reply *TimeoutNowReply) {
	rf.mu.Lock()
	reply.Term = rf.currentTerm
	if args.Term < rf.currentTerm || rf.killed() || !rf.isVoter[rf.me] || rf.state == leader {
		rf.mu.Unlock()
		return
	}
	rf.mu.Unlock()
	go rf.startElection(true)
}

// ---------------------------------------------------------------------------
// AppendEntries (heartbeat + replication + commit + backup optimization)
// ---------------------------------------------------------------------------

type AppendEntriesArgs struct {
	Term         int
	LeaderId     int
	PrevLogIndex int
	PrevLogTerm  int
	Entries      []LogEntry
	LeaderCommit int
}

type AppendEntriesReply struct {
	Term          int
	Success       bool
	ConflictTerm  int
	ConflictIndex int
}

// AppendEntries is the RPC handler.
func (rf *Raft) AppendEntries(args *AppendEntriesArgs, reply *AppendEntriesReply) {
	rf.mu.Lock()
	defer rf.mu.Unlock()

	reply.Success = false
	reply.Term = rf.currentTerm
	reply.ConflictTerm = -1
	reply.ConflictIndex = -1

	if args.Term < rf.currentTerm {
		return
	}

	if args.Term > rf.currentTerm {
		rf.currentTerm = args.Term
		rf.votedFor = -1
	}
	rf.state = follower
	rf.transferee = -1
	rf.resetElectionTimer()
	rf.lastLeaderContact = time.Now()
	reply.Term = rf.currentTerm

	// If the leader's prev is behind our snapshot, skip the covered entries.
	if args.PrevLogIndex < rf.lastIncludedIndex {
		skip := rf.lastIncludedIndex - args.PrevLogIndex
		if skip <= len(args.Entries) {
			args.Entries = args.Entries[skip:]
			args.PrevLogIndex = rf.lastIncludedIndex
			args.PrevLogTerm = rf.lastIncludedTerm
		} else {
			// everything the leader sent is already in our snapshot
			reply.Success = true
			rf.maybeAdvanceCommitFromLeader(args.LeaderCommit)
			return
		}
	}

	if args.PrevLogIndex > rf.lastLogIndex() {
		reply.ConflictIndex = rf.lastLogIndex() + 1
		reply.ConflictTerm = -1
		return
	}
	if rf.termAt(args.PrevLogIndex) != args.PrevLogTerm {
		ct := rf.termAt(args.PrevLogIndex)
		reply.ConflictTerm = ct
		i := args.PrevLogIndex
		for i > rf.lastIncludedIndex+1 && rf.termAt(i-1) == ct {
			i--
		}
		reply.ConflictIndex = i
		return
	}

	// Splice in new entries, truncating only on an actual term conflict.
	changed := false
	for i, e := range args.Entries {
		idx := args.PrevLogIndex + 1 + i
		pos := idx - rf.lastIncludedIndex
		if pos < len(rf.log) {
			if rf.log[pos].Term != e.Term {
				rf.log = append(rf.log[:pos], args.Entries[i:]...)
				changed = true
				break
			}
		} else {
			rf.log = append(rf.log, args.Entries[i:]...)
			changed = true
			break
		}
	}
	if changed {
		rf.recomputeConfigLocked()
	}
	rf.persist()
	rf.maybeAdvanceCommitFromLeader(args.LeaderCommit)
	reply.Success = true
}

func (rf *Raft) maybeAdvanceCommitFromLeader(leaderCommit int) {
	if leaderCommit > rf.commitIndex {
		rf.commitIndex = min(leaderCommit, rf.lastLogIndex())
		rf.applyCond.Broadcast()
	}
}

func (rf *Raft) broadcastAppendEntries() {
	rf.mu.Lock()
	if rf.state != leader {
		rf.mu.Unlock()
		return
	}
	rf.lastContact[rf.me] = time.Now()
	peers := rf.replicationTargetsLocked()
	rf.mu.Unlock()

	for _, p := range peers {
		go rf.sendAppendEntriesTo(p)
	}
}

func (rf *Raft) sendAppendEntriesTo(peer int) {
	rf.mu.Lock()
	if rf.state != leader {
		rf.mu.Unlock()
		return
	}
	// If the peer needs entries we have already snapshotted away, install the
	// snapshot instead.
	if rf.nextIndex[peer] <= rf.lastIncludedIndex {
		rf.mu.Unlock()
		rf.sendInstallSnapshotTo(peer)
		return
	}
	term := rf.currentTerm
	ni := rf.nextIndex[peer]
	if ni < rf.lastIncludedIndex+1 {
		ni = rf.lastIncludedIndex + 1
	}
	prevIndex := ni - 1
	prevTerm := rf.termAt(prevIndex)
	entries := rf.entriesFrom(ni)
	args := &AppendEntriesArgs{
		Term:         term,
		LeaderId:     rf.me,
		PrevLogIndex: prevIndex,
		PrevLogTerm:  prevTerm,
		Entries:      entries,
		LeaderCommit: rf.commitIndex,
	}
	rf.mu.Unlock()

	var reply AppendEntriesReply
	if !rf.peers[peer].Call("Raft.AppendEntries", args, &reply) {
		return
	}

	rf.mu.Lock()
	defer rf.mu.Unlock()
	if rf.state != leader || rf.currentTerm != term {
		return
	}
	if reply.Term > rf.currentTerm {
		rf.becomeFollower(reply.Term)
		return
	}
	rf.lastContact[peer] = time.Now()

	if reply.Success {
		newMatch := prevIndex + len(entries)
		if newMatch > rf.matchIndex[peer] {
			rf.matchIndex[peer] = newMatch
		}
		rf.nextIndex[peer] = rf.matchIndex[peer] + 1
		rf.advanceCommitLocked()
		return
	}

	// Conflict: use the backup hints to jump nextIndex.
	if reply.ConflictTerm == -1 {
		rf.nextIndex[peer] = reply.ConflictIndex
	} else {
		lastIdx := -1
		for i := rf.lastLogIndex(); i > rf.lastIncludedIndex; i-- {
			if rf.termAt(i) == reply.ConflictTerm {
				lastIdx = i
				break
			}
		}
		if lastIdx >= 0 {
			rf.nextIndex[peer] = lastIdx + 1
		} else {
			rf.nextIndex[peer] = reply.ConflictIndex
		}
	}
	if rf.nextIndex[peer] < 1 {
		rf.nextIndex[peer] = 1
	}
	go rf.sendAppendEntriesTo(peer)
}

// advanceCommitLocked advances commitIndex to the highest N replicated on a
// (joint-aware) majority whose entry is from the current term.
func (rf *Raft) advanceCommitLocked() {
	for n := rf.lastLogIndex(); n > rf.commitIndex; n-- {
		if rf.termAt(n) != rf.currentTerm {
			continue
		}
		if rf.isAgreedLocked(func(p int) bool { return rf.matchIndex[p] >= n }) {
			rf.commitIndex = n
			rf.applyCond.Broadcast()
			rf.maybeFinalizeJointLocked()
			return
		}
	}
}

// ---------------------------------------------------------------------------
// InstallSnapshot
// ---------------------------------------------------------------------------

type InstallSnapshotArgs struct {
	Term              int
	LeaderId          int
	LastIncludedIndex int
	LastIncludedTerm  int
	BaseConfig        ConfigState
	Data              []byte
}

type InstallSnapshotReply struct {
	Term int
}

func (rf *Raft) sendInstallSnapshotTo(peer int) {
	rf.mu.Lock()
	if rf.state != leader {
		rf.mu.Unlock()
		return
	}
	args := &InstallSnapshotArgs{
		Term:              rf.currentTerm,
		LeaderId:          rf.me,
		LastIncludedIndex: rf.lastIncludedIndex,
		LastIncludedTerm:  rf.lastIncludedTerm,
		BaseConfig:        rf.baseConfig,
		Data:              rf.snapshot,
	}
	term := rf.currentTerm
	rf.mu.Unlock()

	var reply InstallSnapshotReply
	if !rf.peers[peer].Call("Raft.InstallSnapshot", args, &reply) {
		return
	}

	rf.mu.Lock()
	defer rf.mu.Unlock()
	if rf.state != leader || rf.currentTerm != term {
		return
	}
	if reply.Term > rf.currentTerm {
		rf.becomeFollower(reply.Term)
		return
	}
	rf.lastContact[peer] = time.Now()
	if args.LastIncludedIndex > rf.matchIndex[peer] {
		rf.matchIndex[peer] = args.LastIncludedIndex
	}
	if rf.nextIndex[peer] < args.LastIncludedIndex+1 {
		rf.nextIndex[peer] = args.LastIncludedIndex + 1
	}
	rf.advanceCommitLocked()
}

// InstallSnapshot is the RPC handler.
func (rf *Raft) InstallSnapshot(args *InstallSnapshotArgs, reply *InstallSnapshotReply) {
	rf.mu.Lock()
	defer rf.mu.Unlock()

	reply.Term = rf.currentTerm
	if args.Term < rf.currentTerm {
		return
	}
	if args.Term > rf.currentTerm {
		rf.currentTerm = args.Term
		rf.votedFor = -1
	}
	rf.state = follower
	rf.transferee = -1
	rf.resetElectionTimer()
	rf.lastLeaderContact = time.Now()
	reply.Term = rf.currentTerm

	// Ignore a stale snapshot.
	if args.LastIncludedIndex <= rf.lastIncludedIndex || args.LastIncludedIndex <= rf.commitIndex {
		return
	}

	// Keep any suffix we already have past the snapshot point.
	if args.LastIncludedIndex < rf.lastLogIndex() &&
		rf.termAt(args.LastIncludedIndex) == args.LastIncludedTerm {
		suffix := rf.entriesFrom(args.LastIncludedIndex + 1)
		newLog := make([]LogEntry, 1, 1+len(suffix))
		newLog[0] = LogEntry{Term: args.LastIncludedTerm}
		newLog = append(newLog, suffix...)
		rf.log = newLog
	} else {
		rf.log = []LogEntry{{Term: args.LastIncludedTerm}}
	}

	rf.lastIncludedIndex = args.LastIncludedIndex
	rf.lastIncludedTerm = args.LastIncludedTerm
	rf.baseConfig = args.BaseConfig
	rf.snapshot = args.Data
	if rf.commitIndex < args.LastIncludedIndex {
		rf.commitIndex = args.LastIncludedIndex
	}
	if rf.lastApplied < args.LastIncludedIndex {
		rf.lastApplied = args.LastIncludedIndex
	}
	rf.recomputeConfigLocked()
	rf.persist()

	rf.snapshotToApply = &harness.ApplyMsg{
		SnapshotValid: true,
		Snapshot:      args.Data,
		SnapshotIndex: args.LastIncludedIndex,
		SnapshotTerm:  args.LastIncludedTerm,
	}
	rf.applyCond.Broadcast()
}

// ---------------------------------------------------------------------------
// applier
// ---------------------------------------------------------------------------

func (rf *Raft) applier() {
	for {
		rf.mu.Lock()
		for rf.snapshotToApply == nil && rf.commitIndex <= rf.lastApplied && !rf.killed() {
			rf.applyCond.Wait()
		}
		if rf.killed() {
			rf.mu.Unlock()
			return
		}

		if rf.snapshotToApply != nil {
			msg := *rf.snapshotToApply
			rf.snapshotToApply = nil
			if rf.lastApplied < msg.SnapshotIndex {
				rf.lastApplied = msg.SnapshotIndex
			}
			rf.mu.Unlock()
			select {
			case rf.applyCh <- msg:
			case <-rf.killedCh:
				return
			}
			continue
		}

		if rf.lastApplied < rf.lastIncludedIndex {
			rf.lastApplied = rf.lastIncludedIndex
		}
		var msgs []harness.ApplyMsg
		for rf.lastApplied < rf.commitIndex {
			rf.lastApplied++
			if rf.lastApplied <= rf.lastIncludedIndex {
				continue
			}
			e := rf.log[rf.lastApplied-rf.lastIncludedIndex]
			cmd := e.Command
			if e.Config != nil {
				cmd = *e.Config
			}
			msgs = append(msgs, harness.ApplyMsg{
				CommandValid: true,
				Command:      cmd,
				CommandIndex: rf.lastApplied,
				CommandTerm:  e.Term,
			})
		}
		rf.mu.Unlock()

		for _, m := range msgs {
			select {
			case rf.applyCh <- m:
			case <-rf.killedCh:
				return
			}
		}
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
