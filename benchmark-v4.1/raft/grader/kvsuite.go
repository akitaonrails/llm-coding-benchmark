package grader

import (
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"v41raft/harness"
	"v41raft/harness/labrpc"
	"v41raft/harness/porcupine"
)

// ---------------------------------------------------------------------------
// KV implementation factories (so the reference and the broken variants can be
// driven by the same tests)
// ---------------------------------------------------------------------------

// KVServerHandle is the slice of a KV server the cluster manager drives.
type KVServerHandle interface {
	Kill()
	Raft() interface{} // the concrete raft peer, for labrpc service registration
}

// KVClerk is a KV client.
type KVClerk interface {
	Get(key string) string
	Put(key, value string)
	Append(key, value string)
}

// MakeKVFunc constructs a KV server; MakeClerkFunc constructs a clerk.
type MakeKVFunc func(servers []*labrpc.ClientEnd, me int, persister *harness.Persister,
	maxraftstate int, initial harness.Config) KVServerHandle
type MakeClerkFunc func(ends []*labrpc.ClientEnd) KVClerk

// KVImpl bundles the two factories.
type KVImpl struct {
	MakeServer MakeKVFunc
	MakeClerk  MakeClerkFunc
}

// ---------------------------------------------------------------------------
// KV cluster manager
// ---------------------------------------------------------------------------

type kvCluster struct {
	mu           sync.Mutex
	t            *testing.T
	net          *labrpc.Network
	n            int
	maxraftstate int
	impl         KVImpl
	initial      harness.Config
	servers      []KVServerHandle
	saved        []*harness.Persister
	connected    []bool
	clerkSeq     int64
	finished     int32
}

var kvSeedCounter int64

func makeKVCluster(t *testing.T, n int, reliable bool, maxraftstate int, impl KVImpl) *kvCluster {
	seed := atomic.AddInt64(&kvSeedCounter, 1)*2_000_003 + int64(n)
	kc := &kvCluster{
		t:            t,
		net:          labrpc.MakeNetwork(seed),
		n:            n,
		maxraftstate: maxraftstate,
		impl:         impl,
		servers:      make([]KVServerHandle, n),
		saved:        make([]*harness.Persister, n),
		connected:    make([]bool, n),
	}
	kc.net.SetReliable(reliable)
	voters := make([]int, n)
	for i := range voters {
		voters[i] = i
	}
	kc.initial = harness.Config{Voters: voters}
	for i := 0; i < n; i++ {
		kc.saved[i] = harness.MakePersister()
		kc.startServer(i)
	}
	for i := 0; i < n; i++ {
		kc.connect(i)
	}
	return kc
}

func (kc *kvCluster) startServer(i int) {
	ends := make([]*labrpc.ClientEnd, kc.n)
	for j := 0; j < kc.n; j++ {
		ends[j] = kc.net.MakeEnd(i, j)
	}

	kc.mu.Lock()
	kc.saved[i] = kc.saved[i].Copy()
	persister := kc.saved[i]
	kc.mu.Unlock()

	kv := kc.impl.MakeServer(ends, i, persister, kc.maxraftstate, kc.initial)

	kc.mu.Lock()
	kc.servers[i] = kv
	kc.mu.Unlock()

	srv := labrpc.MakeServer()
	srv.AddService(labrpc.MakeService(kv))
	srv.AddService(labrpc.MakeService(kv.Raft()))
	kc.net.AddServer(i, srv)
}

func (kc *kvCluster) crash(i int) {
	kc.disconnect(i)
	kc.net.DeleteServer(i)
	kc.mu.Lock()
	kc.saved[i] = kc.saved[i].Copy()
	kv := kc.servers[i]
	kc.servers[i] = nil
	kc.mu.Unlock()
	if kv != nil {
		kv.Kill()
	}
}

func (kc *kvCluster) restart(i int) {
	kc.crash(i)
	kc.startServer(i)
	kc.connect(i)
}

func (kc *kvCluster) connect(i int) {
	kc.mu.Lock()
	kc.connected[i] = true
	kc.mu.Unlock()
	kc.net.Enable(i, true)
}

func (kc *kvCluster) disconnect(i int) {
	kc.mu.Lock()
	kc.connected[i] = false
	kc.mu.Unlock()
	kc.net.Enable(i, false)
}

func (kc *kvCluster) partition(groups [][]int) { kc.net.Partition(groups) }

func (kc *kvCluster) makeClerk() KVClerk {
	seq := atomic.AddInt64(&kc.clerkSeq, 1)
	from := kc.n + int(seq) // clerk endpoint ids never collide with servers
	ends := make([]*labrpc.ClientEnd, kc.n)
	for j := 0; j < kc.n; j++ {
		ends[j] = kc.net.MakeEnd(from, j)
	}
	kc.net.Enable(from, true)
	return kc.impl.MakeClerk(ends)
}

