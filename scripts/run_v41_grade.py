#!/usr/bin/env python3
"""Grade a v4.1 submission (problem-parameterized: raft | storage | typedlang).

SECURE grading: build a CLEAN workspace from the known-good harness+grader and drop in ONLY the model's
authored package source, plus a generated wiring `_test.go` that adapts the model's concrete types to the
grader's maker. Run the hidden gauntlet per-test under -race (one deadlock fails only that test). Score /100.

Usage: run_v41_grade.py --problem storage --slug <slug>   |   --problem raft --src <dir>
"""
from __future__ import annotations
import argparse, json, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------- RAFT wiring
RAFT_WIRING = '''package grader
import ("testing";"v41raft/harness";"v41raft/harness/labrpc";"v41raft/raft")
func mMake(peers []*labrpc.ClientEnd, me int, p *harness.Persister, ch chan harness.ApplyMsg, initial harness.Config) harness.RaftNode {
  return raft.Make(peers, me, p, ch, initial)
}
func TestInitialElection(t *testing.T){RunInitialElection(t,mMake)}
func TestReElection(t *testing.T){RunReElection(t,mMake)}
func TestPreVote(t *testing.T){RunPreVote(t,mMake)}
func TestCheckQuorum(t *testing.T){RunCheckQuorum(t,mMake)}
func TestBasicAgree(t *testing.T){RunBasicAgree(t,mMake)}
func TestFailAgree(t *testing.T){RunFailAgree(t,mMake)}
func TestFailNoAgree(t *testing.T){RunFailNoAgree(t,mMake)}
func TestConcurrentStarts(t *testing.T){RunConcurrentStarts(t,mMake)}
func TestRejoin(t *testing.T){RunRejoin(t,mMake)}
func TestBackup(t *testing.T){RunBackup(t,mMake)}
func TestPersist1(t *testing.T){RunPersist1(t,mMake)}
func TestPersist2(t *testing.T){RunPersist2(t,mMake)}
func TestPersist3(t *testing.T){RunPersist3(t,mMake)}
func TestSnapshotBasic(t *testing.T){RunSnapshotBasic(t,mMake)}
func TestSnapshotInstall(t *testing.T){RunSnapshotInstall(t,mMake)}
func TestSnapshotCrash(t *testing.T){RunSnapshotCrash(t,mMake)}
func TestMembershipJoint(t *testing.T){RunMembershipJoint(t,mMake)}
func TestLearnerCatchup(t *testing.T){RunLearnerCatchup(t,mMake)}
func TestLeadershipTransfer(t *testing.T){RunLeadershipTransfer(t,mMake)}
'''
RAFT_KV_WIRING = '''package grader
import ("testing";"v41raft/harness";"v41raft/harness/labrpc";"v41raft/kvraft")
var mKV = KVImpl{
  MakeServer: func(servers []*labrpc.ClientEnd, me int, persister *harness.Persister, maxraftstate int, initial harness.Config) KVServerHandle {
    return kvraft.StartKVServer(servers, me, persister, maxraftstate, initial) },
  MakeClerk: func(ends []*labrpc.ClientEnd) KVClerk { return kvraft.MakeClerk(ends) },
}
func TestKVBasic(t *testing.T){RunKVBasic(t,mKV)}
func TestKVConcurrent(t *testing.T){RunKVConcurrent(t,mKV)}
func TestKVPartition(t *testing.T){RunKVPartition(t,mKV)}
func TestKVSnapshotSize(t *testing.T){RunKVSnapshotSize(t,mKV)}
func TestKVLinearizable(t *testing.T){RunKVLinearizable(t,mKV)}
'''
# --------------------------------------------------------------------------- STORAGE wiring
STORAGE_WIRING = '''package grader
import ("errors";"testing";"v41store/harness";"v41store/engine")
type dbShim struct{ db *engine.DB }
func (s dbShim) Begin() harness.TxnHandle { return txShim{s.db.Begin()} }
func (s dbShim) Close() error { return s.db.Close() }
type txShim struct{ tx *engine.Txn }
func (t txShim) Get(k []byte) ([]byte, bool) { return t.tx.Get(k) }
func (t txShim) Set(k, v []byte) { t.tx.Set(k, v) }
func (t txShim) Delete(k []byte) { t.tx.Delete(k) }
func (t txShim) Commit() error { return t.tx.Commit() }
func (t txShim) Abort() { t.tx.Abort() }
func (t txShim) Scan(lo, hi []byte, fn func(k, v []byte) bool) { t.tx.Scan(lo, hi, fn) }
func mMaker() harness.Maker {
  return harness.Maker{
    Open: func(dir string) (harness.DBHandle, error) { db, err := engine.Open(dir); if err != nil { return nil, err }; return dbShim{db}, nil },
    IsSerErr: func(e error) bool { return errors.Is(e, engine.ErrSerializationFailure) },
  }
}
func TestBasicPutGet(t *testing.T){RunBasicPutGet(t,mMaker())}
func TestScan(t *testing.T){RunScan(t,mMaker())}
func TestCommitDurable(t *testing.T){RunCommitDurable(t,mMaker())}
func TestAbortNoTrace(t *testing.T){RunAbortNoTrace(t,mMaker())}
func TestCrashMidCommitAtomic(t *testing.T){RunCrashMidCommitAtomic(t,mMaker())}
func TestRecoveryManyTxns(t *testing.T){RunRecoveryManyTxns(t,mMaker())}
func TestSnapshotIsolation(t *testing.T){RunSnapshotIsolation(t,mMaker())}
func TestLostUpdate(t *testing.T){RunLostUpdate(t,mMaker())}
func TestWriteSkew(t *testing.T){RunWriteSkew(t,mMaker())}
func TestReadOnlyAnomaly(t *testing.T){RunReadOnlyAnomaly(t,mMaker())}
func TestG2Cycle(t *testing.T){RunG2Cycle(t,mMaker())}
func TestSerializableFuzz(t *testing.T){RunSerializableFuzz(t,mMaker())}
'''

