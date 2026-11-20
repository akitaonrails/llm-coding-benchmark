#!/usr/bin/env python3
"""Benchmark v5 orchestrator: Cost, Speed & Prompt-Caching Economics.

Runs the 14-goal greenfield Rails web app (2 phases: build + validate, plus up
to 2 standardized nudges if the automated quality gate fails) across each
model family's preferred native harness with full anti-cheat isolation and
5-bucket cache-aware token/cost accounting.
"""
from __future__ import annotations

import argparse
import atexit
import json
import os
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from shlex import quote as shlex_quote
from typing import Any, Iterator, cast

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from benchmark.runner import (  # noqa: E402
    OPENCODE_YOLO_PERMISSION,
    parse_event_stream,
)
from benchmark.util import save_json, utc_now  # noqa: E402
from benchmark.v5_metrics import (  # noqa: E402
    compute_cost_breakdown,
    extract_v5_usage,
    sum_token_dicts,
)

PHASE_TIMEOUT = int(os.environ.get("V5_PHASE_TIMEOUT", "3600"))
STALL_TIMEOUT = int(os.environ.get("V5_STALL_TIMEOUT", "1200"))
KIMI_TERMINAL_GRACE = 8


def count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)


def load_secrets_into_env(env: dict[str, str]) -> None:
    secrets_file = Path.home() / ".config" / "zsh" / "secrets"
    if not secrets_file.exists():
        return
    for line in secrets_file.read_text().splitlines():
        line = line.strip()
        if line.startswith("export ") and "=" in line:
            name, _, value = line[len("export "):].partition("=")
            name = name.strip()
            if name and name not in env:
                env[name] = value.strip().strip('"').strip("'")


@contextmanager
def anti_cheat_shield(active_results_dir: Path, active_slug: str, enabled: bool = True) -> Iterator[None]:
    """Atomically move grading keys, reports, and sibling workspaces outside the repo."""
    if not enabled:
        yield
        return

    # Place shield on the same filesystem as REPO_ROOT (for instant atomic rename)
    # under a non-obvious temp directory name.
    shield_root = Path(tempfile.mkdtemp(prefix=".v5_iso_", dir=REPO_ROOT.parent))
    moved: list[tuple[Path, Path]] = []

    def _move(src: Path, rel_key: str) -> None:
        if not src.exists():
            return
        dst = shield_root / rel_key
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        moved.append((src, dst))

    def _restore() -> None:
        all_restored = True
        while moved:
            src, dst = moved.pop()
            if dst.exists():
                if src.exists():
                    # Never lose shielded data if something recreated an empty src dir
                    backup = src.parent / f"{src.name}.conflict-{int(time.time())}"
                    src.rename(backup)
                src.parent.mkdir(parents=True, exist_ok=True)
                dst.rename(src)
            elif not src.exists():
                all_restored = False
        if all_restored:
            shutil.rmtree(shield_root, ignore_errors=True)

    atexit.register(_restore)
    try:
        _move(REPO_ROOT / "CLAUDE.md", "CLAUDE.md")
        _move(REPO_ROOT / "benchmark-v5" / "DESIGN.md", "benchmark-v5/DESIGN.md")
        _move(REPO_ROOT / ".agents" / "skills" / "benchmark-audit", "benchmark-audit")
        docs_dir = REPO_ROOT / "docs"
        if docs_dir.exists():
            for p in docs_dir.glob("success_report*.md"):
                _move(p, f"docs/{p.name}")
            _move(docs_dir / "audit_prompt_template.md", "docs/audit_prompt_template.md")
        # Move older result directories
        for res_dir in REPO_ROOT.glob("results*"):
            if res_dir.resolve() == active_results_dir.resolve():
                continue
            if res_dir.is_dir():
                _move(res_dir, f"old_results/{res_dir.name}")
        # Move sibling workspaces in active_results_dir
        if active_results_dir.exists():
            for sib in active_results_dir.iterdir():
                if sib.is_dir() and sib.name != active_slug:
                    _move(sib, f"siblings/{sib.name}")
        yield
    finally:
        _restore()
        atexit.unregister(_restore)


