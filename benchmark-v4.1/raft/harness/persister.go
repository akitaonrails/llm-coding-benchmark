package harness

import "sync"

// Persister is the simulated stable storage. A Raft peer saves its persistent
// state (and, in later sprints, a snapshot) here. Copy() produces an
// independent snapshot of the bytes so a crash/restart can hand the restarted
// peer exactly what was durable, while in-memory state is lost.
//
// Snapshot support is stubbed in for the foundation sprint (the methods exist
// and round-trip bytes) but the reference does not yet produce snapshots.
type Persister struct {
	mu        sync.Mutex
	raftstate []byte
	snapshot  []byte
}

// MakePersister returns an empty Persister.
func MakePersister() *Persister {
	return &Persister{}
}

func clone(b []byte) []byte {
	if b == nil {
		return nil
	}
	c := make([]byte, len(b))
	copy(c, b)
	return c
}

// Copy returns an independent Persister holding the same bytes.
func (ps *Persister) Copy() *Persister {
	ps.mu.Lock()
	defer ps.mu.Unlock()
	return &Persister{
		raftstate: clone(ps.raftstate),
		snapshot:  clone(ps.snapshot),
	}
}

// SaveRaftState persists the raft state, leaving any snapshot untouched.
func (ps *Persister) SaveRaftState(state []byte) {
	ps.mu.Lock()
	defer ps.mu.Unlock()
	ps.raftstate = clone(state)
}

// ReadRaftState returns the persisted raft state.
func (ps *Persister) ReadRaftState() []byte {
	ps.mu.Lock()
	defer ps.mu.Unlock()
	return clone(ps.raftstate)
}

// RaftStateSize returns the size of the persisted raft state in bytes.
func (ps *Persister) RaftStateSize() int {
	ps.mu.Lock()
	defer ps.mu.Unlock()
	return len(ps.raftstate)
}

// SaveStateAndSnapshot atomically persists raft state and a snapshot.
func (ps *Persister) SaveStateAndSnapshot(state, snapshot []byte) {
	ps.mu.Lock()
	defer ps.mu.Unlock()
	ps.raftstate = clone(state)
	ps.snapshot = clone(snapshot)
}

// ReadSnapshot returns the persisted snapshot (nil if none).
func (ps *Persister) ReadSnapshot() []byte {
	ps.mu.Lock()
	defer ps.mu.Unlock()
	return clone(ps.snapshot)
}

// SnapshotSize returns the size of the persisted snapshot in bytes.
func (ps *Persister) SnapshotSize() int {
	ps.mu.Lock()
	defer ps.mu.Unlock()
	return len(ps.snapshot)
}