func (kc *kvCluster) cleanup() {
	atomic.StoreInt32(&kc.finished, 1)
	kc.mu.Lock()
	servers := make([]KVServerHandle, kc.n)
	copy(servers, kc.servers)
	kc.mu.Unlock()
	for _, kv := range servers {
		if kv != nil {
			kv.Kill()
		}
	}
	kc.net.Cleanup()
}

func (kc *kvCluster) raftStateSize(i int) int {
	kc.mu.Lock()
	defer kc.mu.Unlock()
	if kc.saved[i] == nil {
		return 0
	}
	return kc.saved[i].RaftStateSize()
}

// ---------------------------------------------------------------------------
// porcupine KV register model
// ---------------------------------------------------------------------------

type kvInput struct {
	op    uint8 // 0 get, 1 put, 2 append
	key   string
	value string
}
type kvOutput struct {
	value string
}

func kvModel() porcupine.Model {
	return porcupine.Model{
		// Partition by key: each key is an independent register.
		Partition: func(history []porcupine.Operation) [][]porcupine.Operation {
			byKey := map[string][]porcupine.Operation{}
			order := []string{}
			for _, op := range history {
				k := op.Input.(kvInput).key
				if _, ok := byKey[k]; !ok {
					order = append(order, k)
				}
				byKey[k] = append(byKey[k], op)
			}
			out := make([][]porcupine.Operation, 0, len(order))
			for _, k := range order {
				out = append(out, byKey[k])
			}
			return out
		},
		Init: func() interface{} { return "" },
		Step: func(state, input, output interface{}) (bool, interface{}) {
			in := input.(kvInput)
			out := output.(kvOutput)
			st := state.(string)
			switch in.op {
			case 0: // get
				return out.value == st, st
			case 1: // put
				return true, in.value
			default: // append
				return true, st + in.value
			}
		},
		Equal: func(a, b interface{}) bool { return a.(string) == b.(string) },
	}
}

// recorder captures a concurrent history for porcupine.
type recorder struct {
	mu      sync.Mutex
	history []porcupine.Operation
}

func (r *recorder) begin() int64 { return time.Now().UnixNano() }

func (r *recorder) record(clientId int, in kvInput, out kvOutput, call, ret int64) {
	r.mu.Lock()
	r.history = append(r.history, porcupine.Operation{
		ClientId: clientId, Input: in, Output: out, Call: call, Return: ret,
	})
	r.mu.Unlock()
}

// ---------------------------------------------------------------------------
// KV tests
// ---------------------------------------------------------------------------

// RunKVBasic: single-client Get/Put/Append correctness.
func RunKVBasic(t *testing.T, impl KVImpl) {
	kc := makeKVCluster(t, 3, true, -1, impl)
	defer kc.cleanup()

	ck := kc.makeClerk()
	if v := ck.Get("k"); v != "" {
		t.Fatalf("Get of absent key = %q, want \"\"", v)
	}
	ck.Put("k", "v1")
	if v := ck.Get("k"); v != "v1" {
		t.Fatalf("Get = %q, want v1", v)
	}
	ck.Append("k", "-v2")
	if v := ck.Get("k"); v != "v1-v2" {
		t.Fatalf("Get = %q, want v1-v2", v)
	}
	ck.Put("k", "reset")
	ck.Append("k", "-a")
	ck.Append("k", "-b")
	if v := ck.Get("k"); v != "reset-a-b" {
		t.Fatalf("Get = %q, want reset-a-b", v)
	}
}

// RunKVConcurrent: several clerks, each hammering its own key, all consistent.
func RunKVConcurrent(t *testing.T, impl KVImpl) {
	kc := makeKVCluster(t, 5, true, -1, impl)
	defer kc.cleanup()

	const nClerks = 5
	const nOps = 20
	var wg sync.WaitGroup
	for c := 0; c < nClerks; c++ {
		wg.Add(1)
		go func(c int) {
			defer wg.Done()
			ck := kc.makeClerk()
			key := fmt.Sprintf("key-%d", c)
			want := ""
			for i := 0; i < nOps; i++ {
				tok := fmt.Sprintf("(%d.%d)", c, i)
				ck.Append(key, tok)
				want += tok
			}
			if got := ck.Get(key); got != want {
				t.Errorf("clerk %d: Get=%q want %q", c, got, want)
			}
		}(c)
	}
	wg.Wait()
}

// RunKVPartition: a client keeps making progress and reads its own writes
// correctly across partitions and leader churn.
func RunKVPartition(t *testing.T, impl KVImpl) {
	kc := makeKVCluster(t, 5, false, -1, impl)
	defer kc.cleanup()

	ck := kc.makeClerk()
	rnd := rand.New(rand.NewSource(99))

	want := ""
	for round := 0; round < 12; round++ {
		// shuffle a majority|minority partition
		maj, min := randPartition(rnd, 5)
		kc.partition([][]int{maj, min})

		tok := fmt.Sprintf("<%d>", round)
		ck.Append("k", tok)
		want += tok
		if got := ck.Get("k"); got != want {
			t.Fatalf("round %d: Get=%q want %q", round, got, want)
		}

		kc.partition(nil)
	}
}

