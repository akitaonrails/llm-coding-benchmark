"""Runner for Grok CLI headless benchmark (grok --prompt-file --output-format streaming-json)."""
from __future__ import annotations

import json
import os
import select
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark.config import BenchmarkConfig, summarize_project
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
class GrokStreamResult:
    stdout: str
    stderr: str
    timed_out: bool
    stalled: bool
    stall_reason: str | None
    final_end_event: dict[str, Any] | None = None
    assistant_text: str = ""
    num_turns: int = 0


def resolve_grok_binary() -> str | None:
    return shutil.which("grok") or shutil.which("agent")


def redact_grok_command(command: list[str]) -> list[str]:
    redacted = list(command)
    for index, part in enumerate(redacted):
        if part == "--prompt-file" and index + 1 < len(redacted):
            redacted[index + 1] = "<prompt-file>"
    return redacted


def build_grok_command(
    model_id: str,
    prompt_path: Path,
    *,
    resume_session_id: str | None = None,
    max_turns: int | None = None,
) -> list[str]:
    binary = resolve_grok_binary()
    if binary is None:
        raise RuntimeError("grok CLI is not available on PATH (tried grok and agent)")

    command = [
        binary,
        "--model",
        model_id,
        "--prompt-file",
        str(prompt_path.resolve()),
        "--output-format",
        "streaming-json",
        "--always-approve",
    ]
    if max_turns is not None:
        command.extend(["--max-turns", str(max_turns)])
    if resume_session_id:
        command.extend(["--resume", resume_session_id])
    return command


def resolve_grok_no_progress_timeout_seconds(
    model: dict[str, Any],
    phase_name: str,
    default_seconds: int,
) -> int:
    """Phase 2 often runs long docker/build commands with no streaming-json output."""
    if phase_name == "phase2":
        minutes = model.get("grok_followup_no_progress_minutes")
        if isinstance(minutes, (int, float)) and minutes > 0:
            return int(minutes * 60)
    return default_seconds


def _process_group_has_children(root_pid: int) -> bool:
    """True when the grok session spawned shell/docker children still running."""
    try:
        result = subprocess.run(
            ["pgrep", "-P", str(root_pid)],
            capture_output=True,
            text=True,
            check=False,
        )
        return bool(result.stdout.strip())
    except OSError:
        return False


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


def _describe_grok_event(event: dict[str, Any]) -> str | None:
    etype = event.get("type")
    if etype == "text":
        data = event.get("data", "")
        if isinstance(data, str) and data.strip():
            return f"text: {shorten_text(data)}"
    if etype == "thought":
        data = event.get("data", "")
        if isinstance(data, str) and data.strip():
            return f"thought: {shorten_text(data)}"
    if etype == "end":
        reason = event.get("stopReason", "?")
        turns = event.get("num_turns", 0)
        cost = event.get("total_cost_usd")
        cost_str = f"${cost:.4f}" if isinstance(cost, (int, float)) else "-"
        return f"end: {reason} turns={turns} cost={cost_str}"
    if etype == "error":
        return f"error: {event.get('message', '?')}"
    if etype == "max_turns_reached":
        return "max_turns_reached"
    return None


