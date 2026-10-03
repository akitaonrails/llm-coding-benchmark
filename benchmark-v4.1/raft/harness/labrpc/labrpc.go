// Package labrpc is a clean-room, deterministic, in-process RPC network
// simulator. It lets a set of integer-indexed "servers" call each other's
// methods without real sockets, while the test harness injects faults:
// per-link reliability, server enable/disable, network partitions, message
// delay, drop and reorder. All randomness is drawn from a single seeded RNG
// so a given seed + goroutine schedule is reproducible.
//
// This is written from scratch for v4.1; it is not copied from MIT 6.824. The
// design choices that differ: servers are addressed by integer id (not opaque
// endnames), partitions are a first-class Network operation taking groups of
// ids, and the service dispatch requires pointer args AND pointer reply.
//
// RPC method convention (enforced by MakeService):
//
//	func (t *T) Method(args *ArgT, reply *ReplyT)   // no return value
//
// A ClientEnd.Call("T.Method", args, reply) returns true iff a reply came back
// (the network delivered the request, the handler ran, and the reply was
// delivered). A false return means "no reply" (timeout/drop/partition) — the
// caller cannot tell why, exactly like a real RPC timeout.
package labrpc

import (
	"bytes"
	"math/rand"
	"reflect"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"v41raft/harness/labgob"
)

// ---------------------------------------------------------------------------
// ClientEnd
// ---------------------------------------------------------------------------

// ClientEnd is one directed endpoint: RPCs sent through it originate at server
// `from` and target server `to`.
type ClientEnd struct {
	from int
	to   int
	net  *Network
}

// Call sends an RPC and waits for the reply. args and reply must both be
// pointers. Returns true iff a reply was delivered.
func (e *ClientEnd) Call(svcMeth string, args interface{}, reply interface{}) bool {
	buf := new(bytes.Buffer)
	enc := labgob.NewEncoder(buf)
	if err := enc.Encode(args); err != nil {
		panic("labrpc: Call could not encode args: " + err.Error())
	}

	ok, replyb := e.net.processCall(e.from, e.to, svcMeth, buf.Bytes())
	if !ok {
		return false
	}

	dec := labgob.NewDecoder(bytes.NewBuffer(replyb))
	if err := dec.Decode(reply); err != nil {
		panic("labrpc: Call could not decode reply: " + err.Error())
	}
	return true
}

// ---------------------------------------------------------------------------
// Network
// ---------------------------------------------------------------------------

// Network is the simulated switch fabric.
type Network struct {
	mu             sync.Mutex
	rng            *rand.Rand
	reliable       bool
	longReordering bool // occasionally hold a reply back a long time
	longDelays     bool // unreachable calls take longer to fail
	servers        map[int]*Server
	enabled        map[int]bool // is server i connected to the net
	partitions     map[int]int  // server id -> partition group; nil = one group
	count          int32        // total RPCs attempted
	bytesSent      int64
	done           chan struct{}
	closed         bool
}

// MakeNetwork creates a reliable network seeded deterministically.
func MakeNetwork(seed int64) *Network {
	return &Network{
		rng:        rand.New(rand.NewSource(seed)),
		reliable:   true,
		servers:    make(map[int]*Server),
		enabled:    make(map[int]bool),
		partitions: nil,
		done:       make(chan struct{}),
	}
}

// SetReliable toggles drop/delay on reachable links.
func (rn *Network) SetReliable(yes bool) {
	rn.mu.Lock()
	rn.reliable = yes
	rn.mu.Unlock()
}

// SetLongReordering toggles occasional long reply reordering.
func (rn *Network) SetLongReordering(yes bool) {
	rn.mu.Lock()
	rn.longReordering = yes
	rn.mu.Unlock()
}

// SetLongDelays toggles whether unreachable calls take a long time to fail.
func (rn *Network) SetLongDelays(yes bool) {
	rn.mu.Lock()
	rn.longDelays = yes
	rn.mu.Unlock()
}

// MakeEnd creates a directed endpoint from server `from` to server `to`.
func (rn *Network) MakeEnd(from, to int) *ClientEnd {
	return &ClientEnd{from: from, to: to, net: rn}
}

