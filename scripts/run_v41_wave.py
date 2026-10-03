#!/usr/bin/env python3
"""Drive a full v4.1 problem across models: all sprints per model (resume-aware), abort-early on incoherence
(the OSS-DNF signal), then grade each. Problem-parameterized.

Usage: run_v41_wave.py --problem storage --models v2_genesys_pi_house,v41_fable_5_1,... [--config ...]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def out_dir_for(problem: str) -> Path:
    return REPO / "results-v4.1" if problem == "raft" else REPO / "results-v4.1" / problem


def sprints_for(problem: str) -> list[str]:
    pdir = REPO / "benchmark-v4.1" / problem / "prompts"
    names = []
    for f in sorted(pdir.glob("sprint*.txt")):
        names.append(f.stem[len("sprint"):])  # sprint01_btree.txt -> 01_btree
    return names


def model_src_go(proj: Path) -> list[Path]:
    return [p for p in proj.rglob("*.go")
            if "/harness/" not in str(p) and not p.name.endswith("_test.go")]


def project_builds(proj: Path) -> bool:
    if not any(model_src_go(proj)):
        return False
    try:
        r = subprocess.run(["go", "build", "./..."], cwd=proj, capture_output=True, text=True, timeout=300)
        return r.returncode == 0
    except Exception:
        return False


def run_model(problem: str, slug: str, config: str) -> dict:
    OUT = out_dir_for(problem)
    out_root = OUT / slug
    proj = out_root / "project"
    rec = {"slug": slug, "sprints_run": [], "dnf": False, "dnf_reason": None}
    fail_streak = 0
    SPRINTS = sprints_for(problem)
    for i, sp in enumerate(SPRINTS):
        sprint_dir = out_root / "sprints" / f"sprint{sp}"
        if sprint_dir.exists():
            print(f"[{slug}] sprint {sp} present — skipping (resume)"); rec["sprints_run"].append(sp); continue
        print(f"[{problem}/{slug}] === sprint {sp} ===")
        subprocess.run([sys.executable, str(REPO/"scripts"/"run_v41_sprint.py"),
                        "--problem", problem, "--model", slug, "--sprint", sp, "--config", config], cwd=REPO)
        rec["sprints_run"].append(sp)
        if i >= 1 and not any(model_src_go(proj)):
            rec["dnf"] = True; rec["dnf_reason"] = f"no model source after sprint {sp}"; break
        if project_builds(proj):
            fail_streak = 0
        else:
            fail_streak += 1
            print(f"[{slug}] sprint {sp}: does NOT compile (streak {fail_streak})")
            if fail_streak >= 2:
                rec["dnf"] = True; rec["dnf_reason"] = f"2 consecutive non-compiling sprints (through {sp})"; break
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True, choices=["raft", "storage", "typedlang"])
    ap.add_argument("--models", required=True)
    ap.add_argument("--config", default=str(REPO / "config" / "models_v41.json"))
    ap.add_argument("--skip-grade", action="store_true")
    a = ap.parse_args()
    OUT = out_dir_for(a.problem)
    slugs = [s.strip() for s in a.models.split(",") if s.strip()]
    summary = []
    for slug in slugs:
        print(f"\n########## v4.1/{a.problem} MODEL: {slug} ##########")
        rec = run_model(a.problem, slug, a.config)
        if not a.skip_grade:
            print(f"[{slug}] grading ...")
            subprocess.run([sys.executable, str(REPO/"scripts"/"run_v41_grade.py"),
                            "--problem", a.problem, "--slug", slug], cwd=REPO)
            gj = OUT / slug / "grade.json"
            if gj.exists():
                try:
                    d = json.loads(gj.read_text()); rec["score"] = d.get("score"); rec["sprints_cleared"] = d.get("max_sprint_cleared")
                except Exception: pass
        summary.append(rec)
        print(f"[{slug}] DONE dnf={rec['dnf']} score={rec.get('score')} cleared={rec.get('sprints_cleared')}")
    print(f"\n========== v4.1/{a.problem} WAVE SUMMARY ==========")
    for r in summary:
        print(f"  {r['slug']:28} score={r.get('score')} cleared={r.get('sprints_cleared')} dnf={r['dnf']} {r.get('dnf_reason') or ''}")
    (OUT / "_wave_summary.json").parent.mkdir(parents=True, exist_ok=True)
    (OUT / "_wave_summary.json").write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