def stream_grok_process(
    process: subprocess.Popen[str],
    stdout_path: Path,
    stderr_path: Path,
    project_dir: Path,
    model_slug: str,
    timeout_seconds: int,
    no_progress_timeout_seconds: int,
    *,
    treat_child_processes_as_progress: bool = False,
) -> GrokStreamResult:
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    assistant_chunks: list[str] = []
    last_heartbeat = 0.0
    heartbeat_interval = 10.0
    started = time.monotonic()
    last_activity = started
    last_activity_detail = "process started"
    last_file_count = count_files(project_dir)
    final_end_event: dict[str, Any] | None = None
    terminal_end_seen_at: float | None = None
    terminal_grace_seconds = 5.0
    num_turns = 0

    def _build(timed_out: bool, stalled: bool, stall_reason: str | None) -> GrokStreamResult:
        return GrokStreamResult(
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            timed_out=timed_out,
            stalled=stalled,
            stall_reason=stall_reason,
            final_end_event=final_end_event,
            assistant_text="".join(assistant_chunks),
            num_turns=num_turns,
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
                    stripped = chunk.strip()
                    if not stripped:
                        continue
                    try:
                        event = json.loads(stripped)
                    except json.JSONDecodeError:
                        stdout_chunks.append(chunk)
                        stdout_file.write(chunk)
                        stdout_file.flush()
                        last_activity = now
                        continue

                    etype = event.get("type")
                    if etype == "text":
                        data = event.get("data", "")
                        if isinstance(data, str):
                            assistant_chunks.append(data)
                    if etype == "end":
                        final_end_event = event
                        terminal_end_seen_at = now
                        if isinstance(event.get("num_turns"), int):
                            num_turns = event["num_turns"]
                    if etype == "error":
                        final_end_event = event

                    # Grok emits one JSON line per thought token; persisting those
                    # balloons logs to gigabytes on long docker-validation runs.
                    if etype != "thought":
                        stdout_chunks.append(chunk)
                        stdout_file.write(chunk)
                        stdout_file.flush()

                    description = _describe_grok_event(event)
                    if description and etype != "thought":
                        last_activity_detail = description
                        print_line(f"[{model_slug}] {description}")
                        last_activity = now
                    elif etype == "thought":
                        last_activity = now
                        last_activity_detail = "thought stream active"
                else:
                    stderr_chunks.append(chunk)
                    stderr_file.write(chunk)
                    stderr_file.flush()
                    last_activity = now
                    stripped = chunk.strip()
                    if stripped:
                        last_activity_detail = f"stderr: {shorten_text(stripped)}"
                        print_line(f"[{model_slug}] {last_activity_detail}")

            if terminal_end_seen_at is not None and (now - terminal_end_seen_at) >= terminal_grace_seconds:
                if process.poll() is None:
                    _kill_group(process)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
                print_line(
                    f"[{model_slug}] terminal end event observed; finalizing after {terminal_grace_seconds:.0f}s grace"
                )
                return _build(False, False, None)

            if now - last_heartbeat >= heartbeat_interval:
                file_count = count_files(project_dir)
                if file_count != last_file_count:
                    last_file_count = file_count
                    last_activity = now
                    last_activity_detail = f"project file count changed to {file_count}"
                elif (
                    treat_child_processes_as_progress
                    and process.poll() is None
                    and _process_group_has_children(process.pid)
                ):
                    last_activity = now
                    last_activity_detail = "subprocess activity detected (docker/build/shell)"
                print_line(
                    f"[{model_slug}] heartbeat elapsed={format_duration(elapsed)} files={file_count} "
                    f"turns={num_turns} {last_activity_detail}"
                )
                last_heartbeat = now

            idle = now - last_activity
            if idle >= no_progress_timeout_seconds:
                _kill_group(process)
                return _build(False, True, f"no progress for {format_duration(idle)}; last: {last_activity_detail}")

            if process.poll() is not None and not ready:
                return _build(False, False, None)


def extract_grok_metrics(end_event: dict[str, Any] | None) -> dict[str, Any]:
    if not end_event:
        return {
            "session_id": None,
            "finish_reason": None,
            "tokens": {},
            "total_cost_usd": None,
            "num_turns": None,
            "model_usage": {},
        }

    usage = end_event.get("usage") or {}
    input_tokens = usage.get("input_tokens") or 0
    output_tokens = usage.get("output_tokens") or 0
    cache_read = usage.get("cache_read_input_tokens") or 0
    total_tokens = usage.get("total_tokens")
    if total_tokens is None:
        total_tokens = input_tokens + cache_read + output_tokens

    return {
        "session_id": end_event.get("sessionId"),
        "finish_reason": end_event.get("stopReason"),
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "cache_read": cache_read,
            "total": total_tokens,
        },
        "total_cost_usd": end_event.get("total_cost_usd"),
        "num_turns": end_event.get("num_turns"),
        "model_usage": end_event.get("modelUsage") or {},
    }


