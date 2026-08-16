#!/usr/bin/env python3
"""Benchmark v2 orchestrator: 3-phase runs (build / validate / self-review)
through each model's native harness (claude | codex | kimi), subscriptions first.

Phases are session-independent by design: each phase is a fresh CLI invocation
in the same workspace, continuing via the filesystem. This levels the field
across harnesses and mirrors real-world "new session picks up the repo" usage.

First-class metrics per phase: elapsed seconds, token usage, cost.
- claude: total_cost_usd + modelUsage from the final result event (native USD)
- codex:  token_count events -> tokens x rates_per_m from config (UPPER BOUND:
          codex events expose no cached-input split, so cached tokens are
          charged at the full input rate; correct with blended methodology in analysis)
- kimi:   session export wire.jsonl step.end sums x rates_per_m (API-equivalent)
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from shlex import quote as shlex_quote
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from benchmark.runner import (  # noqa: E402
    OPENCODE_YOLO_PERMISSION,
    build_codex_command,
    extract_codex_metrics,
    extract_kimi_metrics,
    extract_metrics as extract_opencode_metrics,
    collect_kimi_session_tokens,
    parse_event_stream,
)
from benchmark.util import save_json, utc_now  # noqa: E402

PHASE_TIMEOUT = 5400
KIMI_TERMINAL_GRACE = 8


def count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file())


def build_claude_command(model: str, prompt: str) -> list[str]:
    return [
        "claude", "-p",
        "--model", model,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
        "--verbose",
        prompt,
    ]


def build_kimi_v2_command(model_id: str, prompt: str) -> list[str]:
    args = ["kimi", "-p", prompt, "--output-format", "stream-json", "-m", model_id]
    return ["bash", "-lc", " ".join(shlex_quote(a) for a in args)]


def build_grok_command(model_id: str, prompt: str) -> list[str]:
    # Official xAI grok CLI (@xai-official/grok, mise/npm) — headless single-turn
    # via -p, streaming-json NDJSON on stdout. The terminal `end` event carries
    # native usage + total_cost_usd (the earlier grok-cli-hurry-mode fork had no
    # metrics and needed a Live Search patch — the official CLI needs neither).
    # --always-approve = YOLO tool exec; --disable-web-search for parity with the
    # opencode runs (isolate the model's own API knowledge, matching the prior
    # grok CLI runs whose forked Live Search was non-functional); --max-turns 400.
    args = ["grok", "-m", model_id, "-p", prompt,
            "--max-turns", "400", "--always-approve", "--disable-web-search",
            "--output-format", "streaming-json"]
    return ["bash", "-lc", " ".join(shlex_quote(a) for a in args)]


def build_agy_command(model_id: str, prompt: str, project_dir: Path) -> list[str]:
    # Antigravity CLI — headless via --print. agy defaults file operations to its
    # own scratch workspace, so the workspace must be added via --add-dir AND the
    # prompt gets a workspace preamble (run_phase does that for harness == "agy").
    return [
        "agy", "--print", prompt, "--model", model_id,
        "--dangerously-skip-permissions",
        "--add-dir", str(project_dir.resolve()),
        "--print-timeout", "100m",
    ]


def run_phase(model: dict[str, Any], phase_name: str, prompt: str,
              project_dir: Path, out_dir: Path) -> dict[str, Any]:
    harness = model["harness"]
    stdout_path = out_dir / f"{phase_name}.ndjson"
    stderr_path = out_dir / f"{phase_name}.stderr.log"
    (out_dir / f"{phase_name}.prompt.txt").write_text(prompt)

    env = os.environ.copy()
    # Backfill env vars from the user's secrets file without overriding anything
    # already set — headless sessions don't source zsh config, and provider
    # templates like {env:SAKANA_AI_TOKEN} silently hang opencode when empty.
    secrets_file = Path.home() / ".config" / "zsh" / "secrets"
    if secrets_file.exists():
        for line in secrets_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                name, _, value = line[len("export "):].partition("=")
                name = name.strip()
                if name and name not in env:
                    env[name] = value.strip().strip('"').strip("'")
    stdin_data: str | None = None

    if harness == "claude":
        command = build_claude_command(model["model_id"], prompt)
        # Isolate HOME so user-level ~/.claude/agents don't leak into the run —
        # but copy the SUBSCRIPTION credentials in, and strip ANTHROPIC_API_KEY
        # so the CLI can never silently fall back to API billing. (Learned the
        # expensive way: without this, every run bills the API account.)
        env["HOME"] = str(out_dir.resolve())
        import shutil
        real_creds = Path.home() / ".claude" / ".credentials.json"
        iso_claude = out_dir / ".claude"
        iso_claude.mkdir(parents=True, exist_ok=True)
        if real_creds.exists():
            shutil.copy2(real_creds, iso_claude / ".credentials.json")
        env.pop("ANTHROPIC_API_KEY", None)
    elif harness == "codex":
        command = build_codex_command(
            model["model_id"], project_dir,
            reasoning_effort=model.get("codex_reasoning_effort"),
        )
        stdin_data = prompt
    elif harness == "kimi":
        command = build_kimi_v2_command(model["model_id"], prompt)
    elif harness == "grok":
        command = build_grok_command(model["model_id"], prompt)
    elif harness == "agy":
        preamble = (f"Your workspace directory is {project_dir.resolve()}. Do ALL work inside it; "
                    f"create and edit every file under that absolute path, never in any other scratch area.\n\n")
        command = build_agy_command(model["model_id"], preamble + prompt, project_dir)
    elif harness == "opencode":
        # v2 phases are session-independent: fresh `opencode run` per phase
        # in the same workspace, model selected via -m each time.
        command = [
            "opencode", "run", "--agent", "build", "--format", "json",
            "--dir", str(project_dir.resolve()),
            "-m", model["model_id"],
            prompt,
        ]
        opencode_config = REPO_ROOT / "config" / "opencode.benchmark.json"
        if opencode_config.exists():
            env["OPENCODE_CONFIG"] = str(opencode_config.resolve())
        env["OPENCODE_PERMISSION"] = json.dumps(OPENCODE_YOLO_PERMISSION, separators=(",", ":"))
        # Full config isolation: plugins (oh-my-opencode-slim) load from
        # $XDG_CONFIG_HOME/opencode regardless of OPENCODE_CONFIG, replacing the
        # built-in agents with an "orchestrator" whose delegation machinery
        # (fixer/librarian lanes, deepwork) derailed delegation-prone models.
        # Redirecting XDG_CONFIG_HOME restores vanilla opencode: the built-in
        # "build" agent resolves and no user plugin shapes the run. Auth is
        # unaffected (auth.json lives under XDG_DATA_HOME).
        xdg_iso = REPO_ROOT / "config" / "opencode.xdg-isolated"
        (xdg_iso / "opencode").mkdir(parents=True, exist_ok=True)
        env["XDG_CONFIG_HOME"] = str(xdg_iso.resolve())
    else:
        raise ValueError(f"unknown harness {harness}")

    started_at = utc_now()
    wall_start = time.monotonic()
    process = subprocess.Popen(
        command, cwd=project_dir.resolve(), env=env, text=True,
        stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True, bufsize=1,
    )
    if stdin_data is not None and process.stdin:
        try:
            process.stdin.write(stdin_data)
            process.stdin.close()
        except BrokenPipeError:
            pass

    stdout_lines: list[str] = []
    terminal_seen: float | None = None
    timed_out = False
    import selectors
    sel = selectors.DefaultSelector()
    if process.stdout:
        sel.register(process.stdout, selectors.EVENT_READ)
    stderr_chunks: list[str] = []

    with open(stdout_path, "w") as out_f:
        while True:
            now = time.monotonic()
            if now - wall_start > PHASE_TIMEOUT:
                timed_out = True
                os.killpg(process.pid, signal.SIGTERM)
                break
            if terminal_seen is not None and now - terminal_seen > KIMI_TERMINAL_GRACE:
                os.killpg(process.pid, signal.SIGTERM)  # kimi lingers after final event
                break
            if process.poll() is not None:
                for line in process.stdout or []:
                    out_f.write(line)
                    stdout_lines.append(line)
                break
            events = sel.select(timeout=1.0)
            for key, _ in events:
                stream = cast(Any, key.fileobj)
                line = stream.readline()
                if not line:
                    continue
                out_f.write(line)
                out_f.flush()
                stdout_lines.append(line)
                if '"session.resume_hint"' in line:
                    terminal_seen = time.monotonic()

    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
    if process.stderr:
        stderr_chunks.append(process.stderr.read() or "")
    stderr_path.write_text("".join(stderr_chunks))

    elapsed = round(time.monotonic() - wall_start, 2)
    stdout_text = "".join(stdout_lines)
    events = parse_event_stream(stdout_text)

    tokens: dict[str, Any] = {}
    cost_usd: float | None = None
    session_id: str | None = None
    rates = model.get("rates_per_m") or {}

    if harness == "claude":
        for ev in events:
            if ev.get("type") == "result":
                cost_usd = ev.get("total_cost_usd")
                usage = ev.get("usage") or {}
                tokens = {
                    "input": usage.get("input_tokens", 0),
                    "output": usage.get("output_tokens", 0),
                    "cache": {"read": usage.get("cache_read_input_tokens", 0),
                              "write": usage.get("cache_creation_input_tokens", 0)},
                }
                tokens["total"] = sum([tokens["input"], tokens["output"],
                                       tokens["cache"]["read"], tokens["cache"]["write"]])
                session_id = ev.get("session_id")
    elif harness == "codex":
        metrics = extract_codex_metrics(events)
        tokens = metrics.get("tokens") or {}
    elif harness == "kimi":
        metrics = extract_kimi_metrics(events)
        session_id = metrics.get("session_id")
        tokens = collect_kimi_session_tokens(session_id, model["slug"]) or {}
    elif harness == "opencode":
        metrics = extract_opencode_metrics(events)
        tokens = metrics.get("tokens") or {}
        session_id = metrics.get("session_id")
        cost_usd = round(metrics["cost"], 4) if metrics.get("cost") else None

    if cost_usd is None and tokens and rates:
        cost_usd = round(
            (tokens.get("input", 0) or 0) / 1e6 * rates.get("input", 0)
            + ((tokens.get("output", 0) or 0) + (tokens.get("reasoning", 0) or 0)) / 1e6 * rates.get("output", 0)
            + ((tokens.get("cache") or {}).get("read", 0) or 0) / 1e6 * rates.get("cache_read", 0)
            + ((tokens.get("cache") or {}).get("write", 0) or 0) / 1e6 * rates.get("cache_write", 0),
            4,
        )

    payload = {
        "phase": phase_name,
        "harness": harness,
        "command_kind": command[0] if command[0] != "bash" else "bash -lc",
        "started_at": started_at,
        "ended_at": utc_now(),
        "elapsed_seconds": elapsed,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "tokens": tokens,
        "cost_usd": cost_usd,
        "session_id": session_id,
        "file_count_after": count_files(project_dir),
    }
    save_json(out_dir / f"{phase_name}.result.json", payload)
    print(f"[{model['slug']}/{phase_name}] done elapsed={elapsed}s exit={process.returncode} "
          f"tokens={tokens.get('total', '-')} cost=${cost_usd if cost_usd is not None else '-'}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark v2 (3-phase, native harnesses)")
    parser.add_argument("--model", required=True, help="v2 slug from config/models_v2.json")
    parser.add_argument("--config", default=str(REPO_ROOT / "config" / "models_v2.json"))
    parser.add_argument("--results-dir", default=str(REPO_ROOT / "results-v2"))
    parser.add_argument("--phases", default="1,2,3", help="comma list, e.g. 1,2,3 or 2,3 to resume")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text())
    model = next((m for m in config["models"] if m["slug"] == args.model), None)
    if model is None:
        sys.exit(f"unknown v2 slug: {args.model}")
    if model.get("blocked"):
        sys.exit(f"model blocked: {model['blocked']}")

    out_dir = Path(args.results_dir) / model["slug"]
    project_dir = out_dir / "project"
    project_dir.mkdir(parents=True, exist_ok=True)

    prompts = {name: (REPO_ROOT / rel).read_text()
               for name, rel in config["prompts"].items()}

    phases_to_run = [f"phase{n.strip()}" for n in args.phases.split(",")]
    results = []
    for phase_name in phases_to_run:
        results.append(run_phase(model, phase_name, prompts[phase_name], project_dir, out_dir))
        if results[-1]["timed_out"]:
            print(f"[{model['slug']}] {phase_name} timed out; stopping")
            break

    total = {
        "slug": model["slug"],
        "label": model["label"],
        "harness": model["harness"],
        "billing": model.get("billing"),
        "phases": results,
        "elapsed_seconds_total": round(sum(r["elapsed_seconds"] for r in results), 2),
        "cost_usd_total": round(sum(r["cost_usd"] or 0 for r in results), 4),
        "tokens_total": sum((r["tokens"] or {}).get("total", 0) or 0 for r in results),
        "self_review_present": (project_dir / "SELF_REVIEW.md").exists(),
        "ended_at": utc_now(),
    }
    save_json(out_dir / "result.json", total)
    print(f"[{model['slug']}] ALL DONE elapsed={total['elapsed_seconds_total']}s "
          f"tokens={total['tokens_total']} cost=${total['cost_usd_total']} "
          f"self_review={'yes' if total['self_review_present'] else 'MISSING'}")


if __name__ == "__main__":
    main()
