# P1 — Raft-variant replicated KV: the CONTRACT (interface + grader spec)

Language: **Go** (go1.27). Deterministic in-process network simulation (no real sockets) so the
linearizability grader is reproducible — the proven approach (MIT 6.824 style), extended and hardened.

The model implements **only** `raft/raft.go` (+ helpers) and `kvraft/server.go` + `kvraft/client.go`.
Everything else below is **provided scaffold** (given in sprint 1, the model must NOT reimplement it) so the
grader can drive any submission identically.

---

## Provided scaffold (given to the model; the grader also uses it)
- `labrpc/` — deterministic network sim with **fault-injection hooks the grader controls**: per-link
  reliability, `partition(groups)`, delay/reorder/drop, long-delay. Clean-room (not copied from any course).
- `raft/persister.go` — `Persister` with `SaveStateAndSnapshot`, `ReadRaftState`, `ReadSnapshot`, and a
  `Copy()` used to simulate crash/restart (state survives; in-memory does not).
- `raft/config.go` (test support) — cluster manager: `make_config(n)`, `connect/disconnect(i)`,
  `crash1(i)/start1(i)`, `checkOneLeader()`, `nCommitted(index)`, `one(cmd, expectedServers, retry)`.
- `go.mod` (module `v41raft`), `labgob` for encoding.

## What the model implements

### `raft` package — `raft/raft.go`
```go
type ApplyMsg struct {
  CommandValid bool; Command interface{}; CommandIndex int; CommandTerm int
  SnapshotValid bool; Snapshot []byte; SnapshotTerm int; SnapshotIndex int
}
type Config struct { // cluster config: voters + learners (for membership changes)
  Voters []int; Learners []int
}
func Make(peers []*labrpc.ClientEnd, me int, persister *Persister,
          applyCh chan ApplyMsg, initial Config) *Raft
func (rf *Raft) Start(command interface{}) (index int, term int, isLeader bool)
func (rf *Raft) GetState() (term int, isLeader bool)
func (rf *Raft) Snapshot(index int, snapshot []byte)   // log compaction
func (rf *Raft) Kill()

// RPC handlers (args/reply structs defined by the model, wired via labrpc):
//   RequestVote   — MUST carry a PreVote bool (two-phase election)
//   AppendEntries — heartbeat + log replication; carries leader commit
//   InstallSnapshot
//   TimeoutNow    — for leadership transfer

// Membership (the TWIST — joint consensus, not single-server):
func (rf *Raft) ChangeMembership(newVoters []int, newLearners []int) (index int, ok bool)
func (rf *Raft) TransferLeadership(target int) bool
```

### `kvraft` package — linearizable KV on top of raft
```go
func StartKVServer(servers []*labrpc.ClientEnd, me int, persister *Persister,
                   maxraftstate int, initial raft.Config) *KVServer
type Clerk struct{ ... }
func MakeClerk(servers []*labrpc.ClientEnd) *Clerk
func (ck *Clerk) Get(key string) string
func (ck *Clerk) Put(key, value string)
func (ck *Clerk) Append(key, value string)
// Must provide: at-most-once semantics (client id + seq dedup), linearizable reads
// (reads go through the log or a read-index/lease), and snapshotting when the raft
// state exceeds maxraftstate.
```

## The variant TWIST (breaks memorized 6.824 / textbook Raft)
Mandatory, and each has a dedicated grader test:
1. **PreVote** — a candidate must win a pre-election (no term bump) before starting a real election, so a
   partitioned-then-rejoined node cannot disrupt a stable leader. Test: isolate a node, let its term inflate
   attempts, reconnect → the existing leader must NOT be deposed.
2. **CheckQuorum** — a leader that cannot reach a majority must step down within an election timeout. Test:
   partition the leader into a minority → it must relinquish leadership.
3. **Joint-consensus membership change** — `ChangeMembership` must go through C_old,new (joint) before C_new;
   safe under partition. Test: reconfigure (add/remove voters) *while a partition is active*; no split-brain,
   no committed-entry loss.
4. **Learners (non-voting)** — added nodes catch up as learners (don't count toward quorum) before promotion.
   Test: add a far-behind learner; it must receive a snapshot + catch up without stalling commits.
5. **Snapshot/compaction** — `Snapshot` trims the log; `InstallSnapshot` brings laggards/learners current.

---

## The GRADER gauntlet (HIDDEN until grading; run by an isolated executor)
Each is a Go test; score = fraction passing, weighted. All run with the race detector (`-race`).

**Raft correctness**
- `TestInitialElection` — exactly one leader; stable; term agreement.
- `TestReElection` / `TestPreVote` — leader survives a reconnecting high-term node (PreVote works).
- `TestCheckQuorum` — minority-partitioned leader steps down.
- `TestBasicAgree`, `TestFailAgree`, `TestFailNoAgree` — replication; progress with a majority, none without.
- `TestConcurrentStarts`, `TestRejoin`, `TestBackup` — the hard log-divergence/backup cases.
- `TestPersist1/2/3` — crash/restart via Persister; committed entries survive.
- `TestSnapshotBasic/Install/Crash` — compaction + InstallSnapshot + crash during snapshot.
- `TestMembershipJoint` — reconfig under partition; **no split-brain, no committed-entry loss** (the twist).
- `TestLearnerCatchup` — far-behind learner catches up via snapshot, promoted, commits continue.

**Linearizable KV (the apex)**
- `TestKVBasic`, `TestKVConcurrent`, `TestKVPartition` — Get/Put/Append under partitions + leader churn.
- `TestKVLinearizable` — a fault-injecting workload (partitions, crashes, reorder, long-delay) records a
  history; a **Porcupine-based linearizability checker** (KV register model) must find the history
  linearizable. This is the decisive test: a subtly-wrong Raft produces a non-linearizable history.
- `TestKVSnapshotSize` — with small `maxraftstate`, snapshots keep state bounded while staying correct.

Grader output: JSON `{test: pass|fail, elapsed, detail}` + a weighted total and a per-sprint "depth cleared."

---

## VALIDATION requirement (do BEFORE any model run)
The grader is worthless unless it is **sound and sensitive**:
- **Sound:** a provided reference-correct implementation (`reference/raft.go`, `reference/kvraft/`) passes the
  ENTIRE gauntlet with `-race`, repeatably (run ≥5×; no flakes).
- **Sensitive (proven negative tests):** a set of deliberately-broken variants each fail the *right* test:
  (a) no PreVote → `TestPreVote` fails; (b) commit-without-majority → `TestFailNoAgree`/linearizability fails;
  (c) no dedup in KV → `TestKVLinearizable` fails (duplicate Append); (d) single-server membership (no joint)
  → `TestMembershipJoint` fails under partition; (e) forget to persist votedFor → `TestPersist` fails.
Only once sound+sensitive do we run models.

## Sprint breakdown (8, accumulating — the long-horizon axis)
S1 election (+PreVote) · S2 log replication · S3 persistence/crash · S4 snapshots/compaction ·
S5 joint-consensus membership · S6 learners + leadership transfer + CheckQuorum · S7 linearizable KV layer ·
S8 "hardening reveal": the full fault-injection + linearizability gauntlet is described and the model must
make everything green under `-race`.