def run_grok_phase(
    *,
    bench: BenchmarkConfig,
    model: dict[str, Any],
    model_slug: str,
    prompt: str,
    started_at: str,
    project_dir: Path,
    prompt_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    result_path: Path | None,
    phase_name: str = "phase1",
    continue_session_id: str | None = None,
) -> dict[str, Any]:
    prompt_path.write_text(prompt)
    max_turns = model.get("grok_max_turns") if phase_name == "phase1" else model.get("grok_followup_max_turns")
    resume_session_id = continue_session_id
    if phase_name == "phase2" and model.get("grok_followup_resume") is False:
        resume_session_id = None
    command = build_grok_command(
        model["id"],
        prompt_path,
        resume_session_id=resume_session_id,
        max_turns=max_turns,
    )
    wall_start = time.monotonic()

    no_progress_timeout_seconds = resolve_grok_no_progress_timeout_seconds(
        model,
        phase_name,
        bench.no_progress_timeout_seconds,
    )

    process = subprocess.Popen(
        command,
        cwd=project_dir.resolve(),
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        bufsize=1,
    )

    result = stream_grok_process(
        process=process,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        project_dir=project_dir,
        model_slug=f"{model_slug}/{phase_name}",
        timeout_seconds=bench.timeout_seconds,
        no_progress_timeout_seconds=no_progress_timeout_seconds,
        treat_child_processes_as_progress=phase_name == "phase2",
    )

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _kill_group(process)
        process.wait(timeout=5)

    wall_end = time.monotonic()
    metrics = extract_grok_metrics(result.final_end_event)
    project_summary = summarize_project(project_dir)
    elapsed_seconds = round(wall_end - wall_start, 2)
    total_tokens = metrics["tokens"].get("total")
    finish_reason = metrics["finish_reason"]
    terminal_completed = finish_reason in ("EndTurn", "end_turn", "stop", "stop_sequence", None)

    if result.timed_out:
        status = "timeout"
    elif result.stalled:
        status = "failed"
    elif result.final_end_event and result.final_end_event.get("type") == "error":
        status = "failed"
    elif terminal_completed and project_summary["works_as_intended"] == "yes":
        status = "completed"
    elif terminal_completed:
        status = "completed_with_errors"
    elif process.returncode == 0 and project_summary["works_as_intended"] == "yes":
        status = "completed"
    elif process.returncode == 0:
        status = "completed_with_errors"
    else:
        status = "failed"

    payload = {
        "phase": phase_name,
        "assistant_output_excerpt": result.assistant_text[:4000],
        "command": redact_grok_command(command),
        "continued_from_session": continue_session_id,
        "elapsed_seconds": elapsed_seconds,
        "ended_at": utc_now(),
        "exit_code": process.returncode,
        "finish_reason": finish_reason,
        "model": model,
        "opencode_session_id": metrics["session_id"],
        "grok_session_id": metrics["session_id"],
        "paths": {
            "opencode_config": None,
            "project_dir": str(project_dir),
            "prompt": str(prompt_path),
            "stderr": str(stderr_path),
            "stdout": str(stdout_path),
        },
        "project_summary": project_summary,
        "prompt_sha256": prompt_sha256(prompt),
        "started_at": started_at,
        "status": status,
        "stderr_excerpt": result.stderr[:4000],
        "stalled": result.stalled,
        "stall_reason": result.stall_reason,
        "timed_out": result.timed_out,
        "timeout_seconds": bench.timeout_seconds,
        "no_progress_timeout_seconds": no_progress_timeout_seconds,
        "tokens": metrics["tokens"],
        "total_cost_usd": metrics["total_cost_usd"],
        "model_usage": metrics["model_usage"],
        "num_turns": metrics["num_turns"] or result.num_turns,
        "runner_type": "grok",
        "tokens_per_second": round(total_tokens / elapsed_seconds, 2) if total_tokens and elapsed_seconds else None,
        "output_tokens_per_second": (
            round(metrics["tokens"].get("output", 0) / elapsed_seconds, 2)
            if metrics["tokens"].get("output") and elapsed_seconds
            else None
        ),
    }
    if result_path is not None:
        save_json(result_path, payload)
    return payload