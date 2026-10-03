package nodedup

import (
	"bytes"
	"sync"
	"sync/atomic"
	"time"

	"v41raft/harness"
	"v41raft/harness/labgob"
	"v41raft/harness/labrpc"
	"v41raft/reference"
)

const applyWaitTimeout = 1 * time.Second

// Op is one replicated state-machine command.
type Op struct {
	Type     string // "Get", "Put", "Append"
	Key      string
	Value    string
	ClientId int64
	Seq      int64
}

type opResult struct {
	clientId int64
	seq      int64
	value    string
}

// KVServer is a single KV replica backed by a Raft peer.
type KVServer struct {
	mu        sync.Mutex
	me        int
	rf        *reference.Raft
	applyCh   chan harness.ApplyMsg
	dead      int32
	persister *harness.Persister

	maxraftstate int

	data        map[string]string
	lastSeq     map[int64]int64 // clientId -> highest applied write seq (dedup)
	lastApplied int             // highest raft index applied
	waiters     map[int]chan opResult

	killCh chan struct{}
}

// StartKVServer creates and starts a KV replica.
func StartKVServer(servers []*labrpc.ClientEnd, me int, persister *harness.Persister,
	maxraftstate int, initial harness.Config) *KVServer {

	labgob.Register(Op{})
	labgob.Register(reference.ConfigState{})

	kv := &KVServer{
		me:           me,
		applyCh:      make(chan harness.ApplyMsg),
		persister:    persister,
		maxraftstate: maxraftstate,
		data:         map[string]string{},
		lastSeq:      map[int64]int64{},
		waiters:      map[int]chan opResult{},
		killCh:       make(chan struct{}),
	}
	kv.restoreFromSnapshot(persister.ReadSnapshot())
	kv.rf = reference.Make(servers, me, persister, kv.applyCh, initial)

	go kv.applyLoop()
	return kv
}

// Raft returns the underlying raft peer so the harness can register its RPC
// service (labrpc reflects the concrete *reference.Raft).
func (kv *KVServer) Raft() interface{} { return kv.rf }

// Kill stops the server.
func (kv *KVServer) Kill() {
	atomic.StoreInt32(&kv.dead, 1)
	kv.rf.Kill()
	select {
	case <-kv.killCh:
	default:
		close(kv.killCh)
	}
}

func (kv *KVServer) killed() bool { return atomic.LoadInt32(&kv.dead) == 1 }

// ---------------------------------------------------------------------------
// RPC handlers
// ---------------------------------------------------------------------------

// Get drives a (linearizable) read through the log.
func (kv *KVServer) Get(args *GetArgs, reply *GetReply) {
	op := Op{Type: "Get", Key: args.Key, ClientId: args.ClientId, Seq: args.Seq}
	res, ok := kv.submit(op)
	if !ok {
		reply.Err = errWrongLeader
		return
	}
	reply.Err = errOK
	reply.Value = res.value
}

// PutAppend drives a write through the log.
func (kv *KVServer) PutAppend(args *PutAppendArgs, reply *PutAppendReply) {
	op := Op{Type: args.Op, Key: args.Key, Value: args.Value, ClientId: args.ClientId, Seq: args.Seq}
	_, ok := kv.submit(op)
	if !ok {
		reply.Err = errWrongLeader
		return
	}
	reply.Err = errOK
}

// submit proposes op, waits for the committed entry at its index, and confirms
// the committed entry is the one we proposed (guarding against leader change).
func (kv *KVServer) submit(op Op) (opResult, bool) {
	index, _, isLeader := kv.rf.Start(op)
	if !isLeader {
		return opResult{}, false
	}

	kv.mu.Lock()
	ch := make(chan opResult, 1)
	kv.waiters[index] = ch
	kv.mu.Unlock()

	defer func() {
		kv.mu.Lock()
		delete(kv.waiters, index)
		kv.mu.Unlock()
	}()

	select {
	case res := <-ch:
		if res.clientId != op.ClientId || res.seq != op.Seq {
			return opResult{}, false // a different op committed at our index
		}
		return res, true
	case <-time.After(applyWaitTimeout):
		return opResult{}, false
	case <-kv.killCh:
		return opResult{}, false
	}
}

