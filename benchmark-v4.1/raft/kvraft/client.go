// Package kvraft is a linearizable key/value service built on the reference
// Raft. A Clerk talks to whichever server is the current leader; writes carry a
// (client-id, seq) pair so the servers can apply each operation at most once,
// and every operation (including Get) is driven through the Raft log so reads
// are linearizable.
package kvraft

import (
	"crypto/rand"
	"math/big"
	"sync"

	"v41raft/harness/labrpc"
)

const (
	errOK          = "OK"
	errWrongLeader = "ErrWrongLeader"
	errTimeout     = "ErrTimeout"
)

// GetArgs/GetReply and PutAppendArgs/PutAppendReply are the RPC payloads.
type GetArgs struct {
	Key      string
	ClientId int64
	Seq      int64
}
type GetReply struct {
	Err   string
	Value string
}
type PutAppendArgs struct {
	Key      string
	Value    string
	Op       string // "Put" or "Append"
	ClientId int64
	Seq      int64
}
type PutAppendReply struct {
	Err string
}

func nrand() int64 {
	max := big.NewInt(int64(1) << 62)
	x, _ := rand.Int(rand.Reader, max)
	return x.Int64()
}

// Clerk is a KV client.
type Clerk struct {
	servers  []*labrpc.ClientEnd
	clientId int64
	mu       sync.Mutex
	seq      int64
	leader   int
}

// MakeClerk creates a Clerk talking to the given servers.
func MakeClerk(servers []*labrpc.ClientEnd) *Clerk {
	return &Clerk{servers: servers, clientId: nrand()}
}

func (ck *Clerk) nextSeq() int64 {
	ck.mu.Lock()
	defer ck.mu.Unlock()
	ck.seq++
	return ck.seq
}

// Get returns the current value for key ("" if absent). It retries until a
// server answers as leader.
func (ck *Clerk) Get(key string) string {
	args := GetArgs{Key: key, ClientId: ck.clientId, Seq: ck.nextSeq()}
	for {
		ck.mu.Lock()
		leader := ck.leader
		ck.mu.Unlock()
		for i := 0; i < len(ck.servers); i++ {
			srv := (leader + i) % len(ck.servers)
			var reply GetReply
			if ck.servers[srv].Call("KVServer.Get", &args, &reply) && reply.Err == errOK {
				ck.setLeader(srv)
				return reply.Value
			}
		}
	}
}

// Put sets key to value.
func (ck *Clerk) Put(key, value string) { ck.putAppend(key, value, "Put") }

// Append appends value to key.
func (ck *Clerk) Append(key, value string) { ck.putAppend(key, value, "Append") }

func (ck *Clerk) putAppend(key, value, op string) {
	args := PutAppendArgs{Key: key, Value: value, Op: op, ClientId: ck.clientId, Seq: ck.nextSeq()}
	for {
		ck.mu.Lock()
		leader := ck.leader
		ck.mu.Unlock()
		for i := 0; i < len(ck.servers); i++ {
			srv := (leader + i) % len(ck.servers)
			var reply PutAppendReply
			if ck.servers[srv].Call("KVServer.PutAppend", &args, &reply) && reply.Err == errOK {
				ck.setLeader(srv)
				return
			}
		}
	}
}

func (ck *Clerk) setLeader(i int) {
	ck.mu.Lock()
	ck.leader = i
	ck.mu.Unlock()
}
