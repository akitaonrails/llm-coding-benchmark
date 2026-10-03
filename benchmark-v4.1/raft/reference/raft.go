// Package reference is a correct Raft implementation for the v4.1 foundation
// sprint: leader election with PreVote, log replication with the conflict
// backup optimization, CheckQuorum step-down, and persistence of
// currentTerm/votedFor/log via the harness Persister.
//
// Snapshot / membership-change / learner / leadership-transfer methods are
// present as compiling stubs; they are the next sprint's work.
//
// It is the grader's "sound" reference: wired into the grader it must pass the
// entire foundation gauntlet under -race, repeatably.
package reference

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
	tickInterval      = 20 * time.Millisecond
	heartbeatInterval = 100 * time.Millisecond
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

// LogEntry is one replicated command. Index equals the entry's position in the
// in-memory log slice (index 0 is a zero-term sentinel); no snapshot trimming
// happens in the foundation sprint.
type LogEntry struct {
	Term    int
	Command interface{}
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
	log         []LogEntry

	// volatile state
	state       raftState
	commitIndex int
	lastApplied int

	// leader volatile state
	nextIndex   []int
	matchIndex  []int
	lastContact []time.Time // last time a reply was received from each peer

	// membership (foundation: all voters)
	voters   []int
	isVoter  map[int]bool

	// election timing
	electionDeadline time.Time
	lastHeartbeat    time.Time
	// lastLeaderContact is the last time we heard from a valid leader. It is
	// updated ONLY by a successful AppendEntries, never by our own election
	// attempts, so a node that is itself campaigning will still grant a
	// pre-vote to a peer. The PreVote grant gate uses this (not the election
	// deadline) to decide whether a leader is still considered alive.
	lastLeaderContact time.Time

	applyCh   chan harness.ApplyMsg
	applyCond *sync.Cond
	killedCh  chan struct{}
	killOnce  sync.Once

	rng *rand.Rand
}

var makeCounterMu sync.Mutex
var makeCounter int64

// Make creates a peer. It returns immediately; background goroutines drive
// elections, replication and application.
func Make(peers []*labrpc.ClientEnd, me int, persister *harness.Persister,
	applyCh chan harness.ApplyMsg, initial harness.Config) *Raft {

	labgob.Register(0)

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
	}
	rf.applyCond = sync.NewCond(&rf.mu)

	rf.voters = append(rf.voters, initial.Voters...)
	if len(rf.voters) == 0 {
		for i := range peers {
			rf.voters = append(rf.voters, i)
		}
	}
	for _, v := range rf.voters {
		rf.isVoter[v] = true
	}

	rf.nextIndex = make([]int, len(peers))
	rf.matchIndex = make([]int, len(peers))
	rf.lastContact = make([]time.Time, len(peers))

	rf.readPersist(persister.ReadRaftState())
	rf.resetElectionTimer()

	go rf.ticker()
	go rf.applier()

	return rf
}

// ---------------------------------------------------------------------------
// persistence
// ---------------------------------------------------------------------------

func (rf *Raft) persist() {
	buf := new(bytes.Buffer)
	enc := labgob.NewEncoder(buf)
	_ = enc.Encode(rf.currentTerm)
	_ = enc.Encode(rf.votedFor)
	_ = enc.Encode(rf.log)
	rf.persister.SaveRaftState(buf.Bytes())
}

