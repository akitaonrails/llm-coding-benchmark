#!/usr/bin/env python3
"""Run ONE v4 sprint across a WAVE of models sequentially, with ABORT-EARLY.

The v4 shield moves all sibling results dirs aside per run, so models MUST run one at a
time (never in parallel). This wraps run_v4_sprint.py for a list of models and:
  - SKIPS any model already marked DNF (results-v4/<slug>/DNF exists) — a weak model that
    failed to build early self-drops instead of burning all 7 sprints of spend.
  - After each run, reads sprint.result.json and marks DNF when the model clearly failed:
    stall_aborted, OR exit!=0 with ~no tokens (auth/crash), OR (sprint>=02) the project has
    no Rails app (app/ + Gemfile missing). Benign exit -15 WITH tokens (kimi lingers) is OK.
  - Writes a wave status line per model to results-v4/_wave_status/<sprint>.log.

The hardened run_v4_sprint.py self-heals any stranded shield at startup, so a killed wave can
simply be re-run for the same sprint — completed models are cheap re-runs only if forced; here
we DON'T force, so a model whose sprint dir already exists is left as-is unless --redo.

Usage: run_v4_wave.py --sprint 01_foundation --models v2_a,v2_b,...  [--config ...] [--redo]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results-v4"
DNF_TOKEN_FLOOR = 2000  # below this with a nonzero/failed exit = DNF (no real work)


def is_dnf(model: str) -> bool:
    return (OUT / model / "DNF").exists()


def mark_dnf(model: str, reason: str) -> None:
    (OUT / model).mkdir(parents=True, exist_ok=True)
    (OUT / model / "DNF").write_text(reason + "\n")


def project_has_rails(model: str) -> bool:
    proj = OUT / model / "project"
    return (proj / "Gemfile").exists() and (proj / "app").is_dir()


def evaluate(model: str, sprint: str) -> tuple[bool, str]:
    """Return (dnf, reason) by inspecting the just-written sprint.result.json + project."""
    # find the sprint dir (basename may be sprintNN_name)
    sprints = OUT / model / "sprints"
    cand = sorted(sprints.glob(f"sprint{sprint}*")) or sorted(sprints.glob(f"*{sprint}*"))
    if not cand:
        return True, f"no sprint dir for {sprint}"
    rj = cand[-1] / "sprint.result.json"
    if not rj.exists():
        return True, "no sprint.result.json (run did not complete)"
    d = json.loads(rj.read_text())
    exit_code = d.get("exit_code")
    toks = d.get("tokens_total") or 0
    if d.get("stall_aborted"):
        return True, "stall_aborted"
    if exit_code not in (0, -15, 143) and toks < DNF_TOKEN_FLOOR:
        return True, f"exit={exit_code} tokens={toks} (crash/auth, no real work)"
    # from sprint 02 on, a completed run must have produced a Rails app
    if not sprint.startswith("01") and not project_has_rails(model):
        return True, "no Rails app in project/ (Gemfile+app/ missing)"
    return False, f"ok exit={exit_code} tokens={toks} cost=${d.get('cost_usd')}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprint", required=True)
    ap.add_argument("--models", required=True, help="comma-separated slugs")
    ap.add_argument("--config", default=str(REPO / "config" / "models_v2.json"))
    ap.add_argument("--redo", action="store_true", help="re-run even if sprint dir exists")
    a = ap.parse_args()
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    statusdir = OUT / "_wave_status"; statusdir.mkdir(parents=True, exist_ok=True)
    log = statusdir / f"{a.sprint}.log"

    def note(s: str):
        line = f"{time.strftime('%H:%M:%S')} {s}"
        print(line, flush=True)
        with open(log, "a") as f:
            f.write(line + "\n")

    note(f"=== WAVE sprint {a.sprint} : {len(models)} models ===")
    for m in models:
        if is_dnf(m):
            note(f"SKIP {m} (already DNF)")
            continue
        # skip if this sprint already ran (no --redo) — idempotent resume after a kill
        sprints = OUT / m / "sprints"
        done = sprints.glob(f"sprint{a.sprint}*") if sprints.exists() else []
        if not a.redo and any((p / "sprint.result.json").exists() for p in done):
            note(f"SKIP {m} (sprint {a.sprint} already done)")
            continue
        note(f"RUN  {m} sprint {a.sprint} ...")
        subprocess.run([sys.executable, str(REPO / "scripts" / "run_v4_sprint.py"),
                        "--model", m, "--sprint", a.sprint, "--config", a.config])
        dnf, reason = evaluate(m, a.sprint)
        if dnf:
            mark_dnf(m, f"sprint {a.sprint}: {reason}")
            note(f"DNF  {m} — {reason} (dropped from remaining sprints)")
        else:
            note(f"DONE {m} — {reason}")
    note(f"=== WAVE sprint {a.sprint} complete ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
