"""Process management and benchmark execution."""
from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import time
from shlex import quote as shlex_quote
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from benchmark.backends import LocalModelBackend
from benchmark.config import (
    OPENCODE_YOLO_PERMISSION,
    BenchmarkConfig,
    existing_terminal_result,
    mark_model_skip_by_default,
    model_enables_followup,
    resolve_ollama_context_limit,
    resolve_ollama_model_name,
    summarize_project,
)
from benchmark.loop_detector import ToolCallLoopDetector
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
class StreamResult:
    """Output from a streamed opencode process."""

    stdout: str
    stderr: str
    timed_out: bool
    stalled: bool
    stall_reason: str | None
    latest_preview_output_tps: float | None
    preview_average_output_tps: float | None


def kill_process_group(process: subprocess.Popen[str]) -> None:
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
    except PermissionError:
        process.kill()


def build_opencode_command(
    runner: dict[str, Any],
    model_id: str,
    prompt: str,
    continue_session_id: str | None = None,
) -> list[str]:
    command = [runner["command"], *runner["args"]]
    if continue_session_id:
        command.extend(["--session", continue_session_id])
    else:
        command.extend(["-m", model_id])
    command.append(prompt)
    return command


def build_codex_command(
    model_id: str,
    project_dir: Path,
    reasoning_effort: str | None = None,
) -> list[str]:
    """Build a codex exec command for a fully autonomous benchmark run."""
    # Build codex exec arguments. The codex binary may be a shell wrapper
    # (e.g., `exec npx --yes @openai/codex "$@"`) so we launch through bash
    # to ensure the full shell environment (mise, node) is available.
    codex_args = [
        "codex", "exec",
        "--json",
        "--ephemeral",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "-s", "danger-full-access",
        "-C", str(project_dir.resolve()),
        "-m", model_id,
    ]
    if reasoning_effort:
        codex_args.extend(["-c", f"model_reasoning_effort={reasoning_effort}"])
    codex_args.append("-")  # read prompt from stdin
    # Wrap in bash -lc to get login shell environment (mise, PATH, etc.)
    cmd = ["bash", "-lc", " ".join(shlex_quote(a) for a in codex_args)]
    return cmd


def export_opencode_session(
    session_id: str,
    export_path: Path,
    process_env: dict[str, str],
    model_slug: str,
) -> Path | None:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    error_path = export_path.with_suffix(".stderr.log")
    completed = subprocess.run(
        ["opencode", "export", session_id],
        capture_output=True,
        text=True,
        env=process_env,
        check=False,
    )
    if completed.returncode == 0:
        export_path.write_text(completed.stdout)
        if completed.stderr:
            error_path.write_text(completed.stderr)
        return export_path
    error_path.write_text(completed.stderr or completed.stdout or "opencode export failed")
    print_line(f"[{model_slug}] opencode export failed for session {session_id}")
    return None


def build_followup_prompt(prompt: str, continue_session_id: str | None) -> str:
    if continue_session_id:
        return prompt
    fallback = (
        "\n\nIf this is running in a fresh session rather than a continued one, first inspect the existing project "
        "in the current working directory, understand the current implementation state, and then perform the same "
        "runtime validation work before making any additional fixes."
    )
    return prompt + fallback


