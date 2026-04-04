"""Process management and benchmark execution."""
from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
                            if not is_error_event:
                                description = describe_event(event)
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
    command = build_opencode_command(bench.runner, model["id"], prompt, continue_session_id=continue_session_id)
    wall_start = time.monotonic()
    process_env = os.environ.copy()
    if bench.opencode_config_path is not None:
        process_env["OPENCODE_CONFIG"] = str(bench.opencode_config_path)
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


def _ensure_local_model_ready(
    model: dict[str, Any],
    bench: BenchmarkConfig,
) -> tuple[bool, str]:
    """Run preflight for a local model using the configured backend."""
    if bench.backend is None:
        print_line(f"[{model['slug']}] preflight skipped: no local backend configured")
        return True, "preflight skipped: no local backend configured"

    target_model = resolve_ollama_model_name(model["id"], bench.opencode_config_path)
    context_limit = resolve_ollama_context_limit(model["id"], bench.opencode_config_path)

    if not target_model:
        # For llama-swap, the model name in the config IS the name to request.
        # Fall back to the model slug or the raw ID suffix.
        target_model = model.get("llama_swap_model") or model["id"].split("/", 1)[-1]

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

    started_at = utc_now()
    print_line("")
    print_line(f"[{index}/{total}] starting {model['slug']} -> {model['id']}")
    print_line(f"[{model['slug']}] results_dir={result_dir}")
    print_line(f"[{model['slug']}] timeout={bench.timeout_seconds}s")
    if bench.opencode_config_path is not None:
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

    phase1 = run_opencode_phase(
        bench=bench,
        model=model,
        model_slug=model["slug"],
        prompt=bench.prompt,
        started_at=started_at,
        project_dir=project_dir,
        prompt_path=prompt_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        result_path=phase1_result_path,
        continue_session_id=None,
        phase_name="phase1",
    )

    phases = [phase1]
    final_phase = phase1

    if (
        bench.followup_prompt
        and model_enables_followup(model)
        and not phase1.get("timed_out")
        and not phase1.get("stalled")
    ):
        continued_session_id = phase1.get("opencode_session_id")
        print_line(f"[{model['slug']}] primary phase complete; continuing with follow-up prompt")
        phase2 = run_opencode_phase(
            bench=bench,
            model=model,
            model_slug=model["slug"],
            prompt=build_followup_prompt(bench.followup_prompt, continued_session_id),
            started_at=utc_now(),
            project_dir=project_dir,
            prompt_path=followup_prompt_path,
            stdout_path=followup_stdout_path,
            stderr_path=followup_stderr_path,
            result_path=phase2_result_path,
            continue_session_id=continued_session_id,
            phase_name="phase2",
            override_min_preview_tps=None,
        )
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

    process_env = os.environ.copy()
    if bench.opencode_config_path is not None:
        process_env["OPENCODE_CONFIG"] = str(bench.opencode_config_path)
    process_env["OPENCODE_PERMISSION"] = json.dumps(OPENCODE_YOLO_PERMISSION, separators=(",", ":"))
    session_id = final_phase.get("opencode_session_id") or phase1.get("opencode_session_id")
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
    return payload