// AddServer installs (or replaces) the server at id i.
func (rn *Network) AddServer(i int, srv *Server) {
	rn.mu.Lock()
	rn.servers[i] = srv
	rn.mu.Unlock()
}

// DeleteServer removes the server at id i (simulates a crash: in-flight calls
// to the old instance are dropped).
func (rn *Network) DeleteServer(i int) {
	rn.mu.Lock()
	rn.servers[i] = nil
	rn.mu.Unlock()
}

// Enable connects/disconnects server i from the network (both directions).
func (rn *Network) Enable(i int, yes bool) {
	rn.mu.Lock()
	rn.enabled[i] = yes
	rn.mu.Unlock()
}

// Partition splits the servers into disjoint groups; links only work within a
// group. Every server used in the test must appear in exactly one group. Pass
// nil to heal all partitions.
func (rn *Network) Partition(groups [][]int) {
	rn.mu.Lock()
	defer rn.mu.Unlock()
	if groups == nil {
		rn.partitions = nil
		return
	}
	m := make(map[int]int)
	for gi, g := range groups {
		for _, s := range g {
			m[s] = gi + 1 // group ids start at 1 so the zero value never collides
		}
	}
	rn.partitions = m
}

// GetCount returns the number of RPCs attempted.
func (rn *Network) GetCount() int {
	return int(atomic.LoadInt32(&rn.count))
}

// Cleanup marks the network torn down. In-flight calls are allowed to finish.
func (rn *Network) Cleanup() {
	rn.mu.Lock()
	if !rn.closed {
		rn.closed = true
		close(rn.done)
	}
	rn.mu.Unlock()
}

// reachableLocked reports whether a message from->to can be delivered right
// now. Caller holds rn.mu.
func (rn *Network) reachableLocked(from, to int) bool {
	if !rn.enabled[from] || !rn.enabled[to] {
		return false
	}
	if rn.partitions != nil {
		// A partition only separates servers that are BOTH assigned to groups.
		// Endpoints outside the partition map (e.g. KV clerks) can reach any
		// connected server — exactly like a real client that can route to
		// whatever replica it can still contact.
		fg, fok := rn.partitions[from]
		tg, tok := rn.partitions[to]
		if fok && tok && fg != tg {
			return false
		}
	}
	return true
}

// randn draws a deterministic int in [0,n) under the network lock.
func (rn *Network) randn(n int) int {
	if n <= 0 {
		return 0
	}
	rn.mu.Lock()
	v := rn.rng.Intn(n)
	rn.mu.Unlock()
	return v
}

// processCall is the core delivery path. It returns (delivered, replyBytes).
func (rn *Network) processCall(from, to int, svcMeth string, argb []byte) (bool, []byte) {
	atomic.AddInt32(&rn.count, 1)
	atomic.AddInt64(&rn.bytesSent, int64(len(argb)))

	rn.mu.Lock()
	reachable := rn.reachableLocked(from, to)
	srv := rn.servers[to]
	reliable := rn.reliable
	longReorder := rn.longReordering
	longDelays := rn.longDelays
	rn.mu.Unlock()

	if !reachable || srv == nil {
		// Simulate a request that never gets a reply. Sleep a bounded,
		// deterministic amount so the caller does not busy-loop.
		ms := rn.randn(100)
		if longDelays {
			ms = 200 + rn.randn(600)
		}
		time.Sleep(time.Duration(ms) * time.Millisecond)
		return false, nil
	}

	if !reliable {
		// short random latency before the request is processed
		time.Sleep(time.Duration(rn.randn(27)) * time.Millisecond)
		// 10% chance the request is dropped (no reply)
		if rn.randn(1000) < 100 {
			return false, nil
		}
	}

	// Run the handler in its own goroutine so we can abandon it if the target
	// server is disconnected or replaced (crash/restart) mid-call.
	ech := make(chan replyMsg, 1)
	go func() {
		ech <- srv.dispatch(svcMeth, argb)
	}()

	var reply replyMsg
	gotReply := false
	for !gotReply {
		select {
		case reply = <-ech:
			gotReply = true
		case <-time.After(100 * time.Millisecond):
			rn.mu.Lock()
			stillReachable := rn.reachableLocked(from, to)
			sameServer := rn.servers[to] == srv
			rn.mu.Unlock()
			if !stillReachable || !sameServer {
				// drain in the background so the handler goroutine can exit
				go func() { <-ech }()
				return false, nil
			}
		}
	}

	// unreliable links occasionally drop the reply too
	if !reliable && rn.randn(1000) < 100 {
		return false, nil
	}

	// If the endpoint was disconnected (or the server replaced) while the
	// handler ran, drop the reply.
	rn.mu.Lock()
	stillReachable := rn.reachableLocked(from, to)
	sameServer := rn.servers[to] == srv
	rn.mu.Unlock()
	if !stillReachable || !sameServer {
		return false, nil
	}

	if longReorder && rn.randn(1000) < 600 {
		time.Sleep(time.Duration(200+rn.randn(600)) * time.Millisecond)
	}

	if !reply.ok {
		return false, nil
	}
	atomic.AddInt64(&rn.bytesSent, int64(len(reply.reply)))
	return true, reply.reply
}

