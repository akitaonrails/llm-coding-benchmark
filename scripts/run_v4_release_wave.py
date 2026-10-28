#!/usr/bin/env python3
"""Serial, resumable five-model v4 release wave with boundary checkpoints."""

from __future__ import annotations

import json
import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from run_v4_wave import evaluate

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results-v4"
STATE = Path("/tmp/v4-release-wave-20261027")
STATUS = STATE / "status.json"
SLUGS = (
    "v2_gemini_4_argon_high",
    "v2_claude_sonnet_5_5",
    "v2_kimi_k3_1_pro",
    "v2_gpt_6_1_sol",
    "v2_gpt_6_1_terra",
)
SPRINTS = ("01_foundation", "02_multiuser", "03_admin", "04_reports",
           "05_api", "06_production", "07_reveal")
CONFIG = REPO / "config" / "models_v2.json"
ACTIVE: subprocess.Popen | None = None
# v4_release_boundary.py exits 3 when a grade-only boundary is waiting for a
# human-planted injection. That parks the model at a gate, not a pause.
EXIT_AWAITING = 3


def gate_waiting(root: Path) -> bool:
    """True while a gate has no newer human injection record to re-check."""
    marker = root / "boundaries" / "AWAITING_INJECTION.json"
    if not marker.is_file():
        return False
    record = root / "boundaries" / "human_injections.json"
    return not record.is_file() or record.stat().st_mtime <= marker.stat().st_mtime


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_status(**changes: object) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    prior = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    prior.update(changes)
    prior["updated_at"] = now()
    prior["supervisor_pid"] = os.getpid()
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(prior, indent=2) + "\n")
    tmp.replace(STATUS)


def stop(signum: int, _frame: object) -> None:
    if ACTIVE and ACTIVE.poll() is None:
        os.killpg(ACTIVE.pid, signal.SIGTERM)
    write_status(state="stopping", signal=signum)
    raise SystemExit(128 + signum)


def launch(argv: list[str], log: Path, *, env: dict[str, str] | None = None) -> int:
    global ACTIVE
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("ab") as output:
        ACTIVE = subprocess.Popen(argv, cwd=REPO, env=env, stdout=output,
                                  stderr=subprocess.STDOUT, start_new_session=True)
        started = time.monotonic()
        try:
            while ACTIVE.poll() is None:
                write_status(child_pid=ACTIVE.pid,
                             stage_elapsed_seconds=round(time.monotonic() - started))
                time.sleep(15)
            return ACTIVE.returncode or 0
        finally:
            ACTIVE = None
            write_status(child_pid=None)