func (rf *Raft) readPersist(data []byte) {
	if len(data) == 0 {
		return
	}
	dec := labgob.NewDecoder(bytes.NewBuffer(data))
	var currentTerm, votedFor int
	var log []LogEntry
	if dec.Decode(&currentTerm) != nil || dec.Decode(&votedFor) != nil || dec.Decode(&log) != nil {
		return
	}
	rf.currentTerm = currentTerm
	rf.votedFor = votedFor
	rf.log = log
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
// Otherwise it appends the command and returns the index it will occupy.
func (rf *Raft) Start(command interface{}) (int, int, bool) {
	rf.mu.Lock()
	if rf.state != leader || rf.killed() {
		term := rf.currentTerm
		rf.mu.Unlock()
		return -1, term, false
	}
	index := len(rf.log)
	rf.log = append(rf.log, LogEntry{Term: rf.currentTerm, Command: command})
	rf.matchIndex[rf.me] = index
	rf.nextIndex[rf.me] = index + 1
	rf.persist()
	term := rf.currentTerm
	rf.mu.Unlock()

	rf.broadcastAppendEntries()
	return index, term, true
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

func (rf *Raft) quorum() int {
	return len(rf.voters)/2 + 1
}

// becomeFollower converts to follower, adopting term if it is higher.
// Caller holds rf.mu.
func (rf *Raft) becomeFollower(term int) {
	rf.state = follower
	if term > rf.currentTerm {
		rf.currentTerm = term
		rf.votedFor = -1
		rf.persist()
	}
	rf.resetElectionTimer()
}

func (rf *Raft) lastLogIndex() int { return len(rf.log) - 1 }
func (rf *Raft) lastLogTerm() int  { return rf.log[len(rf.log)-1].Term }

// upToDate reports whether a candidate's log (described by lastIndex/lastTerm)
// is at least as up-to-date as ours. Caller holds rf.mu.
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

// RequestVoteArgs carries a PreVote flag. A PreVote request never mutates the
// voter's term or votedFor; it is a pure "would you vote for me?" probe.
type RequestVoteArgs struct {
	Term         int
	CandidateId  int
	LastLogIndex int
	LastLogTerm  int
	PreVote      bool
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
		// Grant a pre-vote only if the candidate's prospective term is not
		// behind us, its log is up-to-date, AND we have not heard from a
		// leader within an election timeout. The last clause is what makes
		// PreVote actually prevent disruption: a follower currently hearing
		// heartbeats will refuse, so a partitioned-then-rejoined node cannot
		// start a real election against a healthy leader.
		if args.Term >= rf.currentTerm &&
			rf.upToDate(args.LastLogIndex, args.LastLogTerm) &&
			time.Since(rf.lastLeaderContact) >= leaderAliveWindow {
			reply.VoteGranted = true
		}
		// NB: reply.Term stays as our currentTerm; nothing is persisted.
		return
	}

	// Real vote: a higher term forces us to step down first.
	if args.Term > rf.currentTerm {
		rf.currentTerm = args.Term
		rf.votedFor = -1
		rf.state = follower
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
			doHeartbeat := time.Since(rf.lastHeartbeat) >= heartbeatInterval
			if doHeartbeat {
				rf.lastHeartbeat = time.Now()
			}
			lostQuorum := !rf.hasQuorumContactLocked()
			if lostQuorum {
				// CheckQuorum: a leader that cannot reach a majority relinquishes
				// leadership so a minority partition cannot keep a stale leader.
				rf.becomeFollower(rf.currentTerm)
				rf.mu.Unlock()
				continue
			}
			rf.mu.Unlock()
			if doHeartbeat {
				rf.broadcastAppendEntries()
			}
		default:
			timedOut := time.Now().After(rf.electionDeadline)
			rf.mu.Unlock()
			if timedOut {
				rf.startElection()
			}
		}
	}
}

// hasQuorumContactLocked reports whether the leader has heard from a majority
// of voters (itself included) within quorumCheckTimeout. Caller holds rf.mu.
func (rf *Raft) hasQuorumContactLocked() bool {
	now := time.Now()
	count := 0
	for _, v := range rf.voters {
		if v == rf.me {
			count++
			continue
		}
		if !rf.lastContact[v].IsZero() && now.Sub(rf.lastContact[v]) < quorumCheckTimeout {
			count++
		}
	}
	return count >= rf.quorum()
}