# --------------------------------------------------------------------------- TYPEDLANG wiring
TYPEDLANG_WIRING = '''package grader
import ("testing";"v41lang/harness";"v41lang/lang")
type langHandle struct{}
func (langHandle) TypeCheck(s string) error { return lang.TypeCheck(s) }
func (langHandle) Run(s string) (string, error) { return lang.Run(s) }
var mk harness.MakeLangFunc = func() harness.Lang { return langHandle{} }
func TestBasicEval(t *testing.T){RunBasicEval(t,mk)}
func TestClosures(t *testing.T){RunClosures(t,mk)}
func TestRecursion(t *testing.T){RunRecursion(t,mk)}
func TestRecords(t *testing.T){RunRecords(t,mk)}
func TestRecordUpdate(t *testing.T){RunRecordUpdate(t,mk)}
func TestLists(t *testing.T){RunLists(t,mk)}
func TestLetPolymorphism(t *testing.T){RunLetPolymorphism(t,mk)}
func TestOccursCheck(t *testing.T){RunOccursCheck(t,mk)}
func TestValueRestriction(t *testing.T){RunValueRestriction(t,mk)}
func TestRowPolymorphism(t *testing.T){RunRowPolymorphism(t,mk)}
func TestTypeErrors(t *testing.T){RunTypeErrors(t,mk)}
func TestGCNoLeak(t *testing.T){RunGCNoLeak(t,mk)}
func TestGCCycles(t *testing.T){RunGCCycles(t,mk)}
func TestGCStressMixed(t *testing.T){RunGCStressMixed(t,mk)}
'''

