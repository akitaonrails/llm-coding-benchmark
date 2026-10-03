#!/usr/bin/env python3
"""Drive the full v4.1 P1 (Raft) benchmark: all 8 sprints per model (resume-aware), abort-early on
incoherence (the OSS-DNF signal), then grade each with run_v41_grade.

Serialized by design (run_v41_sprint shields per sprint). Usage:
  run_v41_wave.py --models v2_genesys_pi_house,v41_fable_5_1,...   [--config config/models_v41.json]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results-v4.1"
SPRINTS = ["01_election","02_replication","03_persistence","04_snapshots",
           "05_membership","06_learners","07_kv","08_reveal"]


def project_builds(proj: Path) -> bool:
    if not (proj / "raft").exists():
        return False
    r = subprocess.run(["go", "build", "./..."], cwd=proj, capture_output=True, text=True, timeout=300)
    return r.returncode == 0


def has_raft_src(proj: Path) -> bool:
    return any((proj / "raft").glob("*.go")) if (proj / "raft").exists() else False


def run_model(slug: str, config: str) -> dict:
    out_root = OUT / slug
    proj = out_root / "project"
    rec = {"slug": slug, "sprints_run": [], "dnf": False, "dnf_reason": None}
    compile_fail_streak = 0
    for sp in SPRINTS:
        sprint_dir = out_root / "sprints" / f"sprint{sp}"
        if sprint_dir.exists():
            print(f"[{slug}] sprint {sp} already present — skipping (resume)")
            rec["sprints_run"].append(sp)
            continue
        print(f"[{slug}] === sprint {sp} ===")
        t0 = time.time()
        p = subprocess.run([sys.executable, str(REPO/"scripts"/"run_v41_sprint.py"),
                            "--model", slug, "--sprint", sp, "--config", config],
                           cwd=REPO)
        rec["sprints_run"].append(sp)
        # abort-early checks
        if not has_raft_src(proj) and sp != "01_election":
            rec["dnf"] = True; rec["dnf_reason"] = f"no raft/*.go after sprint {sp}"; break
        try:
            builds = project_builds(proj)
        except Exception as e:
            builds = False
        if builds:
            compile_fail_streak = 0
        else:
            compile_fail_streak += 1
            print(f"[{slug}] sprint {sp}: project does NOT compile (streak {compile_fail_streak})")
            if compile_fail_streak >= 2:
                rec["dnf"] = True; rec["dnf_reason"] = f"2 consecutive non-compiling sprints (through {sp})"; break
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True, help="comma-separated slugs")
    ap.add_argument("--config", default=str(REPO / "config" / "models_v41.json"))
    ap.add_argument("--skip-grade", action="store_true")
    a = ap.parse_args()
    slugs = [s.strip() for s in a.models.split(",") if s.strip()]
    summary = []
    for slug in slugs:
        print(f"\n########## v4.1 MODEL: {slug} ##########")
        rec = run_model(slug, a.config)
        if not a.skip_grade:
            print(f"[{slug}] grading ...")
            g = subprocess.run([sys.executable, str(REPO/"scripts"/"run_v41_grade.py"), "--slug", slug],
                               cwd=REPO, capture_output=True, text=True)
            print(g.stdout[-600:])
            gj = OUT / slug / "grade.json"
            score = depth = None
            if gj.exists():
                try:
                    d = json.loads(gj.read_text()); score = d.get("score"); depth = d.get("max_sprint_cleared")
                except Exception: pass
            rec["score"] = score; rec["sprints_cleared"] = depth
        summary.append(rec)
        print(f"[{slug}] DONE dnf={rec['dnf']} score={rec.get('score')} cleared={rec.get('sprints_cleared')}/8")
    print("\n========== v4.1 WAVE SUMMARY ==========")
    for r in summary:
        print(f"  {r['slug']:28} score={r.get('score')} cleared={r.get('sprints_cleared')}/8 "
              f"dnf={r['dnf']} {r.get('dnf_reason') or ''}")
    (OUT / "_wave_summary.json").write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
