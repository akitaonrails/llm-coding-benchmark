#!/usr/bin/env python3
"""Drive a v4.2 problem across models: run the (one-shot) sprint per model
(resume-aware, serial for shield safety), then grade each continuously.

Usage: run_v42_wave.py --problem complexity --sprint 01_rangekth --models a,b,c
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def out_dir(problem: str) -> Path:
    return REPO / "results-v4.2" / problem


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", default="complexity")
    ap.add_argument("--sprint", required=True)
    ap.add_argument("--models", required=True)
    ap.add_argument("--config", default=str(REPO / "config" / "models_v42.json"))
    ap.add_argument("--skip-grade", action="store_true")
    a = ap.parse_args()
    OUT = out_dir(a.problem)
    slugs = [s.strip() for s in a.models.split(",") if s.strip()]
    summary = []
    for slug in slugs:
        print(f"\n########## v4.2/{a.problem} MODEL: {slug} ##########", flush=True)
        ds_dir = OUT / slug / "project" / "ds"
        done = ds_dir.exists() and any(ds_dir.glob("*.go"))
        if done:
            print(f"[{slug}] model source present (project/ds/*.go) — skipping (resume)", flush=True)
        else:
            subprocess.run([sys.executable, str(REPO / "scripts" / "run_v42_sprint.py"),
                            "--problem", a.problem, "--model", slug, "--sprint", a.sprint,
                            "--config", a.config], cwd=REPO)
        rec = {"slug": slug}
        if not a.skip_grade:
            print(f"[{slug}] grading ...", flush=True)
            subprocess.run([sys.executable, str(REPO / "scripts" / "run_v42_grade.py"),
                            "--problem", a.problem, "--slug", slug], cwd=REPO)
            gj = OUT / slug / "grade.json"
            if gj.exists():
                try:
                    d = json.loads(gj.read_text())
                    rec.update(score=d.get("score"), correctness=d.get("correctness"),
                               quality=d.get("quality"), at_n=d.get("quality_at_n"),
                               build_ok=d.get("build_ok"), notes=d.get("notes"))
                except Exception:
                    pass
        summary.append(rec)
        print(f"==> [{a.problem}] {slug}: score={rec.get('score')} "
              f"corr={rec.get('correctness')} quality={rec.get('quality')} @n={rec.get('at_n')}", flush=True)
    print(f"\n========== v4.2/{a.problem} WAVE SUMMARY ==========", flush=True)
    for r in sorted(summary, key=lambda x: (x.get('score') or 0), reverse=True):
        print(f"  {r['slug']:24} score={r.get('score')} corr={r.get('correctness')} q={r.get('quality')}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_wave_summary.json").write_text(json.dumps(summary, indent=2))
    print("### WAVE DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