def build_command(
    model: dict[str, Any],
    prompt: str,
    project_dir: Path,
    out_dir: Path,
    env: dict[str, str],
) -> tuple[list[str], str | None, Path | None]:
    """Build native CLI command, optional stdin, and optional temp HOME to clean up."""
    harness = model["harness"]
    model_id = model["model_id"]
    stdin_data: str | None = None
    temp_home: Path | None = None

    if harness == "claude":
        temp_home = Path(tempfile.mkdtemp(prefix="v5-claude-home-"))
        env["HOME"] = str(temp_home)
        real_creds = Path.home() / ".claude" / ".credentials.json"
        iso_claude = temp_home / ".claude"
        iso_claude.mkdir(parents=True, exist_ok=True)
        if real_creds.exists():
            shutil.copy2(real_creds, iso_claude / ".credentials.json")
        env.pop("ANTHROPIC_API_KEY", None)
        cmd = [
            "claude", "-p",
            "--model", model_id,
            "--output-format", "stream-json",
            "--dangerously-skip-permissions",
            "--verbose",
            prompt,
        ]
        return cmd, None, temp_home

    if harness == "codex":
        effort = model.get("codex_reasoning_effort")
        args = [
            "codex", "exec",
            "--json",
            "--skip-git-repo-check",
            "-m", model_id,
            "-C", str(project_dir.resolve()),
            "--dangerously-bypass-approvals-and-sandbox",
        ]
        if effort:
            args += ["-c", f"model_reasoning_effort={effort}"]
        args.append("-")
        cmd = ["bash", "-lc", " ".join(shlex_quote(a) for a in args)]
        return cmd, prompt, None

    if harness == "agy":
        preamble = (
            f"Your workspace directory is {project_dir.resolve()}. Do ALL work inside it; "
            f"create and edit every file under that absolute path, never in any other scratch area.\n\n"
        )
        cmd = [
            "agy", "--print", preamble + prompt,
            "--model", model_id,
            "--output-format", "stream-json",
            "--dangerously-skip-permissions",
            "--add-dir", str(project_dir.resolve()),
            "--print-timeout", "90m",
        ]
        return cmd, None, None

    if harness == "grok":
        args = [
            "grok", "-m", model_id, "-p", prompt,
            "--max-turns", "400",
            "--always-approve",
            "--disable-web-search",
            "--output-format", "streaming-json",
        ]
        cmd = ["bash", "-lc", " ".join(shlex_quote(a) for a in args)]
        return cmd, None, None

    if harness == "zcode":
        zc_cfg = Path.home() / ".zcode" / "cli" / "config.json"
        if zc_cfg.exists():
            _c = json.loads(zc_cfg.read_text())
            _c.setdefault("model", {})["main"] = model_id
            zc_cfg.write_text(json.dumps(_c, indent=1))
        cmd = [
            "zcode",
            f"--prompt={prompt}",
            f"--cwd={project_dir.resolve()}",
            "--mode=yolo", "--json", "--verbose",
        ]
        return cmd, None, None

    if harness == "kimi":
        args = ["kimi", "-p", prompt, "--output-format", "stream-json", "-m", model_id]
        cmd = ["bash", "-lc", " ".join(shlex_quote(a) for a in args)]
        return cmd, None, None

    if harness == "qwen":
        args = [
            "qwen", "-m", model_id,
            "--yolo",
            "-o", "stream-json",
            prompt,
        ]
        cmd = ["bash", "-lc", " ".join(shlex_quote(a) for a in args)]
        return cmd, None, None

    if harness == "muse":
        temp_home = Path(tempfile.mkdtemp(prefix="v5-muse-home-"))
        iso_cfg = temp_home / ".config"
        iso_data = temp_home / ".local" / "share"
        for p in (iso_cfg, iso_data):
            p.mkdir(parents=True, exist_ok=True)
        chrome_xdg = REPO_ROOT / "config" / "chrome-headless-xdg"
        if chrome_xdg.exists():
            for item in chrome_xdg.iterdir():
                dst = iso_cfg / item.name
                if not dst.exists():
                    if item.is_dir():
                        shutil.copytree(item, dst)
                    else:
                        shutil.copy2(item, dst)
        (iso_cfg / "muse").mkdir(parents=True, exist_ok=True)
        real_auth = Path.home() / ".config" / "muse" / "auth.json"
        if real_auth.exists():
            shutil.copy2(real_auth, iso_cfg / "muse" / "auth.json")
        env["HOME"] = str(temp_home)
        env["XDG_CONFIG_HOME"] = str(iso_cfg)
        env["XDG_DATA_HOME"] = str(iso_data)
        # Keep mise pointing at the real host mise data dir so it never reinstalls muse into /tmp
        env["MISE_DATA_DIR"] = str(Path.home() / ".local" / "share" / "mise")
        env.pop("META_API_KEY", None)
        args = [
            "muse", "exec", "--json", "--provider", "meta",
            "--model", model_id,
            "--workspace", str(project_dir.resolve()),
            prompt,
        ]
        cmd = ["bash", "-lc", " ".join(shlex_quote(a) for a in args)]
        return cmd, None, temp_home

    if harness == "opencode":
        opencode_config = REPO_ROOT / "config" / "opencode.benchmark.json"
        if opencode_config.exists():
            env["OPENCODE_CONFIG"] = str(opencode_config.resolve())
        env["OPENCODE_PERMISSION"] = json.dumps(OPENCODE_YOLO_PERMISSION, separators=(",", ":"))
        xdg_iso = REPO_ROOT / "config" / "opencode.xdg-isolated"
        (xdg_iso / "opencode").mkdir(parents=True, exist_ok=True)
        env["XDG_CONFIG_HOME"] = str(xdg_iso.resolve())
        # opencode 2.x removed `--dir` (uses process cwd) and uses `--auto` for YOLO approval
        cmd = [
            "opencode", "run", "--agent", "build", "--format", "json", "--auto",
            "-m", model_id,
            prompt,
        ]
        return cmd, None, None

    raise ValueError(f"Unknown harness: {harness}")


