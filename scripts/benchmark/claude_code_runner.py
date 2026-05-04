"""Runner for Claude Code headless benchmark (claude -p --output-format stream-json)."""
from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmark.util import (
    count_files,
    format_duration,
    format_value,
    print_line,
    prompt_sha256,
    save_json,
    shorten_text,
    utc_now,
)


@dataclass
class ClaudeCodeStreamResult:
    stdout: str
    stderr: str
    timed_out: bool
    stalled: bool
    stall_reason: str | None
    final_result_event: dict[str, Any] | None = None
    tool_use_counts: Counter = field(default_factory=Counter)
    subagent_invocations: list[dict[str, Any]] = field(default_factory=list)
    assistant_turns: int = 0


def _kill_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        process.terminate()
    try:
        process.wait(timeout=10)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def build_command(model: str, prompt: str) -> list[str]:
    """Build the claude -p command. Prompt is passed as positional arg."""
    return [
        "claude", "-p",
        "--model", model,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
        "--verbose",
        prompt,
    ]


def write_project_agent(project_dir: Path, subagent: dict[str, Any] | None) -> None:
    """Write the subagent definition into .claude/agents/ in the project directory."""
    if not subagent:
        return
    agents_dir = project_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    agent_name = subagent["name"]
    frontmatter_lines = [
        "---",
        f"name: {agent_name}",
        f"description: {subagent['description']}",
        f"model: {subagent['model']}",
        "---",
        "",
        subagent["prompt"].strip(),
        "",
    ]
    (agents_dir / f"{agent_name}.md").write_text("\n".join(frontmatter_lines))


def _describe_event(event: dict[str, Any]) -> str | None:
    etype = event.get("type")
    if etype == "system":
        sub = event.get("subtype", "")
        if sub == "init":
            return f"session init model={event.get('model', '-')} agents={event.get('agents', [])}"
        return f"system: {sub}"
    if etype == "assistant":
        msg = event.get("message", {})
        model = msg.get("model", "-")
        content = msg.get("content", [])
        for part in content:
            ptype = part.get("type")
            if ptype == "text":
                text = part.get("text", "")
                if text.strip():
                    return f"assistant({model}): {shorten_text(text)}"
            if ptype == "tool_use":
                name = part.get("name", "?")
                input_data = part.get("input", {})
                if name == "Task":
                    sub = input_data.get("subagent_type", "?")
                    desc = input_data.get("description", "")
                    return f"delegate to {sub}: {shorten_text(desc)}"
                if name in ("Write", "Edit"):
                    path = input_data.get("file_path", "?")
                    return f"{name} {path}"
                if name == "Bash":
                    cmd = input_data.get("command", "")
                    return f"Bash: {shorten_text(cmd, 80)}"
                return f"tool_use: {name}"
        return f"assistant({model})"
    if etype == "user":
        return None  # tool results — noisy
    if etype == "result":
        reason = event.get("stop_reason", "?")
        cost = event.get("total_cost_usd", 0)
        turns = event.get("num_turns", 0)
        return f"result: {reason} turns={turns} cost=${cost:.4f}"
    return None


