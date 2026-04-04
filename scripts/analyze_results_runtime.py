#!/usr/bin/env python3
"""Verify benchmark-generated Rails apps by booting them locally and via Docker."""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark.util import load_json, save_json, utc_now


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
SCRIPT_DIR = Path(__file__).resolve().parent
BROWSER_PROBE = SCRIPT_DIR / "browser_probe.mjs"
RUNTIME_DIRNAME = "_runtime_verification"


@dataclass
class CommandResult:
    ok: bool
    command: list[str]
    cwd: Path
    exit_code: int | None
    elapsed_seconds: float
    stdout_path: Path
    stderr_path: Path
    note: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify benchmark-generated Rails apps.")
    parser.add_argument("--results-dir", default=str(RESULTS_DIR))
    parser.add_argument("--max-projects", type=int)
    parser.add_argument("--only")
    parser.add_argument("--local-timeout", type=int, default=240)
    parser.add_argument("--bundle-timeout", type=int, default=900)
    parser.add_argument("--docker-build-timeout", type=int, default=1800)
    parser.add_argument("--docker-run-timeout", type=int, default=300)
    parser.add_argument("--browser-timeout", type=int, default=90)
    return parser.parse_args()


def summarize_file(path: Path, max_lines: int = 40) -> str:
    if not path.exists():
        return "(missing)"
    lines = path.read_text(errors="replace").splitlines()
    if not lines:
        return "(empty)"
    excerpt = lines[-max_lines:]
    return "\n".join(excerpt)


def safe_slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text).strip("-").lower()


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def load_openrouter_api_key() -> str | None:
    command = [
        "zsh",
        "-lc",
        'source ~/.config/zsh/secrets >/dev/null 2>&1 && printf %s "$OPENROUTER_API_KEY"',
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
    except Exception:
        return None
    value = completed.stdout.strip()
    return value or None


def command_env(api_key: str | None, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if api_key:
        env["OPENROUTER_API_KEY"] = api_key
    if extra:
        env.update(extra)
    return env


def discover_app_root(project_dir: Path) -> Path | None:
    candidates: list[tuple[int, Path]] = []
    for candidate in [project_dir, *sorted(project_dir.glob("*")), *sorted(project_dir.glob("*/*"))]:
        if not candidate.is_dir():
            continue
        if (candidate / "Gemfile").exists():
            score = 0
            if (candidate / "config" / "routes.rb").exists():
                score += 3
            if (candidate / "bin" / "rails").exists():
                score += 2
            if candidate == project_dir:
                score += 1
            candidates.append((score, candidate))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], len(item[1].parts), str(item[1])))
    return candidates[0][1]


def mise_config_paths(app_root: Path, project_dir: Path) -> list[Path]:
    configs: list[Path] = []
    for directory in [app_root, *app_root.parents]:
        if not str(directory).startswith(str(project_dir)):
            continue
        for name in (".mise.toml", "mise.toml"):
            candidate = directory / name
            if candidate.exists():
                configs.append(candidate)
        if directory == project_dir:
            break
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in configs:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def run_command(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    stdout_path: Path,
    stderr_path: Path,
) -> CommandResult:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with stdout_path.open("w") as stdout_handle, stderr_path.open("w") as stderr_handle:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            start_new_session=True,
        )
        try:
            exit_code = process.wait(timeout=timeout_seconds)
            ok = exit_code == 0
            note = None
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            exit_code = None
            ok = False
            note = f"timed out after {timeout_seconds}s"
    elapsed = round(time.monotonic() - started, 2)
    return CommandResult(ok, command, cwd, exit_code, elapsed, stdout_path, stderr_path, note)


def wait_for_http(url: str, timeout_seconds: int = 60) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            completed = subprocess.run(
                ["curl", "-I", "-s", url],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if completed.returncode == 0 and "HTTP/" in completed.stdout:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def run_browser_probe(url: str, out_dir: Path, message: str, timeout_seconds: int) -> dict[str, Any]:
    command = [
        "node",
        str(BROWSER_PROBE),
        "--url",
        url,
        "--out-dir",
        str(out_dir),
        "--message",
        message,
        "--timeout-seconds",
        str(timeout_seconds),
    ]
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout_seconds + 30, check=False)
    payload_path = out_dir / "browser_probe.json"
    payload = load_json(payload_path) if payload_path.exists() else {
        "ok": False,
        "error": completed.stderr.strip() or completed.stdout.strip() or "browser probe failed without JSON output",
    }
    payload["command_exit_code"] = completed.returncode
    return payload


