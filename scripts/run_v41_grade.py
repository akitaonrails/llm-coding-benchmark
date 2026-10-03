#!/usr/bin/env python3
"""Grade a v4.1 P1 (Raft) submission.

SECURE grading: build a CLEAN workspace from the known-good harness+grader and drop in ONLY the
model's raft/ + kvraft/ source, so a model cannot tamper with the harness/grader to pass. Then run
the hidden gauntlet under -race and score per-test.

Usage:
  run_v41_grade.py --src <dir-with-raft-and-kvraft>   # e.g. results-v4.1/<slug>/project  OR a ref dir
  run_v41_grade.py --slug <slug>                       # shorthand for results-v4.1/<slug>/project
"""
from __future__ import annotations
import argparse, json, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAFT = REPO / "benchmark-v4.1" / "raft"
OUT = REPO / "results-v4.1"

# Per-test weights (sum = 100). Foundation is cheap points; the apex (membership, learners, KV
# linearizability) carries the weight — that is where frontier vs OSS separates.
WEIGHTS = {
    "TestInitialElection": 2, "TestReElection": 2, "TestPreVote": 4, "TestCheckQuorum": 4,
    "TestBasicAgree": 2, "TestFailAgree": 2, "TestFailNoAgree": 3,
    "TestConcurrentStarts": 3, "TestRejoin": 4, "TestBackup": 4,
    "TestPersist1": 3, "TestPersist2": 3, "TestPersist3": 3,
    "TestSnapshotBasic": 4, "TestSnapshotInstall": 5, "TestSnapshotCrash": 5,
    "TestMembershipJoint": 10, "TestLearnerCatchup": 8, "TestLeadershipTransfer": 5,
    "TestKVBasic": 3, "TestKVConcurrent": 4, "TestKVPartition": 5,
    "TestKVSnapshotSize": 4, "TestKVLinearizable": 12,
}
# which sprint each test belongs to (for "depth cleared" reporting)
SPRINT = {
    1: ["TestInitialElection","TestReElection","TestPreVote"],
    2: ["TestBasicAgree","TestFailAgree","TestFailNoAgree","TestConcurrentStarts","TestRejoin","TestBackup"],
    3: ["TestPersist1","TestPersist2","TestPersist3"],
    4: ["TestSnapshotBasic","TestSnapshotInstall","TestSnapshotCrash"],
    5: ["TestMembershipJoint"],
    6: ["TestLearnerCatchup","TestLeadershipTransfer","TestCheckQuorum"],
    7: ["TestKVBasic","TestKVConcurrent","TestKVPartition","TestKVSnapshotSize"],
    8: ["TestKVLinearizable"],
}

RAFT_WIRING = '''package grader
import (
  "testing"
  "v41raft/harness"
  "v41raft/harness/labrpc"
  "v41raft/raft"
)
func mMake(peers []*labrpc.ClientEnd, me int, p *harness.Persister, ch chan harness.ApplyMsg, initial harness.Config) harness.RaftNode {
  return raft.Make(peers, me, p, ch, initial)
}
func TestInitialElection(t *testing.T)  { RunInitialElection(t, mMake) }
func TestReElection(t *testing.T)       { RunReElection(t, mMake) }
func TestPreVote(t *testing.T)          { RunPreVote(t, mMake) }
func TestCheckQuorum(t *testing.T)      { RunCheckQuorum(t, mMake) }
func TestBasicAgree(t *testing.T)       { RunBasicAgree(t, mMake) }
func TestFailAgree(t *testing.T)        { RunFailAgree(t, mMake) }
func TestFailNoAgree(t *testing.T)      { RunFailNoAgree(t, mMake) }
func TestConcurrentStarts(t *testing.T) { RunConcurrentStarts(t, mMake) }
func TestRejoin(t *testing.T)           { RunRejoin(t, mMake) }
func TestBackup(t *testing.T)           { RunBackup(t, mMake) }
func TestPersist1(t *testing.T)         { RunPersist1(t, mMake) }
func TestPersist2(t *testing.T)         { RunPersist2(t, mMake) }
func TestPersist3(t *testing.T)         { RunPersist3(t, mMake) }
func TestSnapshotBasic(t *testing.T)      { RunSnapshotBasic(t, mMake) }
func TestSnapshotInstall(t *testing.T)    { RunSnapshotInstall(t, mMake) }
func TestSnapshotCrash(t *testing.T)      { RunSnapshotCrash(t, mMake) }
func TestMembershipJoint(t *testing.T)    { RunMembershipJoint(t, mMake) }
func TestLearnerCatchup(t *testing.T)     { RunLearnerCatchup(t, mMake) }
func TestLeadershipTransfer(t *testing.T) { RunLeadershipTransfer(t, mMake) }
'''
KV_WIRING = '''package grader
import (
  "testing"
  "v41raft/harness"
  "v41raft/harness/labrpc"
  "v41raft/kvraft"
)
var mKV = KVImpl{
  MakeServer: func(servers []*labrpc.ClientEnd, me int, persister *harness.Persister, maxraftstate int, initial harness.Config) KVServerHandle {
    return kvraft.StartKVServer(servers, me, persister, maxraftstate, initial)
  },
  MakeClerk: func(ends []*labrpc.ClientEnd) KVClerk { return kvraft.MakeClerk(ends) },
}
func TestKVBasic(t *testing.T)        { RunKVBasic(t, mKV) }
func TestKVConcurrent(t *testing.T)   { RunKVConcurrent(t, mKV) }
func TestKVPartition(t *testing.T)    { RunKVPartition(t, mKV) }
func TestKVSnapshotSize(t *testing.T) { RunKVSnapshotSize(t, mKV) }
func TestKVLinearizable(t *testing.T) { RunKVLinearizable(t, mKV) }
'''