def stream_process(
    process: subprocess.Popen[str],
    stdout_path: Path,
    stderr_path: Path,
    project_dir: Path,
    model_slug: str,
    timeout_seconds: int,
    no_progress_timeout_seconds: int,
) -> ClaudeCodeStreamResult:
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    last_heartbeat = 0.0
    heartbeat_interval = 10.0
    started = time.monotonic()
    last_activity = started
    last_activity_detail = "process started"
    last_file_count = count_files(project_dir)
    consecutive_error_events = 0
    error_loop_threshold = 5
    final_result_event: dict[str, Any] | None = None
    terminal_result_seen_at: float | None = None
    terminal_grace_seconds = 5.0
    tool_use_counts: Counter = Counter()
    subagent_invocations: list[dict[str, Any]] = []
    assistant_turns = 0
    session_id: str | None = None

    def _build(timed_out: bool, stalled: bool, stall_reason: str | None) -> ClaudeCodeStreamResult:
        return ClaudeCodeStreamResult(
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            timed_out=timed_out,
            stalled=stalled,
            stall_reason=stall_reason,
            final_result_event=final_result_event,
            tool_use_counts=tool_use_counts,
            subagent_invocations=subagent_invocations,
            assistant_turns=assistant_turns,
        )

    with stdout_path.open("w") as stdout_file, stderr_path.open("w") as stderr_file:
        while True:
            now = time.monotonic()
            elapsed = now - started

            if elapsed >= timeout_seconds:
                _kill_group(process)
                return _build(True, False, None)

            streams = [s for s in (process.stdout, process.stderr) if s is not None]
            ready, _, _ = select.select(streams, [], [], 1.0) if streams else ([], [], [])

            for stream in ready:
                chunk = stream.readline()
                if chunk == "":
                    continue
                if stream is process.stdout:
                    stdout_chunks.append(chunk)
                    stdout_file.write(chunk)
                    stdout_file.flush()
                    stripped = chunk.strip()
                    if not stripped:
                        continue
                    try:
                        event = json.loads(stripped)
                    except json.JSONDecodeError:
                        last_activity = now
                        continue

                    etype = event.get("type")
                    if etype == "system" and event.get("subtype") == "init":
                        session_id = event.get("session_id")

                    if etype == "assistant":
                        assistant_turns += 1
                        msg = event.get("message", {})
                        model = msg.get("model", "?")
                        for part in msg.get("content", []):
                            if part.get("type") != "tool_use":
                                continue
                            tool_name = part.get("name", "?")
                            tool_use_counts[tool_name] += 1
                            if tool_name == "Task":
                                tinput = part.get("input", {})
                                subagent_invocations.append({
                                    "parent_model": model,
                                    "subagent_type": tinput.get("subagent_type"),
                                    "description": tinput.get("description", "")[:300],
                                })

                    if etype == "result":
                        final_result_event = event
                        terminal_result_seen_at = now

                    description = _describe_event(event)
                    if description:
                        last_activity_detail = description
                        print_line(f"[{model_slug}] {description}")

                    is_error = (etype == "result" and event.get("is_error")) or (etype == "system" and event.get("subtype") == "error")
                    if is_error:
                        consecutive_error_events += 1
                        if consecutive_error_events >= error_loop_threshold:
                            _kill_group(process)
                            return _build(False, True, f"{consecutive_error_events} consecutive errors")
                    else:
                        consecutive_error_events = 0
                        last_activity = now
                else:
                    stderr_chunks.append(chunk)
                    stderr_file.write(chunk)
                    stderr_file.flush()
                    last_activity = now
                    stripped = chunk.strip()
                    if stripped:
                        last_activity_detail = f"stderr: {shorten_text(stripped)}"
                        print_line(f"[{model_slug}] {last_activity_detail}")

            # Graceful exit once the result event has been observed
            if terminal_result_seen_at is not None and (now - terminal_result_seen_at) >= terminal_grace_seconds:
                if process.poll() is None:
                    _kill_group(process)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
                print_line(f"[{model_slug}] terminal result observed; finalizing after {terminal_grace_seconds:.0f}s grace")
                return _build(False, False, None)

            if now - last_heartbeat >= heartbeat_interval:
                file_count = count_files(project_dir)
                if file_count != last_file_count:
                    last_file_count = file_count
                    last_activity = now
                    last_activity_detail = f"project file count changed to {file_count}"
                print_line(
                    f"[{model_slug}] heartbeat elapsed={format_duration(elapsed)} files={file_count} "
                    f"turns={assistant_turns} delegations={len(subagent_invocations)} session={session_id or '-'} "
                    f"{last_activity_detail}"
                )
                last_heartbeat = now

            idle = now - last_activity
            if idle >= no_progress_timeout_seconds:
                _kill_group(process)
                return _build(False, True, f"no progress for {format_duration(idle)}; last: {last_activity_detail}")

            if process.poll() is not None and not ready:
                return _build(False, False, None)


