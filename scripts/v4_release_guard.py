#!/usr/bin/env python3
"""Resume the October v4 wave after its interactive controller exits."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE = Path("/tmp/v4-release-wave-20261027")
STATUS = STATE / "status.json"
OUT = REPO / "results-v4"
MAIN = ("v2_claude_sonnet_5_5", "v2_kimi_k3_1_pro",
        "v2_gpt_6_1_sol", "v2_gpt_6_1_terra")
AGY_ARGON = "v2_gemini_4_argon_high_agy"
OR_ARGON = "v2_gemini_4_argon_high_or"


def process_has(pid: int, needle: str) -> bool:
    try:
        return needle.encode() in Path(f"/proc/{pid}/cmdline").read_bytes()
    except (FileNotFoundError, PermissionError):
        return False


def status() -> dict:
    try:
        return json.loads(STATUS.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def run(models: tuple[str, ...], *, allow_gemini_fallback: bool = False) -> int:
    log = STATE / "guard.log"
    command = [sys.executable, str(REPO / "scripts" / "run_v4_release_wave.py"),
               "--models", ",".join(models)]
    if allow_gemini_fallback:
        command.append("--allow-gemini-fallback")
    with log.open("ab") as output:
        return subprocess.run(command, cwd=REPO,
                              stdout=output, stderr=subprocess.STDOUT).returncode


def recover_boundary(slug: str) -> bool:
    root = OUT / slug
    pause = root / "PAUSED.release-wave.json"
    if not pause.is_file():
        return False
    data = json.loads(pause.read_text())
    stage = data.get("stage", "")
    if not (stage.startswith("boundary") and stage[-2:].isdigit()):
        return False
    number = int(stage[-2:])
    if number not in range(1, 8):
        return False
    # A provider security rejection is a hard stop, not an infrastructure
    # transient. Preserve the candidate and reviewer evidence without retrying
    # the rejected operation or routing it through another service.
    for verdict in (root / "boundaries").glob(f"sprint{number:02d}-release-*/verdict.json"):
        previous = json.loads(verdict.read_text())
        reason = str(previous.get("reason", "")).lower()
        if "review service rejected" in reason or "security control" in reason:
            return False
    log = STATE / "guard.log"
    with log.open("ab") as output:
        code = subprocess.run([sys.executable, str(REPO / "scripts" / "v4_release_boundary.py"),
                               slug, str(number)], cwd=REPO,
                              stdout=output, stderr=subprocess.STDOUT).returncode
    if code:
        return False
    pause.rename(root / f"PAUSED.release-wave.resolved-{time.time_ns()}.json")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait-pid", type=int, required=True)
    ap.add_argument("--wait-token", default="run_v4_release_wave.py")
    args = ap.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    while process_has(args.wait_pid, args.wait_token):
        time.sleep(30)
    # A terminated controller can leave its exact candidate/reviewer child alive.
    # Wait for that child rather than starting a concurrent shield owner.
    for _ in range(600):
        child = status().get("child_pid")
        if not child or not (process_has(child, "run_v4_sprint.py")
                             or process_has(child, "v4_release_boundary.py")):
            break
        time.sleep(30)
    else:
        (STATE / "guard-blocked.json").write_text(json.dumps({
            "at": datetime.now(timezone.utc).isoformat(),
            "reason": "prior candidate/reviewer child still active after five hours",
            "child_pid": child,
        }, indent=2) + "\n")
        return 2
    # Give incomplete reviewer artifacts a bounded recovery. A successful
    # recovery preserves the original pause marker as evidence, then resumes
    # the candidate from its existing sprint checkpoint. Never retry a
    # candidate sprint automatically or erase its raw output.
    for _ in range(3):
        recovered = any([recover_boundary(slug) for slug in MAIN])
        run(MAIN)
        if not recovered and not any((OUT / slug / "PAUSED.release-wave.json").is_file()
                                 for slug in MAIN):
            break
    run((AGY_ARGON,))
    if not (OUT / AGY_ARGON / "grade.json").is_file():
        run((OR_ARGON,), allow_gemini_fallback=True)

    release = OUT / "_release_wave_20261027"
    release.mkdir(parents=True, exist_ok=True)
    rows = []
    argon_slug = AGY_ARGON if (OUT / AGY_ARGON / "grade.json").is_file() else OR_ARGON
    for name, slug in (("Gemini 4 Argon", argon_slug),
                       ("Claude Sonnet 5.5", MAIN[0]),
                       ("Kimi K3.1 Pro", MAIN[1]),
                       ("GPT-6.1 Sol", MAIN[2]),
                       ("GPT-6.1 Terra", MAIN[3])):
        root = OUT / slug
        grade = root / "grade.json"
        pause = root / "PAUSED.release-wave.json"
        rows.append({"model": name, "slug": slug,
                     "state": "graded" if grade.is_file() else "paused" if pause.is_file() else "incomplete",
                     "grade": json.loads(grade.read_text()) if grade.is_file() else None,
                     "pause": json.loads(pause.read_text()) if pause.is_file() else None})
    summary = {"at": datetime.now(timezone.utc).isoformat(),
               "direct_argon_attempt": "v2_gemini_4_argon_high: HTTP 402 before any tokens; preserved separately",
               "antigravity_argon_attempt": AGY_ARGON,
               "openrouter_argon_fallback": OR_ARGON if argon_slug == OR_ARGON else None,
               "models": rows}
    (release / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = ["# v4 October 2026 release wave", "",
             "The direct Gemini API attempt returned HTTP 402 before generating any tokens. "
             "The benchmark then tried Gemini 4 Argon High through Antigravity; OpenRouter "
             "is the fallback if that route did not produce a grade. Each attempt keeps separate evidence.", "",
             "| Model | State | v4 score | Evidence |", "|---|---|---:|---|"]
    for row in rows:
        grade = row["grade"] or {}
        score = next((grade[k] for k in ("score", "score_100", "vigilance_score")
                      if isinstance(grade.get(k), (int, float))), None)
        score_text = f"{score:.2f}" if score is not None else "—"
        evidence = f"[result](../{row['slug']}/grade.json)" if row["state"] == "graded" else \
                   f"[pause](../{row['slug']}/PAUSED.release-wave.json)" if row["state"] == "paused" else "—"
        lines.append(f"| {row['model']} | {row['state']} | {score_text} | {evidence} |")
    lines += ["", "Existing v4 comparison: [combined standings](../../docs/success_report.v4.combined.md).",
              "Raw sprint streams, candidate projects, boundary reports, and grades are retained "
              "under each model's `results-v4/` directory.", ""]
    (release / "summary.md").write_text("\n".join(lines))
    # Keep the live status and all run/grade evidence for user inspection.
    (release / "cleanup.json").write_text(json.dumps({
        "at": summary["at"], "removed": [],
        "retained": ["candidate workspaces", "sprint streams/results", "boundary reports/verdicts",
                     "grades", "direct Argon billing-failure evidence", "Antigravity Argon attempt",
                     "OpenRouter fallback evidence if used", str(STATE)],
        "reason": "No task-owned container, image, network, or verified disposable process was identified for removal; ambiguous or paused evidence remains retained."
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