def cleanup_container(name: str) -> None:
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True, check=False)


def cleanup_compose(app_root: Path, env: dict[str, str]) -> None:
    subprocess.run(["docker", "compose", "down", "-v", "--remove-orphans"], cwd=app_root, env=env, capture_output=True, text=True, check=False)


def detect_compose_host_port(app_root: Path) -> int:
    """Try to detect the host port from compose file port mappings. Fallback to 3000."""
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        compose_file = app_root / name
        if not compose_file.exists():
            continue
        try:
            content = compose_file.read_text()
        except OSError:
            continue
        # Match port mappings like "3000:3000", "8080:3000", '3000:3000'
        matches = re.findall(r'["\']?(\d{2,5}):(\d{2,5})["\']?', content)
        if matches:
            return int(matches[0][0])
    return 3000


def detect_compose_published_port(app_root: Path, env: dict[str, str]) -> int | None:
    """Parse `docker compose ps` output for published port mappings after containers are up."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=app_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                publishers = entry.get("Publishers") or []
                for pub in publishers:
                    published = pub.get("PublishedPort")
                    if isinstance(published, int) and published > 0:
                        return published
    except Exception:
        pass
    return None


def command_result_payload(result: CommandResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "command": result.command,
        "cwd": str(result.cwd),
        "exit_code": result.exit_code,
        "elapsed_seconds": result.elapsed_seconds,
        "note": result.note,
        "stdout": result.stdout_path.name,
        "stderr": result.stderr_path.name,
        "stdout_excerpt": summarize_file(result.stdout_path, 20),
        "stderr_excerpt": summarize_file(result.stderr_path, 20),
    }


def local_attempt(project_dir: Path, app_root: Path, runtime_dir: Path, api_key: str | None, timeouts: argparse.Namespace) -> dict[str, Any]:
    method_dir = runtime_dir / "local"
    method_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = method_dir / "bundle"
    env = command_env(
        api_key,
        {
            "BUNDLE_PATH": str(bundle_path),
            "BUNDLE_WITHOUT": "",
            "RAILS_ENV": "development",
            "PORT": "3000",
        },
    )
    result: dict[str, Any] = {"method": "local", "app_root": str(app_root)}

    trust_results: list[dict[str, Any]] = []
    for config_path in mise_config_paths(app_root, project_dir):
        trusted = run_command(
            ["mise", "trust", str(config_path)],
            cwd=app_root,
            env=env,
            timeout_seconds=30,
            stdout_path=method_dir / f"mise-trust-{config_path.name}.stdout.log",
            stderr_path=method_dir / f"mise-trust-{config_path.name}.stderr.log",
        )
        trust_results.append(command_result_payload(trusted))
    if trust_results:
        result["mise_trust"] = trust_results

    bundle = run_command(
        ["bundle", "install"],
        cwd=app_root,
        env=env,
        timeout_seconds=timeouts.bundle_timeout,
        stdout_path=method_dir / "bundle-install.stdout.log",
        stderr_path=method_dir / "bundle-install.stderr.log",
    )
    result["bundle_install"] = command_result_payload(bundle)
    if not bundle.ok:
        return result

    tailwind = run_command(
        ["bundle", "exec", "rails", "tailwindcss:build"],
        cwd=app_root,
        env=env,
        timeout_seconds=180,
        stdout_path=method_dir / "tailwind.stdout.log",
        stderr_path=method_dir / "tailwind.stderr.log",
    )
    result["tailwind_build"] = command_result_payload(tailwind)

    port = find_free_port()
    env["PORT"] = str(port)
    server_stdout = method_dir / "server.stdout.log"
    server_stderr = method_dir / "server.stderr.log"
    with server_stdout.open("w") as stdout_handle, server_stderr.open("w") as stderr_handle:
        process = subprocess.Popen(
            ["bundle", "exec", "rails", "server", "-b", "127.0.0.1", "-p", str(port)],
            cwd=app_root,
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            start_new_session=True,
        )
    url = f"http://127.0.0.1:{port}"
    result["url"] = url
    try:
        ready = wait_for_http(url, timeout_seconds=60)
        result["server_ready"] = ready
        if ready:
            probe = run_browser_probe(url, method_dir / "browser", "hello world", timeouts.browser_timeout)
            result["browser_probe"] = probe
        else:
            result["browser_probe"] = {"ok": False, "error": "server never became ready"}
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
        except Exception:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except Exception:
                pass

    result["server_stdout_excerpt"] = summarize_file(server_stdout, 25)
    result["server_stderr_excerpt"] = summarize_file(server_stderr, 25)
    result["success"] = bool(result.get("server_ready") and result.get("browser_probe", {}).get("ok"))
    return result


def docker_build_attempt(app_root: Path, runtime_dir: Path, timeouts: argparse.Namespace) -> dict[str, Any]:
    method_dir = runtime_dir / "docker-build"
    method_dir.mkdir(parents=True, exist_ok=True)
    tag = f"llm-benchmark-{safe_slug(app_root.parent.name)}-{safe_slug(app_root.name)}"
    build = run_command(
        ["docker", "build", "-t", tag, "."],
        cwd=app_root,
        env=os.environ.copy(),
        timeout_seconds=timeouts.docker_build_timeout,
        stdout_path=method_dir / "docker-build.stdout.log",
        stderr_path=method_dir / "docker-build.stderr.log",
    )
    result = {
        "method": "docker-build",
        "image_tag": tag,
        "build": command_result_payload(build),
        "success": build.ok,
    }
    return result


def docker_compose_attempt(app_root: Path, runtime_dir: Path, api_key: str | None, timeouts: argparse.Namespace) -> dict[str, Any]:
    method_dir = runtime_dir / "docker-compose"
    method_dir.mkdir(parents=True, exist_ok=True)
    if not (app_root / "docker-compose.yml").exists() and not (app_root / "compose.yml").exists():
        return {"method": "docker-compose", "success": False, "note": "no docker compose file"}

    env = command_env(
        api_key,
        {
            "COMPOSE_PROJECT_NAME": f"llmbench_{safe_slug(app_root.parent.name)}_{safe_slug(app_root.name)}",
        },
    )
    cleanup_compose(app_root, env)
    up = run_command(
        ["docker", "compose", "up", "--build", "-d"],
        cwd=app_root,
        env=env,
        timeout_seconds=timeouts.docker_build_timeout,
        stdout_path=method_dir / "compose-up.stdout.log",
        stderr_path=method_dir / "compose-up.stderr.log",
    )
    result: dict[str, Any] = {
        "method": "docker-compose",
        "compose_up": command_result_payload(up),
        "success": False,
    }
    if not up.ok:
        cleanup_compose(app_root, env)
        return result

    # Detect port: try docker compose ps first, then parse compose file, fallback to 3000
    port = detect_compose_published_port(app_root, env) or detect_compose_host_port(app_root)
    url = f"http://127.0.0.1:{port}"
    ready = wait_for_http(url, timeout_seconds=90)
    result["url"] = url
    result["detected_port"] = port
    result["compose_ready"] = ready
    if ready:
        result["browser_probe"] = run_browser_probe(url, method_dir / "browser", "hello world", timeouts.browser_timeout)
        result["success"] = bool(result["browser_probe"].get("ok"))
    else:
        result["browser_probe"] = {"ok": False, "error": f"docker compose app never became reachable on port {port}"}

    ps = subprocess.run(["docker", "compose", "ps"], cwd=app_root, env=env, capture_output=True, text=True, check=False)
    logs = subprocess.run(["docker", "compose", "logs", "--no-color", "--tail", "200"], cwd=app_root, env=env, capture_output=True, text=True, check=False)
    (method_dir / "compose-ps.log").write_text(ps.stdout + ps.stderr)
    (method_dir / "compose-logs.log").write_text(logs.stdout + logs.stderr)
    cleanup_compose(app_root, env)
    return result


def write_report(report_path: Path, report: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append(f"# Runtime Verification: {report['slug']}")
    lines.append("")
    lines.append(f"- Result status: `{report.get('benchmark_status')}`")
    lines.append(f"- Original benchmark verdict: `{report.get('benchmark_works')}`")
    lines.append(f"- Project dir: `{report.get('project_dir')}`")
    lines.append(f"- App root: `{report.get('app_root') or '-'} `")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Local run: `{report['methods'].get('local', {}).get('success', False)}`")
    lines.append(f"- Docker build: `{report['methods'].get('docker_build', {}).get('success', False)}`")
    lines.append(f"- Docker compose: `{report['methods'].get('docker_compose', {}).get('success', False)}`")
    lines.append("")
    for key, title in (
        ("local", "Local Run"),
        ("docker_build", "Docker Build"),
        ("docker_compose", "Docker Compose"),
    ):
        payload = report["methods"].get(key, {})
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"- Success: `{payload.get('success', False)}`")
        note = payload.get("note")
        if note:
            lines.append(f"- Note: {note}")
        browser = payload.get("browser_probe")
        if browser:
            lines.append(f"- Browser probe ok: `{browser.get('ok', False)}`")
            lines.append(f"- Response observed: `{browser.get('responseObserved')}`")
            if browser.get("error"):
                lines.append(f"- Browser error: `{browser['error']}`")
        if key == "local":
            lines.append("")
            lines.append("### Server stderr excerpt")
            lines.append("")
            lines.append("```text")
            lines.append(payload.get("server_stderr_excerpt", "(none)"))
            lines.append("```")
        if key == "docker_build":
            build = payload.get("build", {})
            lines.append("")
            lines.append("### Build stderr excerpt")
            lines.append("")
            lines.append("```text")
            lines.append(build.get("stderr_excerpt", "(none)"))
            lines.append("```")
        if key == "docker_compose":
            compose_up = payload.get("compose_up", {})
            lines.append("")
            lines.append("### Compose stderr excerpt")
            lines.append("")
            lines.append("```text")
            lines.append(compose_up.get("stderr_excerpt", "(none)"))
            lines.append("```")
        lines.append("")

    report_path.write_text("\n".join(lines).rstrip() + "\n")


def analyze_one(result_dir: Path, result_payload: dict[str, Any], args: argparse.Namespace, api_key: str | None) -> dict[str, Any]:
    project_dir = result_dir / "project"
    runtime_dir = project_dir / RUNTIME_DIRNAME
    runtime_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "slug": result_dir.name,
        "benchmark_status": result_payload.get("status"),
        "benchmark_works": (result_payload.get("project_summary") or {}).get("works_as_intended"),
        "project_dir": str(project_dir),
        "app_root": None,
        "methods": {},
    }

    app_root = discover_app_root(project_dir)
    if app_root is None:
        report["methods"]["local"] = {"success": False, "note": "no Rails app root discovered"}
        report["methods"]["docker_build"] = {"success": False, "note": "no Rails app root discovered"}
        report["methods"]["docker_compose"] = {"success": False, "note": "no Rails app root discovered"}
        save_json(runtime_dir / "runtime_report.json", report)
        write_report(runtime_dir / "runtime_report.md", report)
        return report

    report["app_root"] = str(app_root)
    report["methods"]["local"] = local_attempt(project_dir, app_root, runtime_dir, api_key, args)
    report["methods"]["docker_build"] = docker_build_attempt(app_root, runtime_dir, args)
    report["methods"]["docker_compose"] = docker_compose_attempt(app_root, runtime_dir, api_key, args)
    save_json(runtime_dir / "runtime_report.json", report)
    write_report(runtime_dir / "runtime_report.md", report)
    return report


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir)
    api_key = load_openrouter_api_key()
    summaries: list[dict[str, Any]] = []

    result_paths = sorted(results_dir.glob("*/result.json"))
    if args.only:
        only = {slug.strip() for slug in args.only.split(",") if slug.strip()}
        result_paths = [path for path in result_paths if path.parent.name in only]
    if args.max_projects is not None:
        result_paths = result_paths[: args.max_projects]

    for result_path in result_paths:
        payload = load_json(result_path)
        report = analyze_one(result_path.parent, payload, args, api_key)
        summaries.append(
            {
                "slug": report["slug"],
                "benchmark_status": report["benchmark_status"],
                "benchmark_works": report["benchmark_works"],
                "app_root": report["app_root"],
                "local_success": report["methods"]["local"].get("success", False),
                "docker_build_success": report["methods"]["docker_build"].get("success", False),
                "docker_compose_success": report["methods"]["docker_compose"].get("success", False),
            }
        )
        print(f"[{report['slug']}] local={summaries[-1]['local_success']} docker_build={summaries[-1]['docker_build_success']} docker_compose={summaries[-1]['docker_compose_success']}")

    summary_path = results_dir / "runtime_verification_summary.json"
    save_json(summary_path, {"generated_at": utc_now(), "results": summaries})
    print(f"summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