def run_variant(
    *,
    variant: dict[str, Any],
    prompt: str,
    results_dir: Path,
    timeout_seconds: int = 5400,
    no_progress_timeout_seconds: int = 360,
    force: bool = False,
) -> dict[str, Any]:
    """Run a single benchmark variant (opus_alone / opus_sonnet / opus_haiku)."""
    slug = variant["slug"]
    result_dir = results_dir / slug
    project_dir = result_dir / "project"
    prompt_path = result_dir / "prompt.txt"
    stdout_path = result_dir / "stream.ndjson"
    stderr_path = result_dir / "stderr.log"
    result_path = result_dir / "result.json"

    result_dir.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=True, exist_ok=True)

    if not force and result_path.exists():
        try:
            cached = json.loads(result_path.read_text())
            if cached.get("status") in ("completed", "completed_with_errors", "failed", "timeout"):
                print_line(f"[{slug}] cached result status={cached['status']}; skipping (use --force to rerun)")
                return cached
        except (json.JSONDecodeError, OSError):
            pass

    # Write project-local agent definition (for delegation variants)
    write_project_agent(project_dir, variant.get("subagent"))

    prompt_path.write_text(prompt)
    started_at = utc_now()
    command = build_command(variant["main_model"], prompt)
    wall_start = time.monotonic()

    print_line("")
    print_line(f"Starting {slug} -> {variant['main_model']} (subagent={variant.get('subagent', {}).get('name') if variant.get('subagent') else 'none'})")
    print_line(f"[{slug}] results_dir={result_dir}")
    print_line(f"[{slug}] timeout={timeout_seconds}s no_progress_timeout={no_progress_timeout_seconds}s")

    # Isolate HOME so ~/.claude/agents/ resolves to the result dir (not the user's
    # real home). This prevents user-level agents from leaking into the benchmark
    # run and contaminating variants (e.g. a user's sonnet-coder.md showing up in
    # a supposedly "opus alone" run). The result_dir stands in as an ephemeral
    # HOME — it has no .claude/agents/ of its own, so only project-local
    # .claude/agents/ inside project_dir are loaded by Claude Code.
    # Auth still works because ANTHROPIC_API_KEY is inherited from the env.
    isolated_env = os.environ.copy()
    isolated_env["HOME"] = str(result_dir.resolve())
    print_line(f"[{slug}] HOME isolated to {result_dir} (prevents user-level agent leakage)")

    # Optional per-variant env overrides — used by deepclaude-style variants that swap
    # ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN + ANTHROPIC_DEFAULT_*_MODEL to point
    # Claude Code's tool loop at a different (Anthropic-compatible) backend like
    # DeepSeek V4 Pro via OpenRouter. Values may reference $ENVVAR for indirection
    # (e.g. "$OPENROUTER_API_KEY") which gets resolved against the parent env at run
    # time so secrets aren't committed to config files. UNSET= prefix removes the
    # variable from the subprocess env (used to drop ANTHROPIC_API_KEY when swapping).
    overrides = variant.get("env_overrides") or {}
    if overrides:
        applied = []
        for raw_key, raw_val in overrides.items():
            if raw_key.startswith("UNSET:"):
                target = raw_key.split(":", 1)[1]
                isolated_env.pop(target, None)
                applied.append(f"unset {target}")
                continue
            val = str(raw_val)
            if val.startswith("$"):
                # Indirect lookup so we don't commit secrets to JSON
                resolved = os.environ.get(val[1:], "")
                if not resolved:
                    print_line(f"[{slug}] WARNING: env override {raw_key} references {val} but it is empty in parent env")
                isolated_env[raw_key] = resolved
                applied.append(f"{raw_key}=<{val}>")
            else:
                isolated_env[raw_key] = val
                applied.append(f"{raw_key}={val}")
        print_line(f"[{slug}] env_overrides applied: {', '.join(applied)}")

    process = subprocess.Popen(
        command,
        cwd=project_dir.resolve(),
        env=isolated_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        bufsize=1,
    )

    result = stream_process(
        process=process,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        project_dir=project_dir,
        model_slug=slug,
        timeout_seconds=timeout_seconds,
        no_progress_timeout_seconds=no_progress_timeout_seconds,
    )
    wall_end = time.monotonic()
    elapsed = round(wall_end - wall_start, 2)

    # Extract the critical pricing data from the final result event
    final = result.final_result_event or {}
    total_cost_usd = final.get("total_cost_usd")
    usage = final.get("usage", {})
    model_usage = final.get("modelUsage", {})
    stop_reason = final.get("stop_reason")
    num_turns = final.get("num_turns", result.assistant_turns)

    if result.timed_out:
        status = "timeout"
    elif result.stalled:
        status = "failed"
    elif final.get("is_error"):
        status = "failed"
    elif stop_reason in ("end_turn", "stop_sequence", None) and final:
        status = "completed"
    else:
        status = "completed_with_errors"

    file_count = count_files(project_dir)

    # Aggregate subagent token usage per model
    subagent_counts_by_type: dict[str, int] = defaultdict(int)
    for inv in result.subagent_invocations:
        subagent_counts_by_type[inv.get("subagent_type") or "unknown"] += 1

    payload = {
        "slug": slug,
        "label": variant.get("label"),
        "main_model": variant["main_model"],
        "subagent": variant.get("subagent"),
        "status": status,
        "started_at": started_at,
        "ended_at": utc_now(),
        "elapsed_seconds": elapsed,
        "timed_out": result.timed_out,
        "stalled": result.stalled,
        "stall_reason": result.stall_reason,
        "timeout_seconds": timeout_seconds,
        "no_progress_timeout_seconds": no_progress_timeout_seconds,
        "exit_code": process.returncode,
        "file_count": file_count,
        "num_turns": num_turns,
        "assistant_turns": result.assistant_turns,
        "stop_reason": stop_reason,
        "total_cost_usd": total_cost_usd,
        "usage_total": usage,
        "model_usage": model_usage,
        "tool_use_counts": dict(result.tool_use_counts),
        "subagent_invocations": result.subagent_invocations,
        "subagent_invocation_counts": dict(subagent_counts_by_type),
        "prompt_sha256": prompt_sha256(prompt),
        "command": command[:-1] + ["<prompt>"],  # don't dump the full prompt into result.json
        "paths": {
            "project_dir": str(project_dir),
            "prompt": str(prompt_path),
            "stream_ndjson": str(stdout_path),
            "stderr_log": str(stderr_path),
        },
    }
    save_json(result_path, payload)

    print_line("")
    print_line(
        f"Finished {slug} status={status} elapsed={elapsed:.2f}s files={file_count} "
        f"turns={num_turns} delegations={len(result.subagent_invocations)} "
        f"cost=${format_value(total_cost_usd)}"
    )
    if model_usage:
        print_line(f"[{slug}] model_usage:")
        for model, u in model_usage.items():
            cost = u.get("costUSD", 0)
            in_tok = u.get("inputTokens", 0)
            out_tok = u.get("outputTokens", 0)
            cache_read = u.get("cacheReadInputTokens", 0)
            print_line(
                f"  {model}: in={in_tok} out={out_tok} cache_read={cache_read} cost=${cost:.4f}"
            )

    return payload