def build_workspace(src: Path, ws: Path) -> str | None:
    """Assemble clean grading workspace. Returns error string, or None on success."""
    ws.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RAFT / "go.mod", ws / "go.mod")
    # known-good harness (incl porcupine) + parameterized grader logic (NO *_test.go, NO reference/)
    shutil.copytree(RAFT / "harness", ws / "harness")
    (ws / "grader").mkdir()
    for f in ("suite.go", "kvsuite.go", "extended.go"):
        shutil.copy2(RAFT / "grader" / f, ws / "grader" / f)
    # the MODEL's source only
    for pkg in ("raft", "kvraft"):
        srcpkg = src / pkg
        if not srcpkg.is_dir():
            return f"missing package dir: {pkg}/ (model did not implement it)"
        # copy only .go files (skip any *_test.go the model wrote, and any stray dirs)
        (ws / pkg).mkdir()
        for gf in srcpkg.glob("*.go"):
            if gf.name.endswith("_test.go"):
                continue
            shutil.copy2(gf, ws / pkg / gf.name)
    # grading wiring
    (ws / "grader" / "z_wire_raft_test.go").write_text(RAFT_WIRING)
    (ws / "grader" / "z_wire_kv_test.go").write_text(KV_WIRING)
    return None


def grade(src: Path, slug: str) -> dict:
    ws = Path(tempfile.mkdtemp(prefix=f"v41grade_{slug}_"))
    result = {"slug": slug, "src": str(src), "tests": {}, "score": 0.0,
              "max_sprint_cleared": 0, "compile_ok": False, "error": None}
    try:
        err = build_workspace(src, ws)
        if err:
            result["error"] = err
            return result
        # compile gate
        b = subprocess.run(["go", "vet", "./..."], cwd=ws, capture_output=True, text=True, timeout=300)
        bb = subprocess.run(["go", "build", "./..."], cwd=ws, capture_output=True, text=True, timeout=300)
        if bb.returncode != 0:
            result["error"] = "compile failed (contract mismatch):\n" + (bb.stderr or b.stderr)[:1500]
            return result
        result["compile_ok"] = True
        # run gauntlet, per-test
        t0 = time.time()
        p = subprocess.run(["go", "test", "-race", "-v", "-count=1", "-timeout", "25m", "./grader/"],
                           cwd=ws, capture_output=True, text=True, timeout=2000)
        result["elapsed_s"] = round(time.time() - t0, 1)
        out = p.stdout + "\n" + p.stderr
        for name in WEIGHTS:
            m_pass = re.search(rf"^--- PASS: {re.escape(name)} ", out, re.M)
            m_fail = re.search(rf"^--- FAIL: {re.escape(name)} ", out, re.M)
            if m_pass and not m_fail:
                result["tests"][name] = "pass"
            elif m_fail:
                result["tests"][name] = "fail"
            else:
                result["tests"][name] = "missing"   # panic before report / not run
        # score (normalized to /100 regardless of weight sum)
        earned = sum(WEIGHTS[n] for n, v in result["tests"].items() if v == "pass")
        total = sum(WEIGHTS.values())
        result["score"] = round(earned / total * 100, 1)
        result["earned_raw"] = earned
        # depth: highest sprint all of whose tests passed
        for s in range(1, 9):
            if all(result["tests"].get(t) == "pass" for t in SPRINT[s]):
                result["max_sprint_cleared"] = s
            else:
                break
        result["raw_tail"] = out[-1200:]
    except subprocess.TimeoutExpired:
        result["error"] = "TIMEOUT (likely deadlock/incoherent — OSS-DNF signature)"
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="dir containing raft/ and kvraft/")
    ap.add_argument("--slug", help="results-v4.1/<slug>/project shorthand")
    a = ap.parse_args()
    if a.slug and not a.src:
        a.src = str(OUT / a.slug / "project")
    if not a.src:
        ap.error("need --src or --slug")
    src = Path(a.src)
    slug = a.slug or src.parent.name
    r = grade(src, slug)
    print(json.dumps({k: v for k, v in r.items() if k != "raw_tail"}, indent=2))
    if r.get("error"):
        print("\n--- error detail ---\n" + str(r["error"])[:1000])
    print(f"\n==> {slug}: score {r['score']}/100, sprints cleared {r['max_sprint_cleared']}/8, "
          f"compile={r['compile_ok']}")
    # persist
    if (OUT / slug).exists():
        (OUT / slug / "grade.json").write_text(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