// ---------------------------------------------------------------------------
// apply loop
// ---------------------------------------------------------------------------

func (kv *KVServer) applyLoop() {
	for {
		select {
		case <-kv.killCh:
			return
		case m := <-kv.applyCh:
			switch {
			case m.SnapshotValid:
				kv.applySnapshot(m)
			case m.CommandValid:
				kv.applyCommand(m)
			}
		}
	}
}

func (kv *KVServer) applyCommand(m harness.ApplyMsg) {
	op, ok := m.Command.(Op)
	if !ok {
		// a non-KV entry (e.g. a membership-change ConfigState); nothing to
		// apply to the key/value store, but keep bookkeeping advancing.
		kv.mu.Lock()
		kv.lastApplied = m.CommandIndex
		kv.maybeSnapshotLocked()
		kv.mu.Unlock()
		return
	}

	kv.mu.Lock()
	res := opResult{clientId: op.ClientId, seq: op.Seq}
	switch op.Type {
	case "Get":
		res.value = kv.data[op.Key]
	case "Put":
		// BUG (nodedup): no at-most-once filtering. A Put is idempotent so this
		// alone is harmless, but the matching Append bug below is not.
		kv.data[op.Key] = op.Value
	case "Append":
		// BUG (nodedup): apply every Append unconditionally. When a client
		// retries an Append whose reply was lost (common under an unreliable
		// network / partitions), the value is appended TWICE, which no
		// linearization of the single client Append can explain -> the recorded
		// history is non-linearizable. A correct server dedups on
		// (clientId, seq).
		kv.data[op.Key] += op.Value
	}
	kv.lastApplied = m.CommandIndex
	ch := kv.waiters[m.CommandIndex]
	kv.maybeSnapshotLocked()
	kv.mu.Unlock()

	if ch != nil {
		select {
		case ch <- res:
		default:
		}
	}
}

func (kv *KVServer) applySnapshot(m harness.ApplyMsg) {
	kv.mu.Lock()
	defer kv.mu.Unlock()
	if m.SnapshotIndex <= kv.lastApplied {
		return
	}
	kv.restoreFromSnapshot(m.Snapshot)
	kv.lastApplied = m.SnapshotIndex
}

// ---------------------------------------------------------------------------
// snapshotting
// ---------------------------------------------------------------------------

// maybeSnapshotLocked compacts the raft log when the persisted state grows past
// maxraftstate. Caller holds kv.mu.
func (kv *KVServer) maybeSnapshotLocked() {
	if kv.maxraftstate <= 0 {
		return
	}
	if kv.persister.RaftStateSize() < kv.maxraftstate {
		return
	}
	snap := kv.encodeSnapshotLocked()
	index := kv.lastApplied
	// rf.Snapshot takes rf.mu; call without kv.mu to avoid lock-order coupling.
	go kv.rf.Snapshot(index, snap)
}

func (kv *KVServer) encodeSnapshotLocked() []byte {
	buf := new(bytes.Buffer)
	enc := labgob.NewEncoder(buf)
	_ = enc.Encode(kv.data)
	_ = enc.Encode(kv.lastSeq)
	return buf.Bytes()
}

func (kv *KVServer) restoreFromSnapshot(data []byte) {
	if len(data) == 0 {
		return
	}
	dec := labgob.NewDecoder(bytes.NewBuffer(data))
	var store map[string]string
	var lastSeq map[int64]int64
	if dec.Decode(&store) != nil || dec.Decode(&lastSeq) != nil {
		return
	}
	kv.data = store
	kv.lastSeq = lastSeq
}
