#!/usr/bin/env python3
"""Drive the October release wave through grade-only injection gates.

Waits for the running recovery guard to exit, then repeatedly runs the serial
wave controller for the selected models. A review that stopped because the
review service rejected an injection (boundaries 02-05) becomes an injection
gate: the model switches to grade-only boundaries and waits for human-planted
items (scripts/v4_record_injection.py). The rejected operation is never retried
by a reviewer. Other pauses stay paused for a person to classify.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from v4_release_guard import process_has

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results-v4"
STATE = Path("/tmp/v4-release-wave-20261027")
MODES = STATE / "boundary-modes.json"
LOG = STATE / "gates.log"
GATE_ITEMS = {2: "#1-3", 3: "#4-6", 4: "#7-9", 5: "#10-14"}
EXIT_AWAITING = 3


def note(message: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as log:
        log.write(f"{datetime.now(timezone.utc).isoformat()} {message}\n")


def rejected_by_reviewer(root: Path, number: int) -> bool:
    verdicts = sorted((root / "boundaries").glob(f"sprint{number:02d}-release-*/verdict.json"))
    if not verdicts:
        return False
    reason = str(json.loads(verdicts[-1].read_text()).get("reason", "")).lower()
    return "review service rejected" in reason or "security control" in reason


def open_gates_for_rejections(slugs: tuple[str, ...]) -> None:
    modes = json.loads(MODES.read_text()) if MODES.is_file() else {}
    for slug in slugs:
        root = OUT / slug
        pause = root / "PAUSED.release-wave.json"
        if not pause.is_file():
            continue
        data = json.loads(pause.read_text())
        stage = str(data.get("stage", ""))
        if not stage.startswith("boundary") or int(stage[-2:]) not in GATE_ITEMS:
            continue
        number = int(stage[-2:])
        if not rejected_by_reviewer(root, number):
            continue
        pause.rename(root / f"PAUSED.release-wave.resolved-{time.time_ns()}.json")
        (root / "boundaries" / "AWAITING_INJECTION.json").write_text(json.dumps({
            "sprint": number, "items": GATE_ITEMS[number],
            "reason": f"awaiting_injection: {GATE_ITEMS[number]} — converted from reviewer "
                      f"safety stop on {data.get('at')}; plant by hand, then record",
            "evidence": f"see the latest sprint{number:02d}-release-* boundary report",
            "opened_at": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
        modes[slug] = "grade-only"
        note(f"{slug}: reviewer rejection at {stage} converted to injection gate")
    MODES.write_text(json.dumps(modes, indent=2) + "\n")


def gate_ready(root: Path) -> bool:
    marker = root / "boundaries" / "AWAITING_INJECTION.json"
    record = root / "boundaries" / "human_injections.json"
    return (marker.is_file() and record.is_file()
            and record.stat().st_mtime > marker.stat().st_mtime)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait-pid", type=int, required=True)
    ap.add_argument("--wait-token", default="v4_release_guard.py")
    ap.add_argument("--models", required=True)
    args = ap.parse_args()
    slugs = tuple(s.strip() for s in args.models.split(",") if s.strip())
    while process_has(args.wait_pid, args.wait_token):
        time.sleep(30)
    note(f"guard {args.wait_pid} exited; driving {','.join(slugs)}")
    backoff = 0
    while True:
        open_gates_for_rejections(slugs)
        code = subprocess.run([sys.executable, str(REPO / "scripts" / "run_v4_release_wave.py"),
                               "--models", ",".join(slugs)], cwd=REPO).returncode
        open_gates_for_rejections(slugs)
        gated = [s for s in slugs if (OUT / s / "boundaries" / "AWAITING_INJECTION.json").is_file()]
        note(f"wave pass exited {code}; open gates: {gated or 'none'}")
        if not gated:
            return code
        # A pass that exits with an unexpected code (e.g. a crash on a full disk)
        # must never hot-loop, even when a gate already has a recorded injection:
        # back off so a persistent failure can neither spin the CPU nor flood the
        # tmp quota with status/log writes.
        if code not in (2, 3):
            backoff = min(backoff + 1, 6)
            note(f"unexpected exit {code}; backing off {30 * backoff}s before retry")
            time.sleep(30 * backoff)
            continue
        backoff = 0
        while not any(gate_ready(OUT / s) for s in gated):
            time.sleep(60)
        note("human injection recorded; re-checking gates")


if __name__ == "__main__":
    raise SystemExit(main())