def run_phase(
    model: dict[str, Any],
    rates: dict[str, Any],
    phase_name: str,
    prompt: str,
    project_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    harness = model["harness"]
    stdout_path = out_dir / f"{phase_name}.ndjson"
    stderr_path = out_dir / f"{phase_name}.stderr.log"
    (out_dir / f"{phase_name}.prompt.txt").write_text(prompt)

    env = os.environ.copy()
    env["GIT_CEILING_DIRECTORIES"] = str(out_dir.parent.resolve())
    load_secrets_into_env(env)

    command, stdin_data, temp_home = build_command(model, prompt, project_dir, out_dir, env)

    started_at = utc_now()
    wall_start = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=project_dir.resolve(),
        env=env,
        text=True,
        stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        bufsize=1,
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
    stalled = False
    last_output = time.monotonic()
    sel = selectors.DefaultSelector()
    if process.stdout:
        sel.register(process.stdout, selectors.EVENT_READ)

    try:
        with open(stdout_path, "w") as out_f:
            while True:
                now = time.monotonic()
                if PHASE_TIMEOUT > 0 and now - wall_start > PHASE_TIMEOUT:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGTERM)
                    break
                if harness not in ("zcode", "agy") and now - last_output > STALL_TIMEOUT:
                    stalled = True
                    print(f"[{model['slug']}/{phase_name}] STALL after {int(now - last_output)}s")
                    os.killpg(process.pid, signal.SIGTERM)
                    break
                if terminal_seen is not None and now - terminal_seen > KIMI_TERMINAL_GRACE:
                    os.killpg(process.pid, signal.SIGTERM)
                    break
                if process.poll() is not None:
                    for line in process.stdout or []:
                        out_f.write(line)
                        stdout_lines.append(line)
                    break
                for key, _ in sel.select(timeout=1.0):
                    stream = cast(Any, key.fileobj)
                    line = stream.readline()
                    if not line:
                        continue
                    last_output = time.monotonic()
                    out_f.write(line)
                    out_f.flush()
                    stdout_lines.append(line)
                    if '"session.resume_hint"' in line:
                        terminal_seen = time.monotonic()
    finally:
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        if temp_home is not None:
            shutil.rmtree(temp_home, ignore_errors=True)

    stderr_text = process.stderr.read() if process.stderr else ""
    stderr_path.write_text(stderr_text)

    elapsed = round(time.monotonic() - wall_start, 2)
    stdout_text = "".join(stdout_lines)
    events = parse_event_stream(stdout_text)

    tokens, native_cost, session_id, turns = extract_v5_usage(harness, events, stdout_text, model["slug"])
    cost_breakdown = compute_cost_breakdown(tokens, rates)

    payload = {
        "phase": phase_name,
        "harness": harness,
        "model_id": model["model_id"],
        "started_at": started_at,
        "ended_at": utc_now(),
        "elapsed_seconds": elapsed,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "stall_aborted": stalled,
        "turns": turns,
        "session_id": session_id,
        "tokens": tokens,
        "native_cost_usd": native_cost,
        "cost_breakdown": cost_breakdown,
        "file_count_after": count_files(project_dir),
    }
    save_json(out_dir / f"{phase_name}.result.json", payload)
    print(
        f"[{model['slug']}/{phase_name}] elapsed={elapsed}s exit={process.returncode} "
        f"tok={tokens['total']} hit={tokens['cache_hit_ratio']*100:.1f}% "
        f"cost=${cost_breakdown['actual_cost_usd']:.4f} "
        f"(no-cache=${cost_breakdown['no_cache_cost_usd']:.4f}, saved={cost_breakdown['cache_savings_pct']:.1f}%)"
    )
    return payload