def pause(slug: str, stage: str, reason: str) -> None:
    path = OUT / slug / "PAUSED.release-wave.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"at": now(), "stage": stage, "reason": reason}, indent=2) + "\n")
    write_status(state="model_paused", model=slug, stage=stage, note=reason)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(SLUGS),
                    help="comma-separated release-wave model slugs")
    ap.add_argument("--allow-gemini-fallback", action="store_true",
                    help="allow OpenRouter Gemini after an Antigravity attempt")
    args = ap.parse_args()
    selected = tuple(s.strip() for s in args.models.split(",") if s.strip())
    if not selected or len(set(selected)) != len(selected):
        raise SystemExit("model selection must be nonempty and unique")
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    registry = json.loads(CONFIG.read_text())["models"]
    ids = {m["slug"] for m in registry}
    missing = set(selected) - ids
    if missing:
        raise SystemExit(f"missing model registrations: {sorted(missing)}")
    # The already-running first guard queues the OpenRouter slug. Defer that
    # request without touching its active candidate; the recovery guard tries
    # Antigravity first and explicitly opts into fallback only if needed.
    if "v2_gemini_4_argon_high_or" in selected and not args.allow_gemini_fallback:
        write_status(state="deferred", model="v2_gemini_4_argon_high_or",
                     note="Gemini routing: try Antigravity before OpenRouter")
        return 0
    # The OpenRouter fallback is for Antigravity infrastructure failures only. A
    # run stopped at a review boundary would hit the same reviewer on OpenRouter;
    # it continues through an injection gate instead.
    agy = OUT / "v2_gemini_4_argon_high_agy"
    agy_pause = agy / "PAUSED.release-wave.json"
    if "v2_gemini_4_argon_high_or" in selected and (
            (agy / "boundaries" / "AWAITING_INJECTION.json").is_file()
            or (agy_pause.is_file()
                and json.loads(agy_pause.read_text()).get("stage", "").startswith("boundary"))):
        write_status(state="deferred", model="v2_gemini_4_argon_high_or",
                     note="Antigravity Argon stopped at a review boundary; no OpenRouter rerun")
        return 0
    if not (REPO / "benchmark-v4" / "PROTOCOL.md").is_file():
        raise SystemExit("v4 protocol is shielded or absent; refusing to start")
    write_status(state="starting", models=list(selected), completed=[], paused=[])
    completed: list[str] = []
    paused: list[str] = []
    awaiting: list[str] = []
    for slug in selected:
        root = OUT / slug
        if (root / "grade.json").is_file():
            completed.append(slug)
            write_status(state="already_complete", model=slug, completed=completed)
            continue
        if (root / "PAUSED.release-wave.json").exists():
            paused.append(slug)
            write_status(state="already_paused", model=slug, paused=paused)
            continue
        if gate_waiting(root):
            awaiting.append(slug)
            write_status(state="awaiting_injection", model=slug, awaiting=awaiting)
            continue
        for number, sprint in enumerate(SPRINTS, 1):
            stage = f"sprint{number:02d}"
            sprint_dir = root / "sprints" / f"sprint{sprint}"
            result = sprint_dir / "sprint.result.json"
            if not result.is_file():
                write_status(state="running", model=slug, stage=stage,
                             completed=completed, paused=paused, note="candidate sprint")
                env = os.environ.copy()
                env["V4_PHASE_TIMEOUT"] = "14400"
                env["V4_STALL_TIMEOUT"] = "1800"
                code = launch([sys.executable, str(REPO / "scripts" / "run_v4_sprint.py"),
                               "--model", slug, "--sprint", sprint,
                               "--config", str(CONFIG)],
                              STATE / "logs" / f"{slug}-{stage}.log", env=env)
                if code:
                    pause(slug, stage, f"runner exited {code}; inspect sprint and shield evidence")
                    break
            failed, reason = evaluate(slug, f"{number:02d}")
            if failed or not result.is_file():
                pause(slug, stage, reason if failed else "missing sprint result")
                break
            if number == 1:
                project = root / "project"
                if not (project / "Gemfile").is_file() or not (project / "app").is_dir():
                    pause(slug, stage, "foundation produced no Rails app; inspect before classification")
                    break
            boundary = f"boundary{number:02d}"
            write_status(state="reviewing", model=slug, stage=boundary,
                         completed=completed, paused=paused,
                         note="independent grade and injection")
            code = launch([sys.executable, str(REPO / "scripts" / "v4_release_boundary.py"),
                           slug, str(number)],
                          STATE / "logs" / f"{slug}-{boundary}.log")
            if code == EXIT_AWAITING:
                write_status(state="awaiting_injection", model=slug, stage=boundary,
                             note="grade-only boundary waits for human-planted items")
                break
            if code:
                pause(slug, boundary, f"review failed exit={code}; see boundary verdict and transcript")
                break
        if (root / "grade.json").is_file():
            completed.append(slug)
            write_status(state="model_complete", model=slug,
                         completed=completed, paused=paused, note="final grade written")
        elif (root / "boundaries" / "AWAITING_INJECTION.json").is_file():
            awaiting.append(slug)
        else:
            paused.append(slug)
    state = "needs_review" if paused else "awaiting_injection" if awaiting else "complete"
    write_status(state=state, model=None, stage=None, completed=completed,
                 paused=paused, awaiting=awaiting,
                 note="Selected models attempted; inspect paused reasons and injection gates")
    return 2 if paused else EXIT_AWAITING if awaiting else 0


if __name__ == "__main__":
    raise SystemExit(main())