CONFIG = {
  "raft": {
    "dir": "benchmark-v4.1/raft", "out": "results-v4.1",
    "grader_src": ["suite.go", "kvsuite.go", "extended.go"],
    "pkgs": ["raft", "kvraft"],
    "wiring": {"z_wire_raft_test.go": RAFT_WIRING, "z_wire_kv_test.go": RAFT_KV_WIRING},
    "weights": {"TestInitialElection":2,"TestReElection":2,"TestPreVote":4,"TestCheckQuorum":4,"TestBasicAgree":2,
      "TestFailAgree":2,"TestFailNoAgree":3,"TestConcurrentStarts":3,"TestRejoin":4,"TestBackup":4,"TestPersist1":3,
      "TestPersist2":3,"TestPersist3":3,"TestSnapshotBasic":4,"TestSnapshotInstall":5,"TestSnapshotCrash":5,
      "TestMembershipJoint":10,"TestLearnerCatchup":8,"TestLeadershipTransfer":5,"TestKVBasic":3,"TestKVConcurrent":4,
      "TestKVPartition":5,"TestKVSnapshotSize":4,"TestKVLinearizable":12},
    "sprints": {1:["TestInitialElection","TestReElection","TestPreVote"],
      2:["TestBasicAgree","TestFailAgree","TestFailNoAgree","TestConcurrentStarts","TestRejoin","TestBackup"],
      3:["TestPersist1","TestPersist2","TestPersist3"],4:["TestSnapshotBasic","TestSnapshotInstall","TestSnapshotCrash"],
      5:["TestMembershipJoint"],6:["TestLearnerCatchup","TestLeadershipTransfer","TestCheckQuorum"],
      7:["TestKVBasic","TestKVConcurrent","TestKVPartition","TestKVSnapshotSize"],8:["TestKVLinearizable"]},
  },
  "storage": {
    "dir": "benchmark-v4.1/storage", "out": "results-v4.1/storage",
    "grader_src": ["suite.go", "oracle.go"],
    "pkgs": ["engine"],
    "wiring": {"z_wire_test.go": STORAGE_WIRING},
    "weights": {"TestBasicPutGet":3,"TestScan":3,"TestCommitDurable":6,"TestAbortNoTrace":5,"TestCrashMidCommitAtomic":12,
      "TestRecoveryManyTxns":6,"TestSnapshotIsolation":6,"TestLostUpdate":7,"TestWriteSkew":12,"TestReadOnlyAnomaly":8,
      "TestG2Cycle":10,"TestSerializableFuzz":22},
    "sprints": {1:["TestBasicPutGet","TestScan"],2:["TestCommitDurable","TestAbortNoTrace","TestRecoveryManyTxns"],
      3:["TestSnapshotIsolation","TestLostUpdate"],4:["TestWriteSkew","TestG2Cycle"],5:["TestReadOnlyAnomaly"],
      6:["TestCrashMidCommitAtomic"],7:["TestSerializableFuzz"]},
  },
  "typedlang": {
    "dir": "benchmark-v4.1/typedlang", "out": "results-v4.1/typedlang",
    "grader_src": ["conformance.go", "gc.go", "inference.go", "suite.go"],
    "pkgs": ["lang"],
    "wiring": {"z_wire_test.go": TYPEDLANG_WIRING},
    "weights": {"TestBasicEval":4,"TestClosures":5,"TestRecursion":5,"TestRecords":5,"TestRecordUpdate":6,
      "TestLists":5,"TestLetPolymorphism":7,"TestOccursCheck":6,"TestValueRestriction":7,"TestRowPolymorphism":14,
      "TestTypeErrors":8,"TestGCNoLeak":12,"TestGCCycles":8,"TestGCStressMixed":8},
    "sprints": {1:[],2:["TestLetPolymorphism","TestOccursCheck"],
      3:["TestRowPolymorphism","TestValueRestriction","TestTypeErrors"],
      4:["TestBasicEval","TestClosures","TestRecursion","TestRecords","TestRecordUpdate","TestLists"],
      5:["TestGCNoLeak","TestGCCycles"],6:["TestGCStressMixed"],7:[]},
  },
}