// ---------------------------------------------------------------------------
// Server + Service (reflection-based dispatch)
// ---------------------------------------------------------------------------

type replyMsg struct {
	ok    bool
	reply []byte
}

// Server hosts one or more named services.
type Server struct {
	mu       sync.Mutex
	services map[string]*Service
	count    int
}

// MakeServer creates an empty server.
func MakeServer() *Server {
	return &Server{services: make(map[string]*Service)}
}

// AddService registers svc under its reflected type name.
func (s *Server) AddService(svc *Service) {
	s.mu.Lock()
	s.services[svc.name] = svc
	s.mu.Unlock()
}

func (s *Server) dispatch(svcMeth string, argb []byte) replyMsg {
	dot := strings.LastIndex(svcMeth, ".")
	if dot < 0 {
		return replyMsg{false, nil}
	}
	serviceName := svcMeth[:dot]
	methodName := svcMeth[dot+1:]

	s.mu.Lock()
	svc := s.services[serviceName]
	s.count++
	s.mu.Unlock()

	if svc == nil {
		return replyMsg{false, nil}
	}
	return svc.dispatch(methodName, argb)
}

// Service wraps a receiver and its RPC-shaped methods.
type Service struct {
	name    string
	rcvr    reflect.Value
	typ     reflect.Type
	methods map[string]reflect.Method
}

// MakeService reflects rcvr and registers every method with signature
// func(*Args, *Reply). rcvr may be an interface value; reflection still sees
// the concrete type's methods.
func MakeService(rcvr interface{}) *Service {
	svc := &Service{
		typ:     reflect.TypeOf(rcvr),
		rcvr:    reflect.ValueOf(rcvr),
		methods: make(map[string]reflect.Method),
	}
	svc.name = reflect.Indirect(svc.rcvr).Type().Name()

	for m := 0; m < svc.typ.NumMethod(); m++ {
		method := svc.typ.Method(m)
		mt := method.Type
		// exported, (recv, *Args, *Reply), no results
		if method.PkgPath != "" {
			continue
		}
		if mt.NumIn() != 3 || mt.NumOut() != 0 {
			continue
		}
		if mt.In(1).Kind() != reflect.Ptr || mt.In(2).Kind() != reflect.Ptr {
			continue
		}
		svc.methods[method.Name] = method
	}
	return svc
}

func (svc *Service) dispatch(methname string, argb []byte) replyMsg {
	method, ok := svc.methods[methname]
	if !ok {
		return replyMsg{false, nil}
	}

	// decode args into a fresh *Args
	argv := reflect.New(method.Type.In(1).Elem())
	dec := labgob.NewDecoder(bytes.NewBuffer(argb))
	if err := dec.Decode(argv.Interface()); err != nil {
		return replyMsg{false, nil}
	}

	// fresh *Reply
	replyv := reflect.New(method.Type.In(2).Elem())

	method.Func.Call([]reflect.Value{svc.rcvr, argv, replyv})

	buf := new(bytes.Buffer)
	enc := labgob.NewEncoder(buf)
	if err := enc.Encode(replyv.Interface()); err != nil {
		return replyMsg{false, nil}
	}
	return replyMsg{true, buf.Bytes()}
}