def run_quality_gate(project_dir: Path) -> dict[str, Any]:
    """Quick automated gate to decide if a nudge is needed."""
    checks: dict[str, bool] = {
        "gemfile_present": (project_dir / "Gemfile").is_file(),
        "dockerfile_present": (project_dir / "Dockerfile").is_file(),
        "compose_present": any((project_dir / f).is_file() for f in ("compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml")),
        "tests_pass": False,
        "rubocop_pass": False,
        "brakeman_pass": False,
    }
    if not checks["gemfile_present"]:
        return {"passed": False, "checks": checks}

    def _run(cmd: str, timeout: int = 240) -> bool:
        try:
            p = subprocess.run(
                ["bash", "-lc", f"eval \"$(mise activate bash 2>/dev/null)\" || true; cd {shlex_quote(str(project_dir.resolve()))} && {cmd}"],
                capture_output=True, text=True, timeout=timeout,
            )
            return p.returncode == 0
        except Exception:
            return False

    # If the app uses Redis and nothing is listening on 6379, spin up an ephemeral
    # redis-server solely for the test check so Redis-backed G6 apps don't false-fail.
    redis_proc: subprocess.Popen[str] | None = None
    gemfile_text = (project_dir / "Gemfile").read_text(errors="replace")
    if "redis" in gemfile_text.lower() and shutil.which("redis-server"):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", 6379)) != 0:
                redis_proc = subprocess.Popen(
                    ["redis-server", "--port", "6379", "--save", "", "--appendonly", "no"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True,
                )
                time.sleep(0.5)

    try:
        checks["tests_pass"] = _run("bundle exec rails test")
    finally:
        if redis_proc is not None:
            redis_proc.terminate()
            try:
                redis_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                redis_proc.kill()
    checks["rubocop_pass"] = _run("bundle exec rubocop")
    checks["brakeman_pass"] = _run("bundle exec brakeman --no-pager -q")
    passed = all(checks.values())
    return {"passed": passed, "checks": checks}


def cleanup_project_runtime(project_dir: Path) -> None:
    """Stop any compose stack or stray server spawned inside this model's project dir."""
    compose_files = [f for f in ("compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml") if (project_dir / f).is_file()]
    if compose_files:
        subprocess.run(
            ["docker", "compose", "down", "--remove-orphans"],
            cwd=project_dir, capture_output=True, text=True, timeout=120, check=False,
        )
    # Kill any stray puma/rails processes whose command line references this project_dir
    marker = str(project_dir.resolve())
    subprocess.run(
        ["pkill", "-f", marker],
        capture_output=True, text=True, check=False,
    )


def run_model(
    model: dict[str, Any],
    pricing_entry: dict[str, Any],
    prompts: dict[str, str],
    results_dir: Path,
    max_nudges: int,
    shield: bool,
) -> dict[str, Any]:
    out_dir = results_dir / model["slug"]
    project_dir = out_dir / "project"
    project_dir.mkdir(parents=True, exist_ok=True)

    if not (project_dir / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=project_dir, check=False, capture_output=True, timeout=30)

    rates = pricing_entry.get("rates_per_m") or {}
    phases: list[dict[str, Any]] = []
    nudges_used = 0
    gate: dict[str, Any] = {"passed": False, "checks": {}}

    with anti_cheat_shield(results_dir, model["slug"], enabled=shield):
        for pname in ("phase1", "phase2"):
            res = run_phase(model, rates, pname, prompts[pname], project_dir, out_dir)
            phases.append(res)
            if res["timed_out"] or res["stall_aborted"]:
                break

        gate = run_quality_gate(project_dir)
        while not gate["passed"] and nudges_used < max_nudges:
            nudges_used += 1
            nname = f"nudge{nudges_used}"
            print(f"[{model['slug']}] quality gate failed ({gate['checks']}); running {nname}")
            res = run_phase(model, rates, nname, prompts[nname], project_dir, out_dir)
            phases.append(res)
            gate = run_quality_gate(project_dir)
            if res["timed_out"] or res["stall_aborted"]:
                break

        cleanup_project_runtime(project_dir)

    total_tokens = sum_token_dicts([p["tokens"] for p in phases])
    total_cost = compute_cost_breakdown(total_tokens, rates)
    native_costs = [p["native_cost_usd"] for p in phases if p.get("native_cost_usd") is not None]
    total_native_cost = round(sum(native_costs), 6) if native_costs else None

    alt_costs: dict[str, Any] = {}
    if pricing_entry.get("scheduled_rate_change"):
        alt_costs["post_2026_12_01"] = compute_cost_breakdown(total_tokens, pricing_entry["scheduled_rate_change"])
    if pricing_entry.get("openrouter_rates_per_m"):
        alt_costs["openrouter_rates"] = compute_cost_breakdown(total_tokens, pricing_entry["openrouter_rates_per_m"])

    summary = {
        "slug": model["slug"],
        "label": model["label"],
        "family": model["family"],
        "harness": model["harness"],
        "model_id": model["model_id"],
        "billing": model.get("billing"),
        "nudges_used": nudges_used,
        "quality_gate": gate,
        "elapsed_seconds_total": round(sum(p["elapsed_seconds"] for p in phases), 2),
        "turns_total": sum(int(p.get("turns") or 0) for p in phases),
        "tokens_total": total_tokens,
        "cost_breakdown": total_cost,
        "native_cost_usd_total": total_native_cost,
        "alt_cost_breakdowns": alt_costs,
        "phases": phases,
        "ended_at": utc_now(),
    }
    save_json(out_dir / "result.json", summary)
    print(
        f"[{model['slug']}] COMPLETE gate={'PASS' if gate['passed'] else 'FAIL'} nudges={nudges_used} "
        f"elapsed={summary['elapsed_seconds_total']}s cost=${total_cost['actual_cost_usd']:.4f} "
        f"(no-cache=${total_cost['no_cache_cost_usd']:.4f}, hit={total_tokens['cache_hit_ratio']*100:.1f}%)"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark v5 (Cost, Speed & Prompt Caching)")
    parser.add_argument("--model", action="append", help="Model slug(s) from config/models_v5.json")
    parser.add_argument("--all", action="store_true", help="Run all models in config/models_v5.json")
    parser.add_argument("--config", default=str(REPO_ROOT / "config" / "models_v5.json"))
    parser.add_argument("--pricing", default=str(REPO_ROOT / "config" / "pricing_v5.json"))
    parser.add_argument("--results-dir", default=str(REPO_ROOT / "results-v5"))
    parser.add_argument("--resume", action="store_true", help="Skip models that already have a result.json")
    parser.add_argument("--no-shield", action="store_true", help="Disable anti-cheat shield (debug only)")
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    pricing = json.loads(Path(args.pricing).read_text())["models"]
    prompts = {k: (REPO_ROOT / v).read_text() for k, v in cfg["prompts"].items()}
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    if args.all:
        selected = cfg["models"]
    elif args.model:
        wanted = set(args.model)
        selected = [m for m in cfg["models"] if m["slug"] in wanted]
        missing = wanted - {m["slug"] for m in selected}
        if missing:
            sys.exit(f"Unknown v5 slug(s): {', '.join(sorted(missing))}")
    else:
        sys.exit("Specify --model <slug> or --all")

    for model in selected:
        if args.resume and (results_dir / model["slug"] / "result.json").is_file():
            print(f"[{model['slug']}] already has result.json; skipping (--resume)")
            continue
        run_model(
            model=model,
            pricing_entry=pricing[model["pricing_key"]],
            prompts=prompts,
            results_dir=results_dir,
            max_nudges=int(cfg.get("max_nudges", 2)),
            shield=not args.no_shield,
        )


if __name__ == "__main__":
    main()