// startElection runs a PreVote round and, if it wins, a real election.
func (rf *Raft) startElection() {
	rf.mu.Lock()
	if rf.state == leader || rf.killed() {
		rf.mu.Unlock()
		return
	}
	rf.resetElectionTimer()
	prospectiveTerm := rf.currentTerm + 1
	startTerm := rf.currentTerm
	lastIndex := rf.lastLogIndex()
	lastTerm := rf.lastLogTerm()
	rf.mu.Unlock()

	// --- PreVote phase: no term bump, no persisted state change ---
	won, higher := rf.collectVotes(true, prospectiveTerm, lastIndex, lastTerm)
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
	// --- real election: now bump the term and vote for ourselves ---
	rf.currentTerm++
	rf.state = candidate
	rf.votedFor = rf.me
	rf.persist()
	rf.resetElectionTimer()
	term := rf.currentTerm
	lastIndex = rf.lastLogIndex()
	lastTerm = rf.lastLogTerm()
	rf.mu.Unlock()

	won, higher = rf.collectVotes(false, term, lastIndex, lastTerm)
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

// collectVotes sends RequestVote to every other voter and tallies grants. It
// returns whether a majority (self included) granted, and the highest term
// seen in any reply.
func (rf *Raft) collectVotes(preVote bool, term, lastIndex, lastTerm int) (bool, int) {
	type res struct {
		ok    bool
		reply RequestVoteReply
	}
	peers := make([]int, 0, len(rf.voters))
	for _, v := range rf.voters {
		if v != rf.me {
			peers = append(peers, v)
		}
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
			}
			var reply RequestVoteReply
			ok := rf.sendRequestVote(p, args, &reply)
			ch <- res{ok, reply}
		}(p)
	}

	votes := 1 // self
	higher := 0
	for range peers {
		r := <-ch
		if !r.ok {
			continue
		}
		if r.reply.VoteGranted {
			votes++
		} else if r.reply.Term > higher {
			higher = r.reply.Term
		}
	}
	return votes >= rf.quorum(), higher
}

// becomeLeaderLocked initializes leader state and fires an immediate heartbeat.
// Caller holds rf.mu.
func (rf *Raft) becomeLeaderLocked() {
	rf.state = leader
	last := rf.lastLogIndex()
	now := time.Now()
	for i := range rf.peers {
		rf.nextIndex[i] = last + 1
		rf.matchIndex[i] = 0
		rf.lastContact[i] = now // grace period before any CheckQuorum step-down
	}
	rf.matchIndex[rf.me] = last
	rf.lastHeartbeat = now
	go rf.broadcastAppendEntries()
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
	Term    int
	Success bool
	// Backup (fast conflict) optimization fields.
	ConflictTerm  int // term of the conflicting entry, or -1 if the log is too short
	ConflictIndex int // first index of ConflictTerm, or the follower's log length
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

	// Valid leader for a term >= ours: adopt its term and reset our timer.
	if args.Term > rf.currentTerm {
		rf.currentTerm = args.Term
		rf.votedFor = -1
	}
	rf.state = follower
	rf.resetElectionTimer()
	rf.lastLeaderContact = time.Now()
	reply.Term = rf.currentTerm

	// Consistency check at PrevLogIndex.
	if args.PrevLogIndex > rf.lastLogIndex() {
		reply.ConflictIndex = len(rf.log) // we are too short; skip ahead to our end
		reply.ConflictTerm = -1
		rf.persist()
		return
	}
	if args.PrevLogIndex >= 0 && rf.log[args.PrevLogIndex].Term != args.PrevLogTerm {
		reply.ConflictTerm = rf.log[args.PrevLogIndex].Term
		// first index with that term
		i := args.PrevLogIndex
		for i > 0 && rf.log[i-1].Term == reply.ConflictTerm {
			i--
		}
		reply.ConflictIndex = i
		rf.persist()
		return
	}

	// Splice in the new entries, truncating only on an actual conflict.
	for i, e := range args.Entries {
		idx := args.PrevLogIndex + 1 + i
		if idx < len(rf.log) {
			if rf.log[idx].Term != e.Term {
				rf.log = rf.log[:idx]
				rf.log = append(rf.log, args.Entries[i:]...)
				break
			}
		} else {
			rf.log = append(rf.log, args.Entries[i:]...)
			break
		}
	}
	rf.persist()

	if args.LeaderCommit > rf.commitIndex {
		rf.commitIndex = min(args.LeaderCommit, rf.lastLogIndex())
		rf.applyCond.Broadcast()
	}

	reply.Success = true
}