def build_workspace(cfg: dict, src: Path, ws: Path) -> str | None:
    rdir = REPO / cfg["dir"]
    ws.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rdir / "go.mod", ws / "go.mod")
    shutil.copytree(rdir / "harness", ws / "harness")
    (ws / "grader").mkdir()
    for f in cfg["grader_src"]:
        shutil.copy2(rdir / "grader" / f, ws / "grader" / f)
    for pkg in cfg["pkgs"]:
        sp = src / pkg
        if not sp.is_dir():
            return f"missing package dir: {pkg}/ (model did not implement it)"
        (ws / pkg).mkdir()
        for gf in sp.glob("*.go"):
            if gf.name.endswith("_test.go"):
                continue
            shutil.copy2(gf, ws / pkg / gf.name)
    for fname, content in cfg["wiring"].items():
        (ws / "grader" / fname).write_text(content)
    return None


def grade(problem: str, src: Path, slug: str) -> dict:
    cfg = CONFIG[problem]
    ws = Path(tempfile.mkdtemp(prefix=f"v41g_{problem}_{slug}_"))
    weights = cfg["weights"]; sprints = cfg["sprints"]
    r = {"problem": problem, "slug": slug, "src": str(src), "tests": {}, "score": 0.0,
         "max_sprint_cleared": 0, "compile_ok": False, "error": None}
    try:
        err = build_workspace(cfg, src, ws)
        if err:
            r["error"] = err; return r
        bb = subprocess.run(["go", "build", "./..."], cwd=ws, capture_output=True, text=True, timeout=300)
        if bb.returncode != 0:
            r["error"] = "compile failed (contract mismatch):\n" + bb.stderr[:1500]; return r
        r["compile_ok"] = True
        t0 = time.time()
        for name in weights:
            try:
                p = subprocess.run(["go", "test", "-race", "-count=1", "-run", f"^{name}$", "-timeout", "280s", "./grader/"],
                                   cwd=ws, capture_output=True, text=True, timeout=300)
                out = p.stdout + "\n" + p.stderr
                if re.search(rf"^--- FAIL: {re.escape(name)} ", out, re.M) or p.returncode != 0:
                    r["tests"][name] = "fail"
                elif re.search(r"^ok\s", out, re.M):
                    r["tests"][name] = "pass"
                else:
                    r["tests"][name] = "fail"
            except subprocess.TimeoutExpired:
                r["tests"][name] = "fail"
        r["elapsed_s"] = round(time.time() - t0, 1)
        earned = sum(weights[n] for n, v in r["tests"].items() if v == "pass")
        total = sum(weights.values())
        r["score"] = round(earned / total * 100, 1); r["earned_raw"] = earned
        for s in sorted(sprints):
            if all(r["tests"].get(t) == "pass" for t in sprints[s]):
                r["max_sprint_cleared"] = s
            else:
                break
    except subprocess.TimeoutExpired:
        r["error"] = "TIMEOUT (deadlock/incoherent)"
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", default="raft", choices=list(CONFIG) + ["typedlang"])
    ap.add_argument("--src"); ap.add_argument("--slug")
    a = ap.parse_args()
    if a.problem not in CONFIG:
        ap.error(f"problem {a.problem} not configured yet")
    cfg = CONFIG[a.problem]
    if a.slug and not a.src:
        a.src = str(REPO / cfg["out"] / a.slug / "project")
    if not a.src:
        ap.error("need --src or --slug")
    src = Path(a.src); slug = a.slug or src.parent.name
    r = grade(a.problem, src, slug)
    print(json.dumps(r, indent=2))
    print(f"\n==> [{a.problem}] {slug}: score {r['score']}/100, cleared {r['max_sprint_cleared']}, compile={r['compile_ok']}")
    outdir = REPO / cfg["out"] / slug
    if outdir.exists():
        (outdir / "grade.json").write_text(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
