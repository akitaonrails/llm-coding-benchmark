#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL_STATUSES = {"completed", "completed_with_errors", "failed", "timeout"}
OPENCODE_CONFIG_PATH = Path.home() / ".config" / "opencode" / "opencode.json"
OLLAMA_PREFLIGHT_TIMEOUT_SECONDS = 45.0
OLLAMA_PREFLIGHT_FALLBACK_CONTEXTS = [131072, 98304, 65536, 32768]
DEFAULT_NO_PROGRESS_MINUTES = 6
OPENCODE_YOLO_PERMISSION = {
    "bash": {"*": "allow"},
    "codesearch": {"*": "allow"},
    "doom_loop": {"*": "allow"},
    "edit": {"*": "allow"},
    "external_directory": {"*": "allow"},
    "glob": {"*": "allow"},
    "grep": {"*": "allow"},
    "list": {"*": "allow"},
    "lsp": {"*": "allow"},
    "read": {"*": "allow"},
    "skill": {"*": "allow"},
    "task": {"*": "allow"},
    "todowrite": {"*": "allow"},
    "webfetch": {"*": "allow"},
    "websearch": {"*": "allow"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return load_json(path)
    except (OSError, json.JSONDecodeError):
        return None


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def save_json_preserve_order(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def prompt_sha256(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def load_ollama_warmup_payload(path: Path) -> dict[str, Any] | None:
    payload = load_optional_json(path)
    if not payload:
        return None
    results = payload.get("results")
    if not isinstance(results, list):
        return None
    results_by_slug: dict[str, dict[str, Any]] = {}
    for entry in results:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("slug")
        if isinstance(slug, str) and slug:
            results_by_slug[slug] = entry
    payload["results_by_slug"] = results_by_slug
    return payload


def print_line(message: str) -> None:
    print(message, flush=True)


def format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def count_files(path: Path) -> int:
    return sum(1 for item in path.rglob("*") if item.is_file())


def shorten_text(text: str, limit: int = 100) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def load_opencode_config() -> dict[str, Any] | None:
    if not OPENCODE_CONFIG_PATH.exists():
        return None
    try:
        return json.loads(OPENCODE_CONFIG_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def load_opencode_config_from_path(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return load_opencode_config()
    return load_optional_json(path)


def load_opencode_ollama_api_base() -> str | None:
    payload = load_opencode_config()
    if not payload:
        return None
    base_url = (
        payload.get("provider", {})
        .get("ollama", {})
        .get("options", {})
        .get("baseURL")
    )
    if not isinstance(base_url, str) or not base_url:
        return None
    return base_url[:-3] if base_url.endswith("/v1") else base_url


def ollama_api_url(api_base: str | None, path: str) -> str | None:
    if not api_base:
        return None
    return urllib.parse.urljoin(api_base.rstrip("/") + "/", path.lstrip("/"))


def ollama_api_request(
    api_base: str | None,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 3.0,
) -> dict[str, Any] | None:
    url = ollama_api_url(api_base, path)
    if not url:
        return None
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            return json.loads(error.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"error": f"http_error:{error.code}"}
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return None


def resolve_ollama_model_name(opencode_model_id: str, config_path: Path | None = None) -> str | None:
    payload = load_opencode_config_from_path(config_path)
    if not payload:
        return None
    normalized = opencode_model_id.split("/", 1)[1] if opencode_model_id.startswith("ollama/") else opencode_model_id
    model_entry = (
        payload.get("provider", {})
        .get("ollama", {})
        .get("models", {})
        .get(normalized, {})
    )
    model_name = model_entry.get("id")
    if isinstance(model_name, str) and model_name:
        return model_name
    return None


def resolve_ollama_context_limit(opencode_model_id: str, config_path: Path | None = None) -> int | None:
    payload = load_opencode_config_from_path(config_path)
    if not payload:
        return None
    normalized = opencode_model_id.split("/", 1)[1] if opencode_model_id.startswith("ollama/") else opencode_model_id
    model_entry = (
        payload.get("provider", {})
        .get("ollama", {})
        .get("models", {})
        .get(normalized, {})
    )
    context_limit = model_entry.get("limit", {}).get("context")
    if isinstance(context_limit, int) and context_limit > 0:
        return context_limit
    return None


def ollama_preflight_context_candidates(context_limit: int | None) -> list[int | None]:
    if context_limit is None:
        return [None]
    ordered: list[int | None] = [context_limit]
    for candidate in OLLAMA_PREFLIGHT_FALLBACK_CONTEXTS:
        if candidate >= context_limit:
            continue
        if candidate not in ordered:
            ordered.append(candidate)
    return ordered


def active_ollama_models(api_base: str | None) -> list[str] | None:
    payload = ollama_api_request(api_base, "/api/ps", timeout=1.5)
    if not payload:
        return None
    models = payload.get("models")
    if not isinstance(models, list):
        return None
    names: list[str] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("model")
        if isinstance(name, str) and name:
            names.append(name)
    return names


def fetch_ollama_active_models(api_url: str | None) -> str | None:
    models = active_ollama_models(api_url)
    if models is None:
        return None
    if not models:
        return "remote_ollama=idle"
    return f"remote_ollama={','.join(models)}"


def unload_ollama_model(api_base: str | None, model_name: str) -> bool:
    response = ollama_api_request(
        api_base,
        "/api/generate",
        payload={"model": model_name, "prompt": "", "keep_alive": 0, "stream": False},
        timeout=30.0,
    )
    return bool(response and response.get("done_reason") == "unload")


def preload_ollama_model(api_base: str | None, model_name: str, context_limit: int | None = None) -> tuple[bool, str]:
    # Use a tiny real generation request instead of an empty prompt preload.
    # This matches the warmup path more closely and avoids models that sit loaded
    # but never answer the empty-prompt keep_alive request.
    payload: dict[str, Any] = {
        "model": model_name,
        "prompt": "ping",
        "keep_alive": "2h",
        "stream": False,
        "options": {
            "num_predict": 8,
        },
    }
    if context_limit:
        payload["options"]["num_ctx"] = context_limit
    response = ollama_api_request(
        api_base,
        "/api/generate",
        payload=payload,
        timeout=OLLAMA_PREFLIGHT_TIMEOUT_SECONDS,
    )
    if not response:
        return False, "no response from remote ollama"
    if response.get("error"):
        return False, str(response["error"])
    if response.get("done") is True:
        return True, "preload ok"
    return False, "unexpected preload response"


def ensure_ollama_target_model(
    opencode_model_id: str,
    model_slug: str,
    config_path: Path | None = None,
) -> tuple[bool, str]:
    api_base = load_opencode_ollama_api_base()
    target_model = resolve_ollama_model_name(opencode_model_id, config_path)
    context_limit = resolve_ollama_context_limit(opencode_model_id, config_path)
    if not api_base or not target_model:
        print_line(f"[{model_slug}] ollama preflight skipped: missing config mapping")
        return True, "ollama preflight skipped: missing config mapping"

    current_models = active_ollama_models(api_base)
    if current_models is None:
        print_line(f"[{model_slug}] ollama preflight skipped: unable to query remote /api/ps")
        return True, "ollama preflight skipped: unable to query remote /api/ps"

    if current_models:
        print_line(f"[{model_slug}] unloading remote models: {', '.join(current_models)}")
        for current_model in current_models:
            if unload_ollama_model(api_base, current_model):
                print_line(f"[{model_slug}] unloaded {current_model}")
            else:
                print_line(f"[{model_slug}] unload request may have failed for {current_model}")

    last_message = "unknown preflight failure"
    for candidate_context in ollama_preflight_context_candidates(context_limit):
        context_suffix = f" num_ctx={candidate_context}" if candidate_context else ""
        print_line(f"[{model_slug}] preloading remote model: {target_model}{context_suffix}")
        preload_ok, preload_message = preload_ollama_model(api_base, target_model, candidate_context)
        if preload_ok:
            print_line(f"[{model_slug}] preload ok: {target_model}{context_suffix}")
            return True, preload_message
        last_message = preload_message
        print_line(f"[{model_slug}] preload failed: {target_model}{context_suffix}: {preload_message}")

    return False, last_message


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
        part = event.get("part", {})
        text = part.get("text")
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


def summarize_project(project_dir: Path) -> dict[str, Any]:
    checks = {
        "gemfile": project_dir / "Gemfile",
        "routes": project_dir / "config" / "routes.rb",
        "app_dir": project_dir / "app",
        "views_dir": project_dir / "app" / "views",
        "javascript_dir": project_dir / "app" / "javascript",
        "tests_dir": project_dir / "test",
        "readme_md": project_dir / "README.md",
        "readme_lower": project_dir / "readme.md",
        "dockerfile": project_dir / "Dockerfile",
        "docker_compose_yml": project_dir / "docker-compose.yml",
        "docker_compose_yaml": project_dir / "docker-compose.yaml",
        "compose_yml": project_dir / "compose.yml",
        "compose_yaml": project_dir / "compose.yaml",
    }
    present = {name: path.exists() for name, path in checks.items()}
    files = sum(1 for item in project_dir.rglob("*") if item.is_file())
    readme_present = present["readme_md"] or present["readme_lower"]
    compose_present = any(
        present[name]
        for name in ("docker_compose_yml", "docker_compose_yaml", "compose_yml", "compose_yaml")
    )
    rails_present = present["gemfile"] and present["routes"] and present["app_dir"]
    tests_present = present["tests_dir"]
    docker_present = present["dockerfile"] and compose_present

    if rails_present and readme_present and tests_present and docker_present:
        intended = "yes"
        note = "Rails app, tests, README, and container files detected."
    elif files == 0:
        intended = "no"
        note = "Project directory is empty."
    elif rails_present or readme_present or docker_present or tests_present:
        intended = "partial"
        note = "Some expected benchmark artifacts exist, but the scaffold looks incomplete."
    else:
        intended = "no"
        note = "Generated files do not resemble the requested Rails project."

    return {
        "file_count": files,
        "present": present,
        "works_as_intended": intended,
        "works_note": note,
    }


def existing_terminal_result(result_path: Path) -> dict[str, Any] | None:
    if not result_path.exists():
        return None
    payload = load_json(result_path)
    if payload.get("status") in TERMINAL_STATUSES:
        return payload
    return None


def mark_model_skip_by_default(config_path: Path, model_slug: str, note: str) -> bool:
    payload = load_optional_json(config_path)
    if not payload:
        return False
    models = payload.get("models")
    if not isinstance(models, list):
        return False
    changed = False
    for model in models:
        if not isinstance(model, dict):
            continue
        if model.get("slug") != model_slug:
            continue
        if model.get("skip_by_default") is not True:
            model["skip_by_default"] = True
            changed = True
        reason = model.get("selection_reason")
        note_suffix = f" {note}"
        if isinstance(reason, str) and note_suffix not in reason:
            model["selection_reason"] = reason + note_suffix
            changed = True
        break
    if not changed:
        return False
    save_json_preserve_order(config_path, payload)
    return True


def stream_process_output(
    process: subprocess.Popen[str],
    stdout_path: Path,
    stderr_path: Path,
    project_dir: Path,
    model_slug: str,
    model_provider: str,
    timeout_seconds: int,
    no_progress_timeout_seconds: int,
    min_preview_output_tps: float | None,
    min_preview_samples: int,
) -> tuple[str, str, bool, bool, str | None, float | None, float | None]:
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
    ollama_api_url = load_opencode_ollama_api_base() if model_provider == "ollama" else None
    last_file_count = count_files(project_dir)
    current_step_started_at: int | None = None
    latest_preview_output_tps: float | None = None
    preview_average_output_tps: float | None = None
    preview_output_tps_samples: list[float] = []
    preview_gate_decided = False

    with stdout_path.open("w") as stdout_file, stderr_path.open("w") as stderr_file:
        while True:
            now = time.monotonic()
            elapsed = now - started
            if elapsed >= timeout_seconds:
                kill_process_group(process)
                if stdout_buffer:
                    stdout_chunks.append(stdout_buffer)
                    stdout_file.write(stdout_buffer)
                    stdout_buffer = ""
                if stderr_buffer:
                    stderr_chunks.append(stderr_buffer)
                    stderr_file.write(stderr_buffer)
                    stderr_buffer = ""
                return (
                    "".join(stdout_chunks),
                    "".join(stderr_chunks),
                    True,
                    False,
                    None,
                    latest_preview_output_tps,
                    preview_average_output_tps,
                )

            ready_streams: list[Any] = []
            streams = [stream for stream in (process.stdout, process.stderr) if stream is not None]
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
                    last_activity = now
                    stripped = chunk.strip()
                    if stripped:
                        try:
                            event = json.loads(stripped)
                        except json.JSONDecodeError:
                            last_event_message = f"stdout: {shorten_text(stripped)}"
                            last_activity_detail = last_event_message
                        else:
                            session_id = session_id or event.get("sessionID")
                            if event.get("type") == "step_start":
                                timestamp = event.get("timestamp")
                                if isinstance(timestamp, int):
                                    current_step_started_at = timestamp
                            elif event.get("type") == "step_finish":
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
                                            return (
                                                "".join(stdout_chunks),
                                                "".join(stderr_chunks),
                                                False,
                                                True,
                                                slow_reason,
                                                latest_preview_output_tps,
                                                preview_average_output_tps,
                                            )
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

            if now - last_heartbeat >= heartbeat_interval:
                file_count = count_files(project_dir)
                if file_count != last_file_count:
                    last_file_count = file_count
                    last_activity = now
                    last_activity_detail = f"project file count changed to {file_count}"
                session_hint = session_id if session_id else "-"
                detail = last_event_message if last_event_message else "waiting for output"
                remote_state = fetch_ollama_active_models(ollama_api_url)
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
                return (
                    "".join(stdout_chunks),
                    "".join(stderr_chunks),
                    False,
                    True,
                    stall_reason,
                    latest_preview_output_tps,
                    preview_average_output_tps,
                )

            if process.poll() is not None and not ready_streams:
                if stdout_buffer:
                    stdout_chunks.append(stdout_buffer)
                    stdout_file.write(stdout_buffer)
                if stderr_buffer:
                    stderr_chunks.append(stderr_buffer)
                    stderr_file.write(stderr_buffer)
                return (
                    "".join(stdout_chunks),
                    "".join(stderr_chunks),
                    False,
                    False,
                    None,
                    latest_preview_output_tps,
                    preview_average_output_tps,
                )


def run_model(
    model: dict[str, Any],
    prompt: str,
    runner: dict[str, Any],
    config_path: Path,
    results_dir: Path,
    timeout_seconds: int,
    force: bool,
    index: int,
    total: int,
    opencode_config_path: Path | None,
    no_progress_timeout_seconds: int,
    min_preview_output_tps: float | None,
    min_preview_samples: int,
    auto_skip_slow_preview: bool,
) -> dict[str, Any]:
    result_dir = results_dir / model["slug"]
    project_dir = result_dir / "project"
    prompt_path = result_dir / "prompt.txt"
    stdout_path = result_dir / "opencode-output.ndjson"
    stderr_path = result_dir / "opencode-stderr.log"
    result_path = result_dir / "result.json"
    result_dir.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt)

    if not force:
        cached = existing_terminal_result(result_path)
        if cached:
            print_line(
                f"[{index}/{total}] {model['slug']} skipping cached result status={cached['status']} elapsed={format_value(cached.get('elapsed_seconds'))}s"
            )
            return cached

    started_at = utc_now()
    command = [runner["command"], *runner["args"], "-m", model["id"], prompt]
    print_line("")
    print_line(f"[{index}/{total}] starting {model['slug']} -> {model['id']}")
    print_line(f"[{model['slug']}] results_dir={result_dir}")
    print_line(f"[{model['slug']}] timeout={timeout_seconds}s")
    if opencode_config_path is not None:
        print_line(f"[{model['slug']}] opencode_config={opencode_config_path}")
    print_line(f"[{model['slug']}] no_progress_timeout={no_progress_timeout_seconds}s")
    preflight_error: str | None = None
    if model["provider"] == "ollama":
        preflight_ok, preflight_message = ensure_ollama_target_model(model["id"], model["slug"], opencode_config_path)
        if not preflight_ok:
            preflight_error = preflight_message
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
                    "opencode_config": str(opencode_config_path) if opencode_config_path is not None else None,
                    "project_dir": str(project_dir),
                    "prompt": str(prompt_path),
                    "stderr": str(stderr_path),
                    "stdout": str(stdout_path),
                },
                "project_summary": summarize_project(project_dir),
                "prompt_sha256": prompt_sha256(prompt),
                "started_at": started_at,
                "status": "failed",
                "stderr_excerpt": "",
                "timed_out": False,
                "timeout_seconds": timeout_seconds,
                "no_progress_timeout_seconds": no_progress_timeout_seconds,
                "tokens": {},
                "tokens_per_second": None,
                "output_tokens_per_second": None,
                "preview_output_tokens_per_second": None,
                "preview_output_tokens_per_second_average": None,
                "preflight_error": preflight_error,
            }
            save_json(result_path, payload)
            print_line(f"[{index}/{total}] finished {model['slug']} status=failed preflight_error={preflight_error}")
            return payload
    wall_start = time.monotonic()
    process_env = os.environ.copy()
    if opencode_config_path is not None:
        process_env["OPENCODE_CONFIG"] = str(opencode_config_path)
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

    (
        stdout,
        stderr,
        timed_out,
        stalled,
        stall_reason,
        latest_preview_output_tps,
        preview_average_output_tps,
    ) = stream_process_output(
        process=process,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        project_dir=project_dir,
        model_slug=model["slug"],
        model_provider=model["provider"],
        timeout_seconds=timeout_seconds,
        no_progress_timeout_seconds=no_progress_timeout_seconds,
        min_preview_output_tps=min_preview_output_tps,
        min_preview_samples=min_preview_samples,
    )

    wall_end = time.monotonic()

    events = parse_event_stream(stdout)
    metrics = extract_metrics(events)
    project_summary = summarize_project(project_dir)
    elapsed_seconds = round(wall_end - wall_start, 2)
    total_tokens = metrics["tokens"].get("total")
    output_tokens = metrics["tokens"].get("output")

    if timed_out:
        status = "timeout"
    elif stalled:
        status = "failed"
    elif process.returncode == 0 and project_summary["works_as_intended"] == "yes":
        status = "completed"
    elif process.returncode == 0:
        status = "completed_with_errors"
    else:
        status = "failed"

    payload = {
        "assistant_output_excerpt": metrics["assistant_output"][:4000],
        "command": command,
        "elapsed_seconds": elapsed_seconds,
        "ended_at": utc_now(),
        "exit_code": process.returncode,
        "finish_reason": metrics["finish_reason"],
        "model": model,
        "opencode_session_id": metrics["session_id"],
        "paths": {
            "opencode_config": str(opencode_config_path) if opencode_config_path is not None else None,
            "project_dir": str(project_dir),
            "prompt": str(prompt_path),
            "stderr": str(stderr_path),
            "stdout": str(stdout_path),
        },
        "project_summary": project_summary,
        "prompt_sha256": prompt_sha256(prompt),
        "started_at": started_at,
        "status": status,
        "stderr_excerpt": stderr[:4000],
        "stalled": stalled,
        "stall_reason": stall_reason,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "no_progress_timeout_seconds": no_progress_timeout_seconds,
        "tokens": metrics["tokens"],
        "preview_output_tokens_per_second": latest_preview_output_tps,
        "preview_output_tokens_per_second_average": preview_average_output_tps,
        "tokens_per_second": round(total_tokens / elapsed_seconds, 2) if total_tokens and elapsed_seconds else None,
        "output_tokens_per_second": round(output_tokens / elapsed_seconds, 2)
        if output_tokens and elapsed_seconds
        else None,
    }
    save_json(result_path, payload)
    if (
        auto_skip_slow_preview
        and isinstance(min_preview_output_tps, float)
        and isinstance(preview_average_output_tps, float)
        and preview_average_output_tps < min_preview_output_tps
    ):
        note = (
            f" Skipped by default after benchmark preview averaged "
            f"{preview_average_output_tps:.2f} output tok/s over the first "
            f"{min_preview_samples} steps (< {min_preview_output_tps:.2f})."
        )
        if mark_model_skip_by_default(config_path, model["slug"], note):
            print_line(f"[{model['slug']}] marked skip_by_default in {config_path}")
    print_line(
        f"[{index}/{total}] finished {model['slug']} status={status} elapsed={elapsed_seconds:.2f}s files={project_summary['file_count']} total_tokens={format_value(metrics['tokens'].get('total'))}"
    )
    return payload


def load_results(
    config: dict[str, Any],
    results_dir: Path,
    warmup_payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    warmup_results = warmup_payload.get("results_by_slug", {}) if warmup_payload else {}
    for model in config["models"]:
        result_path = results_dir / model["slug"] / "result.json"
        if result_path.exists():
            row = load_json(result_path)
            row["ollama_warmup"] = warmup_results.get(model["slug"])
            rows.append(row)
            continue
        rows.append(
            {
                "status": "not_run",
                "elapsed_seconds": None,
                "tokens": {},
                "tokens_per_second": None,
                "output_tokens_per_second": None,
                "model": model,
                "ollama_warmup": warmup_results.get(model["slug"]),
                "project_summary": {
                    "file_count": 0,
                    "works_as_intended": "n/a",
                    "works_note": "Run has not been executed yet.",
                },
            }
        )
    return rows


def format_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def fallback_ollama_config_entry(model: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    model_name = model.get("ollama_model_name")
    if not isinstance(model_name, str) or not model_name:
        return None
    model_key = model["id"].split("/", 1)[1] if model["id"].startswith("ollama/") else model["id"]
    entry: dict[str, Any] = {
        "id": model_name,
        "name": model.get("ollama_display_name") or f"{model['label']} (Ollama)",
        "limit": {},
    }
    context_limit = model.get("ollama_limit_context")
    output_limit = model.get("ollama_limit_output")
    if isinstance(context_limit, int) and context_limit > 0:
        entry["limit"]["context"] = context_limit
    if isinstance(output_limit, int) and output_limit > 0:
        entry["limit"]["output"] = output_limit
    if model.get("ollama_tool_call") is True:
        entry["tool_call"] = True
    if model.get("ollama_reasoning") is True:
        entry["reasoning"] = True
    return model_key, entry


def prepare_local_opencode_config(
    models: list[dict[str, Any]],
    warmup_payload: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    summary = {
        "configured": [],
        "missing_warmup": [],
        "missing_source_entry": [],
        "skipped_reason": None,
        "source": str(OPENCODE_CONFIG_PATH),
    }
    source_config = load_opencode_config()
    if not source_config:
        summary["skipped_reason"] = f"missing opencode config at {OPENCODE_CONFIG_PATH}"
        return None, summary

    source_providers = source_config.get("provider", {})
    if not isinstance(source_providers, dict):
        summary["skipped_reason"] = "opencode config has no provider map"
        return None, summary

    warmup_results = warmup_payload.get("results_by_slug", {}) if warmup_payload else {}
    local_config: dict[str, Any] = {
        "$schema": source_config.get("$schema", "https://opencode.ai/config.json"),
        "permission": clone_json(OPENCODE_YOLO_PERMISSION),
        "provider": {},
    }

    selected_provider_names = sorted({model["provider"] for model in models if model["provider"] != "ollama"})
    for provider_name in selected_provider_names:
        provider_entry = source_providers.get(provider_name)
        if isinstance(provider_entry, dict):
            local_config["provider"][provider_name] = clone_json(provider_entry)

    ollama_provider = source_providers.get("ollama")
    if isinstance(ollama_provider, dict):
        local_ollama_provider = clone_json(ollama_provider)
        source_ollama_models = ollama_provider.get("models", {})
        local_ollama_models: dict[str, Any] = {}
    else:
        local_ollama_provider = None
        source_ollama_models = {}
        local_ollama_models = {}

    for model in models:
        if model.get("provider") != "ollama":
            continue

        warmup_entry = warmup_results.get(model["slug"])
        verified_context = warmup_entry.get("highest_verified_context") if isinstance(warmup_entry, dict) else None
        override_context = model.get("benchmark_context_override")

        model_key = model["id"].split("/", 1)[1] if model["id"].startswith("ollama/") else model["id"]
        config_entry = source_ollama_models.get(model_key) if isinstance(source_ollama_models, dict) else None
        fallback_entry = fallback_ollama_config_entry(model)
        if not isinstance(config_entry, dict) and fallback_entry is not None:
            _, config_entry = fallback_entry
        if not isinstance(config_entry, dict):
            summary["missing_source_entry"].append(model_key)
            continue

        local_entry = clone_json(config_entry)
        chosen_context = None
        if isinstance(override_context, int) and override_context > 0:
            chosen_context = override_context
        elif isinstance(verified_context, int) and verified_context > 0:
            chosen_context = verified_context

        if chosen_context is not None:
            local_entry.setdefault("limit", {})["context"] = chosen_context
            source_label = "override" if isinstance(override_context, int) and override_context > 0 else "warmup"
            summary["configured"].append(f"{model['slug']}={chosen_context} ({source_label})")
        else:
            summary["missing_warmup"].append(model["slug"])

        local_ollama_models[model_key] = local_entry

    if local_ollama_provider is not None:
        local_ollama_provider["models"] = local_ollama_models
        local_config["provider"]["ollama"] = local_ollama_provider

    if not local_config["provider"]:
        summary["skipped_reason"] = "no provider config available for selected models"
        return None, summary

    return local_config, summary


def write_local_opencode_config(
    path: Path,
    models: list[dict[str, Any]],
    warmup_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    local_config, summary = prepare_local_opencode_config(models, warmup_payload)
    if local_config is None:
        return summary
    save_json(path, local_config)
    summary["path"] = str(path)
    return summary


def print_local_opencode_config_summary(summary: dict[str, Any]) -> None:
    skipped_reason = summary.get("skipped_reason")
    if skipped_reason:
        print_line(f"Local opencode benchmark config skipped: {skipped_reason}")
        return

    path = summary.get("path")
    configured = summary.get("configured", [])
    missing_warmup = summary.get("missing_warmup", [])
    missing_source_entry = summary.get("missing_source_entry", [])
    source = summary.get("source")

    if path:
        print_line(f"Local opencode benchmark config: {path}")
    if source:
        print_line(f"Local opencode benchmark config source: {source}")
    print_line("Local opencode benchmark permissions: yolo (auto-approve enabled)")
    if configured:
        print_line(f"Ollama benchmark contexts: {', '.join(configured)}")
    else:
        print_line("Ollama benchmark contexts: none")
    if missing_warmup:
        print_line(f"Ollama benchmark config missing warmup: {', '.join(missing_warmup)}")
    if missing_source_entry:
        print_line(f"Ollama benchmark config missing source entries: {', '.join(missing_source_entry)}")


def build_notes(result: dict[str, Any], warmup_minimum_useful_context: int | None) -> str:
    summary = result["project_summary"]
    notes = summary.get("works_note", "")
    if result.get("timed_out"):
        notes = f"Timed out. {notes}".strip()
    elif result.get("exit_code") not in (None, 0):
        notes = f"Exit code {result['exit_code']}. {notes}".strip()

    warmup = result.get("ollama_warmup")
    if isinstance(warmup, dict):
        highest = warmup.get("highest_verified_context")
        recommendation = warmup.get("recommendation")
        if highest is None:
            warmup_note = "Warmup found no verified Ollama context."
        elif warmup_minimum_useful_context is not None and highest < warmup_minimum_useful_context:
            warmup_note = f"Warmup only verified up to {highest} context."
        else:
            warmup_note = f"Warmup verified {highest} context."
        if isinstance(recommendation, str) and recommendation:
            warmup_note = f"{warmup_note} {recommendation}."
        notes = f"{notes} {warmup_note}".strip()

    return notes.replace("|", "/")


def build_report(
    config: dict[str, Any],
    results: list[dict[str, Any]],
    prompt: str,
    warmup_payload: dict[str, Any] | None = None,
    warmup_path: Path | None = None,
) -> str:
    lines: list[str] = []
    counts: dict[str, int] = {}
    warmup_minimum_useful_context = None
    if warmup_payload:
        minimum = warmup_payload.get("minimum_useful_context")
        if isinstance(minimum, int):
            warmup_minimum_useful_context = minimum
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    lines.append("# Benchmark Report")
    lines.append("")
    lines.append(f"Generated at: {utc_now()}")
    lines.append(f"Prompt SHA256: `{prompt_sha256(prompt)}`")
    lines.append("")
    lines.append("## Progress")
    lines.append("")
    for status in ("completed", "completed_with_errors", "failed", "timeout", "not_run"):
        lines.append(f"- `{status}`: {counts.get(status, 0)}")
    lines.append("")
    lines.append("## Runner")
    lines.append("")
    lines.append("`opencode run --agent build --format json`")
    lines.append("")
    for note in config["runner"]["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("## Model Selection")
    lines.append("")
    for model in config["models"]:
        lines.append(f"- `{model['slug']}` -> `{model['id']}`: {model['selection_reason']}")
    lines.append("")
    if warmup_payload:
        lines.append("## Ollama Warmup")
        lines.append("")
        if warmup_path is not None:
            lines.append(f"Loaded from `{warmup_path}`.")
            lines.append("")
        if warmup_minimum_useful_context is not None:
            lines.append(f"Minimum useful context target: `{warmup_minimum_useful_context}`")
            lines.append("")
        lines.append("| Model | Highest verified ctx | Recommendation |")
        lines.append("| --- | ---: | --- |")
        for result in results:
            model = result["model"]
            if model["provider"] != "ollama":
                continue
            warmup = result.get("ollama_warmup")
            if isinstance(warmup, dict):
                highest = format_value(warmup.get("highest_verified_context"))
                recommendation = str(warmup.get("recommendation", "-")).replace("|", "/")
            else:
                highest = "-"
                recommendation = "No warmup result recorded."
            lines.append(f"| {model['label']} | {highest} | {recommendation} |")
        lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| Model | Provider | Warmup ctx | Status | Elapsed (s) | Total tokens | Tok/s | Works? | Files | Notes |")
    lines.append("| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |")
    for result in results:
        model = result["model"]
        summary = result["project_summary"]
        tokens = result.get("tokens", {})
        warmup = result.get("ollama_warmup")
        warmup_context = format_value(warmup.get("highest_verified_context")) if isinstance(warmup, dict) else "-"
        notes = build_notes(result, warmup_minimum_useful_context)
        lines.append(
            "| {label} | {provider} | {warmup_context} | {status} | {elapsed} | {total_tokens} | {tps} | {works} | {files} | {notes} |".format(
                label=model["label"],
                provider=model["provider"],
                warmup_context=warmup_context,
                status=result["status"],
                elapsed=format_value(result.get("elapsed_seconds")),
                total_tokens=format_value(tokens.get("total")),
                tps=format_value(result.get("tokens_per_second")),
                works=summary.get("works_as_intended", "-"),
                files=format_value(summary.get("file_count")),
                notes=notes or "-",
            )
        )
    lines.append("")
    lines.append("## Per-Run Paths")
    lines.append("")
    lines.append("Each run writes to `results/<slug>/` with these files:")
    lines.append("")
    lines.append("- `project/`: the generated project workspace")
    lines.append("- `prompt.txt`: exact prompt used for the run")
    lines.append("- `opencode-output.ndjson`: raw JSON event stream from opencode")
    lines.append("- `opencode-stderr.log`: stderr from the opencode process")
    lines.append("- `result.json`: normalized metadata used for this report")
    lines.append("")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark coding models through opencode.")
    parser.add_argument("--config", default="config/models.json")
    parser.add_argument("--opencode-config", default="config/opencode.benchmark.json")
    parser.add_argument("--prompt", default="prompts/benchmark_prompt.txt")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--report", default="docs/report.md")
    parser.add_argument("--ollama-warmup-results", default="results/ollama_warmup.json")
    parser.add_argument("--timeout-minutes", type=int, default=90)
    parser.add_argument(
        "--no-progress-minutes",
        type=int,
        default=DEFAULT_NO_PROGRESS_MINUTES,
        help="Fail a run if stdout, stderr, and project files stay idle for this many minutes.",
    )
    parser.add_argument("--model", action="append", dest="models", help="Run only the given slug(s).")
    parser.add_argument("--max-runs", type=int, default=None, help="Cap how many models to execute this invocation.")
    parser.add_argument("--force", action="store_true", help="Re-run even if a terminal result.json already exists.")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip execution and only rebuild docs/report.md from saved result.json files.",
    )
    parser.add_argument(
        "--sync-ollama-contexts-only",
        action="store_true",
        help="Write the local benchmark opencode config from warmup results and exit.",
    )
    parser.add_argument(
        "--min-preview-output-tps",
        type=float,
        default=None,
        help="Abort a model early if the average output tokens/sec over the first preview steps stays below this threshold.",
    )
    parser.add_argument(
        "--min-preview-samples",
        type=int,
        default=3,
        help="How many completed steps to average before enforcing the preview output tokens/sec threshold.",
    )
    parser.add_argument(
        "--auto-skip-slow-preview",
        action="store_true",
        help="When the preview output tokens/sec threshold fails, set skip_by_default=true in the benchmark config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    opencode_config_path = Path(args.opencode_config)
    prompt_path = Path(args.prompt)
    results_dir = Path(args.results_dir)
    report_path = Path(args.report)
    warmup_path = Path(args.ollama_warmup_results)

    if shutil.which("opencode") is None:
        print("opencode is not available on PATH", file=sys.stderr)
        return 1

    config = load_json(config_path)
    prompt = prompt_path.read_text().strip()
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    selected_models = [model for model in config["models"] if not model.get("skip_by_default")]
    if args.models:
        wanted = set(args.models)
        selected_models = [model for model in config["models"] if model["slug"] in wanted]
        missing = wanted - {model["slug"] for model in selected_models}
        if missing:
            print(f"Unknown model slug(s): {', '.join(sorted(missing))}", file=sys.stderr)
            return 1

    if args.max_runs is not None:
        selected_models = selected_models[: args.max_runs]

    warmup_payload = load_ollama_warmup_payload(warmup_path)

    if args.sync_ollama_contexts_only:
        config_summary = write_local_opencode_config(opencode_config_path, selected_models, warmup_payload)
        print_local_opencode_config_summary(config_summary)
        return 0

    if not args.report_only:
        config_summary = write_local_opencode_config(opencode_config_path, selected_models, warmup_payload)
        print_local_opencode_config_summary(config_summary)
        opencode_override = opencode_config_path if config_summary.get("path") else None
        runner = config["runner"]
        timeout_seconds = args.timeout_minutes * 60
        no_progress_timeout_seconds = args.no_progress_minutes * 60
        total_models = len(selected_models)
        print_line(
            f"Benchmark run starting: models={total_models} timeout={timeout_seconds}s "
            f"no_progress_timeout={no_progress_timeout_seconds}s force={args.force}"
        )
        for index, model in enumerate(selected_models, start=1):
            run_model(
                model,
                prompt,
                runner,
                config_path,
                results_dir,
                timeout_seconds,
                args.force,
                index,
                total_models,
                opencode_override,
                no_progress_timeout_seconds,
                args.min_preview_output_tps,
                args.min_preview_samples,
                args.auto_skip_slow_preview,
            )

    results = load_results(config, results_dir, warmup_payload)
    report_path.write_text(build_report(config, results, prompt, warmup_payload, warmup_path))
    completed = sum(1 for result in results if result["status"] != "not_run")
    print_line(f"Report updated: {report_path}")
    print_line(f"Progress snapshot: completed_or_attempted={completed}/{len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