def parse_event_stream(raw: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def extract_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    finish = next((event for event in reversed(events) if event.get("type") == "step_finish"), {})
    tokens = finish.get("part", {}).get("tokens", {}) if finish else {}
    text_parts = []
    for event in events:
        if event.get("type") != "text":
            continue
        text = event.get("part", {}).get("text")
        if isinstance(text, str):
            text_parts.append(text)
    return {
        "session_id": next((event.get("sessionID") for event in events if event.get("sessionID")), None),
        "finish_reason": finish.get("part", {}).get("reason"),
        "tokens": tokens,
        "assistant_output": "\n".join(text_parts).strip(),
    }


def extract_codex_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract session/token metrics from Codex CLI JSONL events."""
    thread_id = None
    total_input = 0
    total_output = 0
    text_parts: list[str] = []
    last_turn_failed = False

    for event in events:
        etype = event.get("type")
        if etype == "thread.started":
            thread_id = event.get("thread_id")
        elif etype == "turn.completed":
            usage = event.get("usage", {})
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
            last_turn_failed = False
        elif etype == "turn.failed":
            last_turn_failed = True
        elif etype == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                text = item.get("text", "")
                if isinstance(text, str) and text:
                    text_parts.append(text)

    total_tokens = total_input + total_output
    return {
        "session_id": thread_id,
        "finish_reason": "stop" if not last_turn_failed else "error",
        "tokens": {
            "input": total_input,
            "output": total_output,
            "total": total_tokens,
        },
        "assistant_output": "\n".join(text_parts).strip(),
    }


def describe_event(event: dict[str, Any]) -> str | None:
    event_type = event.get("type")
    part = event.get("part", {})
    if event_type == "step_start":
        return "assistant started"
    if event_type == "step_finish":
        reason = part.get("reason", "unknown")
        tokens = part.get("tokens", {}).get("total")
        if tokens is None:
            return f"assistant finished ({reason})"
        return f"assistant finished ({reason}, total_tokens={tokens})"
    if event_type == "text":
        text = part.get("text", "")
        if isinstance(text, str) and text:
            return f"assistant text: {shorten_text(text)}"
        return "assistant text"
    if part.get("type"):
        return f"event: {part['type']}"
    if event_type:
        return f"event: {event_type}"
    return None


def describe_codex_event(event: dict[str, Any]) -> str | None:
    """Human-readable description of a Codex JSONL event for heartbeat logs."""
    etype = event.get("type")
    if etype == "thread.started":
        return f"codex thread started: {event.get('thread_id', '-')}"
    if etype == "turn.started":
        return "codex turn started"
    if etype == "turn.completed":
        usage = event.get("usage", {})
        out = usage.get("output_tokens", 0)
        return f"codex turn completed (output_tokens={out})"
    if etype == "turn.failed":
        msg = event.get("error", {}).get("message", "unknown")
        return f"codex turn failed: {shorten_text(str(msg))}"
    if etype == "error":
        return f"codex error: {shorten_text(event.get('message', 'unknown'))}"
    if etype == "item.started":
        item = event.get("item", {})
        return f"codex item started: {item.get('type', 'unknown')}"
    if etype == "item.completed":
        item = event.get("item", {})
        itype = item.get("type", "unknown")
        if itype == "agent_message":
            text = item.get("text", "")
            return f"codex message: {shorten_text(text)}"
        if itype == "command_execution":
            cmd = item.get("command", "")
            return f"codex command: {shorten_text(cmd)}"
        if itype == "file_change":
            return "codex file_change"
        return f"codex item completed: {itype}"
    return None


def stream_process_output(
    *,
    process: subprocess.Popen[str],
    stdout_path: Path,
    stderr_path: Path,
    project_dir: Path,
    model_slug: str,
    backend: LocalModelBackend | None,
    timeout_seconds: int,
    no_progress_timeout_seconds: int,
    min_preview_output_tps: float | None,
    min_preview_samples: int,
    event_describer: Callable[[dict[str, Any]], str | None] | None = None,
) -> StreamResult:
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    stdout_buffer = ""
    stderr_buffer = ""
    last_event_message: str | None = None
    session_id: str | None = None
    last_heartbeat = 0.0
    heartbeat_interval = 10.0
    started = time.monotonic()
    last_activity = started
    last_activity_detail = "process started"
    last_file_count = count_files(project_dir)
    current_step_started_at: int | None = None
    latest_preview_output_tps: float | None = None
    preview_average_output_tps: float | None = None
    preview_output_tps_samples: list[float] = []
    preview_gate_decided = False
    terminal_stop_seen_at: float | None = None
    terminal_stop_grace_seconds = 5.0
    consecutive_error_events = 0
    error_loop_threshold = 5
    tool_call_loop_detector = ToolCallLoopDetector(threshold=5)

    def _make_result(timed_out: bool, stalled: bool, stall_reason: str | None) -> StreamResult:
        return StreamResult(
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            timed_out=timed_out,
            stalled=stalled,
            stall_reason=stall_reason,
            latest_preview_output_tps=latest_preview_output_tps,
            preview_average_output_tps=preview_average_output_tps,
        )

    with stdout_path.open("w") as stdout_file, stderr_path.open("w") as stderr_file:
        while True:
            now = time.monotonic()
            elapsed = now - started

            if elapsed >= timeout_seconds:
                kill_process_group(process)
                if stdout_buffer:
                    stdout_chunks.append(stdout_buffer)
                    stdout_file.write(stdout_buffer)
                if stderr_buffer:
                    stderr_chunks.append(stderr_buffer)
                    stderr_file.write(stderr_buffer)
                return _make_result(True, False, None)

            ready_streams: list[Any] = []
            streams = [s for s in (process.stdout, process.stderr) if s is not None]
            if streams:
                ready_streams, _, _ = select.select(streams, [], [], 1.0)

            for stream in ready_streams:
                chunk = stream.readline()
                if chunk == "":
                    continue
                if stream is process.stdout:
                    stdout_chunks.append(chunk)
                    stdout_file.write(chunk)
                    stdout_file.flush()
                    stripped = chunk.strip()
                    if stripped:
                        try:
                            event = json.loads(stripped)
                        except json.JSONDecodeError:
                            last_activity = now
                            consecutive_error_events = 0
                            last_event_message = f"stdout: {shorten_text(stripped)}"
                            last_activity_detail = last_event_message
                        else:
                            is_error_event = (
                                event.get("part", {}).get("type") == "error"
                                or event.get("type") == "error"
                                or event.get("type") == "turn.failed"
                            )
                            if is_error_event:
                                consecutive_error_events += 1
                                error_detail = (
                                    event.get("part", {}).get("error")
                                    or event.get("part", {}).get("message")
                                    or event.get("error")
                                    or "unknown"
                                )
                                if isinstance(error_detail, dict):
                                    error_detail = error_detail.get("message", str(error_detail))
                                description = f"error: {shorten_text(str(error_detail))}"
                                last_event_message = description
                                last_activity_detail = description
                                if consecutive_error_events <= 2:
                                    print_line(f"[{model_slug}] {description}")
                                elif consecutive_error_events == error_loop_threshold:
                                    print_line(
                                        f"[{model_slug}] {consecutive_error_events} consecutive error events, suppressing further output"
                                    )
                                if consecutive_error_events >= error_loop_threshold:
                                    kill_process_group(process)
                                    stall_reason = (
                                        f"error loop: {consecutive_error_events} consecutive error events; "
                                        f"last error: {shorten_text(str(error_detail), 200)}"
                                    )
                                    print_line(f"[{model_slug}] {stall_reason}")
                                    return _make_result(False, True, stall_reason)
                                # Don't refresh last_activity for error events —
                                # let the no-progress timeout catch lingering errors
                                # that stay below the loop threshold.
                            else:
                                last_activity = now
                                consecutive_error_events = 0

                            session_id = session_id or event.get("sessionID")
                            if event.get("type") == "step_start":
                                terminal_stop_seen_at = None
                                timestamp = event.get("timestamp")
                                if isinstance(timestamp, int):
                                    current_step_started_at = timestamp
                            elif event.get("type") == "step_finish":
                                reason = event.get("part", {}).get("reason")
                                if reason == "stop":
                                    terminal_stop_seen_at = now
                                timestamp = event.get("timestamp")
                                output_tokens = event.get("part", {}).get("tokens", {}).get("output")
                                if (
                                    current_step_started_at is not None
                                    and isinstance(timestamp, int)
                                    and isinstance(output_tokens, int)
                                    and timestamp > current_step_started_at
                                ):
                                    duration_seconds = (timestamp - current_step_started_at) / 1000
                                    latest_preview_output_tps = round(output_tokens / duration_seconds, 2)
                                    preview_output_tps_samples.append(latest_preview_output_tps)
                                    print_line(f"[{model_slug}] preview output_tps={latest_preview_output_tps:.2f}")
                                    if not preview_gate_decided and len(preview_output_tps_samples) >= min_preview_samples:
                                        preview_gate_decided = True
                                        preview_average_output_tps = round(
                                            sum(preview_output_tps_samples[:min_preview_samples]) / min_preview_samples,
                                            2,
                                        )
                                        print_line(
                                            f"[{model_slug}] preview average output_tps="
                                            f"{preview_average_output_tps:.2f} over first {min_preview_samples} steps"
                                        )
                                        if (
                                            min_preview_output_tps is not None
                                            and preview_average_output_tps < min_preview_output_tps
                                        ):
                                            kill_process_group(process)
                                            slow_reason = (
                                                f"preview average output_tps {preview_average_output_tps:.2f} "
                                                f"over first {min_preview_samples} steps "
                                                f"below threshold {min_preview_output_tps:.2f}"
                                            )
                                            print_line(f"[{model_slug}] {slow_reason}")
                                            return _make_result(False, True, slow_reason)

                            # Codex: turn.completed is the terminal stop equivalent
                            if event.get("type") == "turn.completed":
                                terminal_stop_seen_at = now

                            # Tool-call loop detection (Gemini CLI style)
                            if event.get("type") == "tool_use":
                                part = event.get("part", {})
                                tool_name = part.get("tool", "")
                                tool_input = part.get("state", {}).get("input", {})
                                if tool_name and tool_call_loop_detector.record(tool_name, tool_input):
                                    kill_process_group(process)
                                    stall_reason = tool_call_loop_detector.loop_description(tool_name)
                                    print_line(f"[{model_slug}] {stall_reason}")
                                    return _make_result(False, True, stall_reason)

                            # Codex: command_execution loop detection
                            if event.get("type") == "item.completed":
                                item = event.get("item", {})
                                if item.get("type") == "command_execution":
                                    cmd = item.get("command", "")
                                    if cmd and tool_call_loop_detector.record("command_execution", {"command": cmd}):
                                        kill_process_group(process)
                                        stall_reason = tool_call_loop_detector.loop_description("command_execution")
                                        print_line(f"[{model_slug}] {stall_reason}")
                                        return _make_result(False, True, stall_reason)

                            if not is_error_event:
                                _describer = event_describer or describe_event
                                description = _describer(event)
                                if description:
                                    last_event_message = description
                                    last_activity_detail = description
                                    print_line(f"[{model_slug}] {description}")
                else:
                    stderr_chunks.append(chunk)
                    stderr_file.write(chunk)
                    stderr_file.flush()
                    last_activity = now
                    stripped = chunk.strip()
                    if stripped:
                        last_event_message = f"stderr: {shorten_text(stripped)}"
                        last_activity_detail = last_event_message
                        print_line(f"[{model_slug}] {last_event_message}")

            if terminal_stop_seen_at is not None and now - terminal_stop_seen_at >= terminal_stop_grace_seconds:
                if process.poll() is None:
                    kill_process_group(process)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
                print_line(
                    f"[{model_slug}] terminal stop observed; finalizing after {terminal_stop_grace_seconds:.0f}s grace period"
                )
                return _make_result(False, False, None)

            if now - last_heartbeat >= heartbeat_interval:
                file_count = count_files(project_dir)
                if file_count != last_file_count:
                    last_file_count = file_count
                    last_activity = now
                    last_activity_detail = f"project file count changed to {file_count}"
                session_hint = session_id if session_id else "-"
                detail = last_event_message if last_event_message else "waiting for output"
                remote_state = backend.fetch_status_string() if backend else None
                remote_suffix = f" {remote_state}" if remote_state else ""
                print_line(
                    f"[{model_slug}] heartbeat elapsed={format_duration(elapsed)} files={file_count} session={session_hint}{remote_suffix} {detail}"
                )
                last_heartbeat = now

            idle_seconds = now - last_activity
            if idle_seconds >= no_progress_timeout_seconds:
                kill_process_group(process)
                stall_reason = (
                    f"no progress for {format_duration(idle_seconds)}; last activity: {last_activity_detail}"
                )
                print_line(f"[{model_slug}] {stall_reason}")
                return _make_result(False, True, stall_reason)

            if process.poll() is not None and not ready_streams:
                if stdout_buffer:
                    stdout_chunks.append(stdout_buffer)
                    stdout_file.write(stdout_buffer)
                if stderr_buffer:
                    stderr_chunks.append(stderr_buffer)
                    stderr_file.write(stderr_buffer)
                return _make_result(False, False, None)


def _verify_opencode_config(
    config_path: Path | None,
    model: dict[str, Any],
    model_slug: str,
    project_dir: Path,
) -> None:
    """Verify the opencode config resolves correctly from the project cwd.

    Guards against the relative-path bug where OPENCODE_CONFIG pointed at a
    path that didn't exist from the opencode cwd, causing silent fallback to
    the home config (wrong port / wrong model ID).
    """
    if config_path is None:
        return
    resolved = config_path.resolve()
    if not resolved.exists():
        raise RuntimeError(
            f"[{model_slug}] OPENCODE_CONFIG does not exist: {resolved} "
            f"(from project_dir={project_dir})"
        )

    if model.get("provider") != "ollama":
        return

    try:
        config = json.loads(resolved.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print_line(f"[{model_slug}] WARNING: could not parse {resolved}: {exc}")
        return

    base_url = (
        config.get("provider", {})
        .get("ollama", {})
        .get("options", {})
        .get("baseURL", "")
    )

    # Check that the model entry exists in the config
    model_key = model["id"]
    if model_key.startswith("ollama/"):
        model_key = model_key[len("ollama/"):]
    models_map = config.get("provider", {}).get("ollama", {}).get("models", {})
    entry = models_map.get(model_key)
    if not entry:
        print_line(
            f"[{model_slug}] WARNING: model key '{model_key}' not found in "
            f"opencode config {resolved} — opencode may fall back to the home config"
        )

    # If using llama-swap, verify baseURL points to the llama-swap port
    llama_swap_model = model.get("llama_swap_model")
    if llama_swap_model and entry:
        config_model_id = entry.get("id", "")
        if config_model_id != llama_swap_model:
            print_line(
                f"[{model_slug}] WARNING: config model id '{config_model_id}' "
                f"doesn't match llama_swap_model '{llama_swap_model}'"
            )

    print_line(f"[{model_slug}] opencode config verified: {resolved} baseURL={base_url}")


def run_opencode_phase(
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
    continue_session_id: str | None = None,
    phase_name: str = "phase1",
    override_min_preview_tps: float | None = ...,  # sentinel
) -> dict[str, Any]:
    prompt_path.write_text(prompt)
    _verify_opencode_config(bench.opencode_config_path, model, model_slug, project_dir)
    command = build_opencode_command(bench.runner, model["id"], prompt, continue_session_id=continue_session_id)
    wall_start = time.monotonic()
    process_env = os.environ.copy()
    if bench.opencode_config_path is not None:
        process_env["OPENCODE_CONFIG"] = str(bench.opencode_config_path.resolve())
    process_env["OPENCODE_PERMISSION"] = json.dumps(OPENCODE_YOLO_PERMISSION, separators=(",", ":"))
    process = subprocess.Popen(
        command,
        cwd=project_dir,
        env=process_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        bufsize=1,
    )

    effective_min_tps = bench.min_preview_output_tps if override_min_preview_tps is ... else override_min_preview_tps

    result = stream_process_output(
        process=process,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        project_dir=project_dir,
        model_slug=f"{model_slug}/{phase_name}",
        backend=bench.backend,
        timeout_seconds=bench.timeout_seconds,
        no_progress_timeout_seconds=bench.no_progress_timeout_seconds,
        min_preview_output_tps=effective_min_tps,
        min_preview_samples=bench.min_preview_samples,
    )

    wall_end = time.monotonic()
    events = parse_event_stream(result.stdout)
    metrics = extract_metrics(events)
    project_summary = summarize_project(project_dir)
    elapsed_seconds = round(wall_end - wall_start, 2)
    total_tokens = metrics["tokens"].get("total")
    terminal_stop_completed = metrics["finish_reason"] == "stop"

    if result.timed_out:
        status = "timeout"
    elif result.stalled:
        status = "failed"
    elif terminal_stop_completed and project_summary["works_as_intended"] == "yes":
        status = "completed"
    elif terminal_stop_completed:
        status = "completed_with_errors"
    elif process.returncode == 0 and project_summary["works_as_intended"] == "yes":
        status = "completed"
    elif process.returncode == 0:
        status = "completed_with_errors"
    else:
        status = "failed"

    payload = {
        "phase": phase_name,
        "assistant_output_excerpt": metrics["assistant_output"][:4000],
        "command": command,
        "continued_from_session": continue_session_id,
        "elapsed_seconds": elapsed_seconds,
        "ended_at": utc_now(),
        "exit_code": process.returncode,
        "finish_reason": metrics["finish_reason"],
        "model": model,
        "opencode_session_id": metrics["session_id"],
        "paths": {
            "opencode_config": str(bench.opencode_config_path) if bench.opencode_config_path is not None else None,
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
        "no_progress_timeout_seconds": bench.no_progress_timeout_seconds,
        "tokens": metrics["tokens"],
        "preview_output_tokens_per_second": result.latest_preview_output_tps,
        "preview_output_tokens_per_second_average": result.preview_average_output_tps,
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


def run_codex_phase(
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
    override_min_preview_tps: float | None = ...,  # sentinel
) -> dict[str, Any]:
    """Run a single benchmark phase using the Codex CLI."""
    prompt_path.write_text(prompt)
    command = build_codex_command(model["id"], project_dir, reasoning_effort=model.get("codex_reasoning_effort"))
    wall_start = time.monotonic()

    process_env = os.environ.copy()
    # Codex uses OPENAI_API_KEY directly — no opencode config needed.

    process = subprocess.Popen(
        command,
        cwd=project_dir.resolve(),
        env=process_env,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        bufsize=1,
    )
    # Write prompt to stdin then close it so codex reads it via '-'
    if process.stdin:
        try:
            process.stdin.write(prompt)
            process.stdin.close()
        except BrokenPipeError:
            pass

    effective_min_tps = bench.min_preview_output_tps if override_min_preview_tps is ... else override_min_preview_tps

    result = stream_process_output(
        process=process,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        project_dir=project_dir,
        model_slug=f"{model_slug}/{phase_name}",
        backend=None,  # Codex models are cloud-only
        timeout_seconds=bench.timeout_seconds,
        no_progress_timeout_seconds=bench.no_progress_timeout_seconds,
        min_preview_output_tps=effective_min_tps,
        min_preview_samples=bench.min_preview_samples,
        event_describer=describe_codex_event,
    )

    wall_end = time.monotonic()
    events = parse_event_stream(result.stdout)
    metrics = extract_codex_metrics(events)
    project_summary = summarize_project(project_dir)
    elapsed_seconds = round(wall_end - wall_start, 2)
    total_tokens = metrics["tokens"].get("total")
    terminal_stop_completed = metrics["finish_reason"] == "stop"

    if result.timed_out:
        status = "timeout"
    elif result.stalled:
        status = "failed"
    elif terminal_stop_completed and project_summary["works_as_intended"] == "yes":
        status = "completed"
    elif terminal_stop_completed:
        status = "completed_with_errors"
    elif process.returncode == 0 and project_summary["works_as_intended"] == "yes":
        status = "completed"
    elif process.returncode == 0:
        status = "completed_with_errors"
    else:
        status = "failed"

    payload = {
        "phase": phase_name,
        "assistant_output_excerpt": metrics["assistant_output"][:4000],
        "command": command,
        "continued_from_session": None,
        "elapsed_seconds": elapsed_seconds,
        "ended_at": utc_now(),
        "exit_code": process.returncode,
        "finish_reason": metrics["finish_reason"],
        "model": model,
        "opencode_session_id": metrics["session_id"],
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
        "no_progress_timeout_seconds": bench.no_progress_timeout_seconds,
        "tokens": metrics["tokens"],
        "preview_output_tokens_per_second": result.latest_preview_output_tps,
        "preview_output_tokens_per_second_average": result.preview_average_output_tps,
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


def _kill_stale_opencode_processes() -> None:
    """Kill stale opencode run processes that may hold the SQLite DB lock.

    When a benchmark run times out, the opencode child processes can survive
    and keep a write lock on ~/.local/share/opencode/opencode.db, causing all
    new opencode instances to hang silently with zero output.

    opencode launches as npm→node→.opencode, so we need multiple patterns
    to catch all layers of the process tree.
    """
    patterns = [
        "opencode.*run.*--agent",
        "opencode.*run.*--format",
        r"opencode-ai/bin/\.opencode",
    ]
    our_pid = os.getpid()
    our_ppid = os.getppid()
    stale: list[int] = []

    for pattern in patterns:
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True, text=True, check=False,
            )
            pids = [int(p) for p in result.stdout.strip().split() if p.strip()]
            stale.extend(p for p in pids if p not in (our_pid, our_ppid) and p not in stale)
        except (OSError, ValueError):
            continue

    if not stale:
        return

    print_line(f"Killing {len(stale)} stale opencode process(es): {stale}")
    for pid in stale:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(2)
    for pid in stale:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    time.sleep(1)


def _get_ollama_for_eviction() -> Any | None:
    """Get an OllamaBackend pointed at the home config URL, for eviction only."""
    from benchmark.backends import OllamaBackend
    from benchmark.config import load_opencode_ollama_api_base

    ollama_base = load_opencode_ollama_api_base()
    if ollama_base:
        return OllamaBackend(ollama_base)
    return None


def _evict_competing_backend(bench: BenchmarkConfig, model_slug: str) -> None:
    """Unload models from the other backend to free GPU memory.

    Ollama and llama-swap share the same GPU, so before using one backend
    we must ensure the other has released VRAM. Without this the server
    OOMs and hangs.
    """
    from benchmark.backends import LlamaSwapBackend, OllamaBackend

    if bench.backend is None:
        return

    if isinstance(bench.backend, LlamaSwapBackend):
        ollama = _get_ollama_for_eviction()
        if ollama:
            active = ollama.list_active()
            if active:
                print_line(f"[{model_slug}] evicting Ollama models to free GPU: {', '.join(active)}")
                ollama.unload_all()
                # Verify eviction succeeded
                still_active = ollama.list_active()
                if still_active:
                    print_line(f"[{model_slug}] WARNING: Ollama still has models loaded after eviction: {', '.join(still_active)}")
    elif isinstance(bench.backend, OllamaBackend):
        # llama-swap auto-evicts on TTL but we can't force it.
        # Best-effort: load a tiny model to trigger swap, then unload it.
        pass


def _ensure_local_model_ready(
    model: dict[str, Any],
    bench: BenchmarkConfig,
) -> tuple[bool, str]:
    """Run preflight for a local model using the configured backend."""
    from benchmark.backends import LlamaSwapBackend

    if bench.backend is None:
        print_line(f"[{model['slug']}] preflight skipped: no local backend configured")
        return True, "preflight skipped: no local backend configured"

    # Free GPU from the competing backend before loading
    _evict_competing_backend(bench, model["slug"])

    if isinstance(bench.backend, LlamaSwapBackend):
        # llama-swap uses its own model names (e.g. "qwen3:32b"), not Ollama IDs.
        # Context is configured server-side, so context_limit is irrelevant.
        target_model = model.get("llama_swap_model")
        if not target_model:
            print_line(f"[{model['slug']}] preflight skipped: no llama_swap_model configured")
            return False, "no llama_swap_model configured for this model"
        return bench.backend.ensure_model_ready(target_model, model["slug"], context_limit=None)

    # Ollama path: resolve model name and context from opencode config
    target_model = resolve_ollama_model_name(model["id"], bench.opencode_config_path)
    context_limit = resolve_ollama_context_limit(model["id"], bench.opencode_config_path)
    if not target_model:
        target_model = model.get("ollama_model_name") or model["id"].split("/", 1)[-1]

    return bench.backend.ensure_model_ready(target_model, model["slug"], context_limit)


def run_model(model: dict[str, Any], bench: BenchmarkConfig, index: int, total: int) -> dict[str, Any]:
    result_dir = bench.results_dir / model["slug"]
    project_dir = result_dir / "project"
    prompt_path = result_dir / "prompt.txt"
    stdout_path = result_dir / "opencode-output.ndjson"
    stderr_path = result_dir / "opencode-stderr.log"
    phase1_result_path = result_dir / "phase1-result.json"
    followup_prompt_path = result_dir / "followup-prompt.txt"
    followup_stdout_path = result_dir / "followup-opencode-output.ndjson"
    followup_stderr_path = result_dir / "followup-opencode-stderr.log"
    phase2_result_path = result_dir / "phase2-result.json"
    session_export_path = result_dir / "session-export.json"
    result_path = result_dir / "result.json"
    result_dir.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=True, exist_ok=True)

    if not bench.force:
        cached = existing_terminal_result(result_path)
        if cached:
            print_line(
                f"[{index}/{total}] {model['slug']} skipping cached result "
                f"status={cached['status']} elapsed={format_value(cached.get('elapsed_seconds'))}s"
            )
            return cached

    runner_type = model.get("runner_type", "opencode")

    if runner_type != "codex":
        _kill_stale_opencode_processes()

    started_at = utc_now()
    print_line("")
    print_line(f"[{index}/{total}] starting {model['slug']} -> {model['id']} (runner={runner_type})")
    print_line(f"[{model['slug']}] results_dir={result_dir}")
    print_line(f"[{model['slug']}] timeout={bench.timeout_seconds}s")
    if runner_type != "codex" and bench.opencode_config_path is not None:
        print_line(f"[{model['slug']}] opencode_config={bench.opencode_config_path}")
    print_line(f"[{model['slug']}] no_progress_timeout={bench.no_progress_timeout_seconds}s")

    # Preflight for local models
    is_local = model["provider"] == "ollama"
    if is_local:
        preflight_ok, preflight_message = _ensure_local_model_ready(model, bench)
        if not preflight_ok:
            payload = {
                "assistant_output_excerpt": "",
                "command": [],
                "elapsed_seconds": 0.0,
                "ended_at": utc_now(),
                "exit_code": None,
                "finish_reason": None,
                "model": model,
                "opencode_session_id": None,
                "paths": {
                    "opencode_config": str(bench.opencode_config_path) if bench.opencode_config_path is not None else None,
                    "project_dir": str(project_dir),
                    "prompt": str(prompt_path),
                    "stderr": str(stderr_path),
                    "stdout": str(stdout_path),
                },
                "project_summary": summarize_project(project_dir),
                "prompt_sha256": prompt_sha256(bench.prompt),
                "started_at": started_at,
                "status": "failed",
                "stderr_excerpt": "",
                "timed_out": False,
                "timeout_seconds": bench.timeout_seconds,
                "no_progress_timeout_seconds": bench.no_progress_timeout_seconds,
                "tokens": {},
                "tokens_per_second": None,
                "output_tokens_per_second": None,
                "preview_output_tokens_per_second": None,
                "preview_output_tokens_per_second_average": None,
                "preflight_error": preflight_message,
                "phases": [],
            }
            save_json(result_path, payload)
            print_line(f"[{index}/{total}] finished {model['slug']} status=failed preflight_error={preflight_message}")
            return payload

    _run_phase = run_codex_phase if runner_type == "codex" else run_opencode_phase
    phase1_kwargs: dict[str, Any] = {
        "bench": bench,
        "model": model,
        "model_slug": model["slug"],
        "prompt": bench.prompt,
        "started_at": started_at,
        "project_dir": project_dir,
        "prompt_path": prompt_path,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "result_path": phase1_result_path,
        "phase_name": "phase1",
    }
    if runner_type != "codex":
        phase1_kwargs["continue_session_id"] = None
    phase1 = _run_phase(**phase1_kwargs)

    phases = [phase1]
    final_phase = phase1

    if (
        bench.followup_prompt
        and model_enables_followup(model)
        and not phase1.get("timed_out")
        and not phase1.get("stalled")
    ):
        continued_session_id = phase1.get("opencode_session_id") if runner_type != "codex" else None
        print_line(f"[{model['slug']}] primary phase complete; continuing with follow-up prompt")
        phase2_kwargs: dict[str, Any] = {
            "bench": bench,
            "model": model,
            "model_slug": model["slug"],
            "prompt": build_followup_prompt(bench.followup_prompt, continued_session_id),
            "started_at": utc_now(),
            "project_dir": project_dir,
            "prompt_path": followup_prompt_path,
            "stdout_path": followup_stdout_path,
            "stderr_path": followup_stderr_path,
            "result_path": phase2_result_path,
            "phase_name": "phase2",
            "override_min_preview_tps": None,
        }
        if runner_type != "codex":
            phase2_kwargs["continue_session_id"] = continued_session_id
        phase2 = _run_phase(**phase2_kwargs)
        phases.append(phase2)
        final_phase = phase2

    if (
        bench.auto_skip_slow_preview
        and isinstance(bench.min_preview_output_tps, float)
        and isinstance(final_phase.get("preview_output_tokens_per_second_average"), float)
        and float(final_phase["preview_output_tokens_per_second_average"]) < bench.min_preview_output_tps
    ):
        note = (
            f" Skipped by default after benchmark preview averaged "
            f"{float(final_phase['preview_output_tokens_per_second_average']):.2f} output tok/s over the first "
            f"{bench.min_preview_samples} steps (< {bench.min_preview_output_tps:.2f})."
        )
        if mark_model_skip_by_default(bench.config_path, model["slug"], note):
            print_line(f"[{model['slug']}] marked skip_by_default in {bench.config_path}")

    session_id = final_phase.get("opencode_session_id") or phase1.get("opencode_session_id")
    exported_session = None
    if runner_type != "codex":
        process_env = os.environ.copy()
        if bench.opencode_config_path is not None:
            process_env["OPENCODE_CONFIG"] = str(bench.opencode_config_path.resolve())
        process_env["OPENCODE_PERMISSION"] = json.dumps(OPENCODE_YOLO_PERMISSION, separators=(",", ":"))
        exported_session = (
            export_opencode_session(session_id, session_export_path, process_env, model["slug"])
            if isinstance(session_id, str) and session_id
            else None
        )

    total_elapsed = round(sum(float(phase.get("elapsed_seconds") or 0.0) for phase in phases), 2)
    payload = {
        **final_phase,
        "elapsed_seconds": total_elapsed,
        "ended_at": utc_now(),
        "model": model,
        "opencode_session_id": session_id,
        "paths": {
            "opencode_config": str(bench.opencode_config_path) if bench.opencode_config_path is not None else None,
            "project_dir": str(project_dir),
            "prompt": str(prompt_path),
            "stderr": str(stderr_path),
            "stdout": str(stdout_path),
            "followup_prompt": str(followup_prompt_path) if followup_prompt_path.exists() else None,
            "followup_stderr": str(followup_stderr_path) if followup_stderr_path.exists() else None,
            "followup_stdout": str(followup_stdout_path) if followup_stdout_path.exists() else None,
            "session_export": str(exported_session) if exported_session is not None else None,
        },
        "primary_prompt_sha256": prompt_sha256(bench.prompt),
        "followup_prompt_sha256": prompt_sha256(bench.followup_prompt) if bench.followup_prompt else None,
        "session_exported": exported_session is not None,
        "phases": phases,
    }
    save_json(result_path, payload)
    print_line(
        f"[{index}/{total}] finished {model['slug']} status={payload['status']} "
        f"elapsed={total_elapsed:.2f}s files={payload['project_summary']['file_count']} "
        f"total_tokens={format_value(payload['tokens'].get('total'))}"
    )

    # Unload the model after the run to free GPU for the next model.
    # This prevents OOM when the next model's preflight tries to evict
    # the competing backend while this model is still resident.
    if is_local and bench.backend is not None:
        active = bench.backend.list_active()
        if active:
            print_line(f"[{model['slug']}] post-run cleanup: unloading {', '.join(active)}")
            bench.backend.unload_all()

    return payload