func (rf *Raft) broadcastAppendEntries() {
	rf.mu.Lock()
	if rf.state != leader {
		rf.mu.Unlock()
		return
	}
	rf.lastContact[rf.me] = time.Now()
	peers := make([]int, 0, len(rf.voters))
	for _, v := range rf.voters {
		if v != rf.me {
			peers = append(peers, v)
		}
	}
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
	term := rf.currentTerm
	ni := rf.nextIndex[peer]
	if ni < 1 {
		ni = 1
	}
	prevIndex := ni - 1
	prevTerm := rf.log[prevIndex].Term
	entries := make([]LogEntry, len(rf.log)-ni)
	copy(entries, rf.log[ni:])
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

	// A reply (success or not) proves we reached this peer: it counts for
	// CheckQuorum.
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

	// Conflict: use the backup hints to jump nextIndex instead of decrementing
	// by one.
	if reply.ConflictTerm == -1 {
		rf.nextIndex[peer] = reply.ConflictIndex
	} else {
		lastIdx := -1
		for i := rf.lastLogIndex(); i >= 1; i-- {
			if rf.log[i].Term == reply.ConflictTerm {
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
	// retry quickly so divergent logs converge within the test budget
	go rf.sendAppendEntriesTo(peer)
}

// advanceCommitLocked advances commitIndex to the highest N replicated on a
// majority whose entry is from the current term. Caller holds rf.mu.
func (rf *Raft) advanceCommitLocked() {
	for n := rf.lastLogIndex(); n > rf.commitIndex; n-- {
		if rf.log[n].Term != rf.currentTerm {
			continue
		}
		count := 0
		for _, v := range rf.voters {
			if rf.matchIndex[v] >= n {
				count++
			}
		}
		if count >= rf.quorum() {
			rf.commitIndex = n
			rf.applyCond.Broadcast()
			return
		}
	}
}

// ---------------------------------------------------------------------------
// applier
// ---------------------------------------------------------------------------

func (rf *Raft) applier() {
	for {
		rf.mu.Lock()
		for rf.commitIndex <= rf.lastApplied && !rf.killed() {
			rf.applyCond.Wait()
		}
		if rf.killed() {
			rf.mu.Unlock()
			return
		}
		var msgs []harness.ApplyMsg
		for rf.lastApplied < rf.commitIndex {
			rf.lastApplied++
			e := rf.log[rf.lastApplied]
			msgs = append(msgs, harness.ApplyMsg{
				CommandValid: true,
				Command:      e.Command,
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

// ---------------------------------------------------------------------------
// next-sprint stubs (compile only)
// ---------------------------------------------------------------------------

// Snapshot trims the log up to index. Not implemented in the foundation sprint.
func (rf *Raft) Snapshot(index int, snapshot []byte) {}

// InstallSnapshotArgs/Reply + handler: stubbed for the next sprint.
type InstallSnapshotArgs struct {
	Term              int
	LeaderId          int
	LastIncludedIndex int
	LastIncludedTerm  int
	Data              []byte
}
type InstallSnapshotReply struct {
	Term int
}

// InstallSnapshot is a stub; it just reports our term.
func (rf *Raft) InstallSnapshot(args *InstallSnapshotArgs, reply *InstallSnapshotReply) {
	rf.mu.Lock()
	reply.Term = rf.currentTerm
	rf.mu.Unlock()
}

// ChangeMembership is a stub for joint-consensus membership changes.
func (rf *Raft) ChangeMembership(newVoters []int, newLearners []int) (int, bool) {
	return -1, false
}

// TransferLeadership is a stub for leadership transfer.
func (rf *Raft) TransferLeadership(target int) bool { return false }

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