// RunKVSnapshotSize: with a small maxraftstate the persisted raft state stays
// bounded (snapshots compact the log) while the store stays correct across a
// restart that must recover from a snapshot.
func RunKVSnapshotSize(t *testing.T, impl KVImpl) {
	const maxraft = 1000
	kc := makeKVCluster(t, 3, true, maxraft, impl)
	defer kc.cleanup()

	ck := kc.makeClerk()
	want := map[string]string{}
	for i := 0; i < 300; i++ {
		key := fmt.Sprintf("k%d", i%10)
		val := fmt.Sprintf("v%d", i)
		ck.Put(key, val)
		want[key] = val
		for s := 0; s < 3; s++ {
			if sz := kc.raftStateSize(s); sz > 10*maxraft {
				t.Fatalf("raft state size %d exceeds 10x maxraftstate (%d) at op %d", sz, maxraft, i)
			}
		}
	}

	// restart every server: each must recover its store from its snapshot.
	for s := 0; s < 3; s++ {
		kc.restart(s)
	}
	ck2 := kc.makeClerk()
	for key, val := range want {
		if got := ck2.Get(key); got != val {
			t.Fatalf("after restart Get(%s)=%q want %q", key, got, val)
		}
	}
}

// RunKVLinearizable: a fault-injecting concurrent workload (partitions,
// crashes, unreliable links) records a history that Porcupine's KV register
// model must find linearizable. A subtly-wrong Raft or a KV layer without
// at-most-once dedup produces a non-linearizable history.
func RunKVLinearizable(t *testing.T, impl KVImpl) {
	kc := makeKVCluster(t, 5, false, -1, impl)
	defer kc.cleanup()

	rec := &recorder{}
	const nClerks = 6
	keys := []string{"a", "b", "c"}

	stop := int32(0)
	var wg sync.WaitGroup

	// fault injector
	wg.Add(1)
	go func() {
		defer wg.Done()
		rnd := rand.New(rand.NewSource(7))
		for atomic.LoadInt32(&stop) == 0 {
			switch rnd.Intn(3) {
			case 0:
				maj, min := randPartition(rnd, 5)
				kc.partition([][]int{maj, min})
				time.Sleep(time.Duration(50+rnd.Intn(100)) * time.Millisecond)
				kc.partition(nil)
			case 1:
				s := rnd.Intn(5)
				kc.restart(s)
				time.Sleep(time.Duration(50+rnd.Intn(100)) * time.Millisecond)
			default:
				time.Sleep(time.Duration(30+rnd.Intn(70)) * time.Millisecond)
			}
		}
		kc.partition(nil)
	}()

	for c := 0; c < nClerks; c++ {
		wg.Add(1)
		go func(c int) {
			defer wg.Done()
			ck := kc.makeClerk()
			rnd := rand.New(rand.NewSource(int64(1000 + c)))
			n := 0
			for atomic.LoadInt32(&stop) == 0 {
				key := keys[rnd.Intn(len(keys))]
				switch rnd.Intn(3) {
				case 0:
					call := rec.begin()
					v := ck.Get(key)
					ret := rec.begin()
					rec.record(c, kvInput{op: 0, key: key}, kvOutput{value: v}, call, ret)
				case 1:
					val := fmt.Sprintf("p.%d.%d", c, n)
					call := rec.begin()
					ck.Put(key, val)
					ret := rec.begin()
					rec.record(c, kvInput{op: 1, key: key, value: val}, kvOutput{}, call, ret)
				default:
					val := fmt.Sprintf("(a.%d.%d)", c, n)
					call := rec.begin()
					ck.Append(key, val)
					ret := rec.begin()
					rec.record(c, kvInput{op: 2, key: key, value: val}, kvOutput{}, call, ret)
				}
				n++
			}
		}(c)
	}

	time.Sleep(8 * time.Second)
	atomic.StoreInt32(&stop, 1)
	wg.Wait()
	kc.partition(nil)

	rec.mu.Lock()
	history := rec.history
	rec.mu.Unlock()
	if len(history) < 50 {
		t.Fatalf("workload recorded too few operations (%d) to be meaningful", len(history))
	}

	res := porcupine.CheckOperationsTimeout(kvModel(), history, 20*time.Second)
	switch res {
	case porcupine.Ok:
		// linearizable
	case porcupine.Illegal:
		t.Fatalf("history of %d ops is NOT linearizable", len(history))
	default:
		t.Fatalf("linearizability check did not finish (result %v) on %d ops", res, len(history))
	}
}

// randPartition splits servers 0..n-1 into a random majority and minority.
func randPartition(rnd *rand.Rand, n int) ([]int, []int) {
	perm := rnd.Perm(n)
	k := n/2 + 1 // majority size
	maj := append([]int(nil), perm[:k]...)
	min := append([]int(nil), perm[k:]...)
	return maj, min
}
