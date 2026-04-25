#!/usr/bin/env python3
"""
Wrapper to dispatch one subtask to opencode, capture full output, log token usage.

Usage:
  manual_dispatch.py <variant_dir> <executor_model> <subtask_label> <prompt_file>

variant_dir: e.g. results/manual_opus_qwen36plus
executor_model: e.g. openrouter/qwen/qwen3.6-plus:free
subtask_label: short slug for the dispatch (e.g. 1_skeleton, 2_gems, 3_service)
prompt_file: path to a file containing the full prompt

Writes to:
  <variant_dir>/dispatches/<NN>_<label>.json — full opencode JSON output
  <variant_dir>/dispatches/<NN>_<label>.prompt.txt — the prompt sent
  <variant_dir>/orchestration_log.jsonl — appended one-line summary
  <variant_dir>/orchestration_trace.md — human-readable summary appended
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def approx_tokens(s: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters."""
    return max(1, len(s) // 4)


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(__doc__, file=sys.stderr)
        return 2
    variant_dir = Path(argv[1])
    executor_model = argv[2]
    subtask_label = argv[3]
    prompt_path = Path(argv[4])
    if not prompt_path.exists():
        print(f"prompt file not found: {prompt_path}", file=sys.stderr)
        return 2

    project_dir = variant_dir / "project"
    dispatches_dir = variant_dir / "dispatches"
    dispatches_dir.mkdir(parents=True, exist_ok=True)
    log_path = variant_dir / "orchestration_log.jsonl"
    trace_path = variant_dir / "orchestration_trace.md"

    # Determine dispatch number
    existing = sorted(dispatches_dir.glob("*.json"))
    n = len(existing) + 1
    out_json = dispatches_dir / f"{n:02d}_{subtask_label}.json"
    out_prompt = dispatches_dir / f"{n:02d}_{subtask_label}.prompt.txt"

    prompt_text = prompt_path.read_text()
    out_prompt.write_text(prompt_text)

    opencode_config = Path("config/opencode.benchmark.json").resolve()
    env = {**os.environ, "OPENCODE_CONFIG": str(opencode_config)}

    print(f"[dispatch {n:02d}] subtask={subtask_label} model={executor_model}")
    print(f"  project_dir={project_dir}")
    print(f"  prompt_chars={len(prompt_text)}")

    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    cmd = [
        "opencode", "run",
        "--agent", "build",
        "--format", "json",
        "-m", executor_model,
        prompt_text,
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min hard cap per dispatch
        )
    except subprocess.TimeoutExpired as e:
        elapsed = time.monotonic() - t0
        with log_path.open("a") as f:
            f.write(json.dumps({
                "n": n, "subtask": subtask_label, "model": executor_model,
                "status": "timeout", "elapsed_s": elapsed,
                "started_at": started_at,
                "stdout_partial": (e.stdout or b"").decode("utf-8", "replace")[-2000:] if e.stdout else "",
            }) + "\n")
        print(f"  TIMEOUT after {elapsed:.0f}s")
        return 3
    elapsed = time.monotonic() - t0
    out_json.write_text(result.stdout)

    # Parse opencode JSON output to extract tokens/cost
    tokens_in = tokens_out = tokens_cache_w = tokens_cache_r = 0
    cost = 0.0
    finish_reason = "unknown"
    assistant_excerpt = ""
    try:
        # opencode --format json may output a single JSON or an ndjson stream
        out = result.stdout.strip()
        if out.startswith("["):
            events = json.loads(out)
        elif out.startswith("{"):
            # Single JSON
            try:
                events = [json.loads(out)]
            except json.JSONDecodeError:
                events = [json.loads(line) for line in out.splitlines() if line.strip()]
        else:
            events = [json.loads(line) for line in out.splitlines() if line.strip()]
        for ev in events:
            if not isinstance(ev, dict): continue
            t = ev.get("type", "")
            part = ev.get("part", {}) or {}
            if t == "step_finish":
                tk = part.get("tokens", {}) or {}
                tokens_in += tk.get("input", 0) or 0
                tokens_out += (tk.get("output", 0) or 0) + (tk.get("reasoning", 0) or 0)
                cache = tk.get("cache", {}) or {}
                tokens_cache_w += cache.get("write", 0) or 0
                tokens_cache_r += cache.get("read", 0) or 0
                cost += part.get("cost", 0) or 0
                finish_reason = part.get("reason", finish_reason)
            elif t == "text":
                txt = part.get("text", "")
                if txt and txt.strip():
                    assistant_excerpt = txt[:1000]
    except Exception as e:
        print(f"  WARNING: could not parse opencode JSON: {e}", file=sys.stderr)

    summary = {
        "n": n,
        "subtask": subtask_label,
        "model": executor_model,
        "status": "ok" if result.returncode == 0 else "error",
        "exit_code": result.returncode,
        "started_at": started_at,
        "elapsed_s": round(elapsed, 1),
        "prompt_chars": len(prompt_text),
        "approx_planner_prompt_tokens": approx_tokens(prompt_text),
        "stdout_chars": len(result.stdout),
        "approx_planner_response_tokens": approx_tokens(result.stdout),
        "executor_tokens": {
            "input": tokens_in,
            "output": tokens_out,
            "cache_write": tokens_cache_w,
            "cache_read": tokens_cache_r,
            "total": tokens_in + tokens_out + tokens_cache_w + tokens_cache_r,
        },
        "executor_cost_usd": round(cost, 4),
        "finish_reason": finish_reason,
        "assistant_excerpt": assistant_excerpt[:500],
    }
    with log_path.open("a") as f:
        f.write(json.dumps(summary) + "\n")

    # Append human-readable line to trace
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    if not trace_path.exists():
        trace_path.write_text(f"# Orchestration trace: {variant_dir.name}\n\n")
    with trace_path.open("a") as f:
        f.write(f"## Dispatch {n:02d} — {subtask_label}\n\n")
        f.write(f"- Model: `{executor_model}`\n")
        f.write(f"- Status: **{summary['status']}** (exit {result.returncode}, finish={finish_reason})\n")
        f.write(f"- Elapsed: {elapsed:.0f}s\n")
        f.write(f"- Prompt: {len(prompt_text)} chars (~{approx_tokens(prompt_text)} planner tokens)\n")
        f.write(f"- Executor tokens: in={tokens_in:,}, out={tokens_out:,}, cache_w={tokens_cache_w:,}, cache_r={tokens_cache_r:,}, cost=${cost:.4f}\n")
        f.write(f"- Stdout/JSON output: `{out_json.name}` ({len(result.stdout):,} chars)\n")
        if assistant_excerpt:
            excerpt_short = assistant_excerpt[:300].replace('\n', ' ')
            f.write(f"- Assistant excerpt: {excerpt_short}{'...' if len(assistant_excerpt) > 300 else ''}\n")
        if result.stderr.strip():
            f.write(f"- Stderr (first 500 chars): `{result.stderr[:500]}`\n")
        f.write("\n")

    print(f"  status={summary['status']} elapsed={elapsed:.0f}s")
    print(f"  executor_tokens: in={tokens_in:,} out={tokens_out:,} cache_w={tokens_cache_w:,} cache_r={tokens_cache_r:,} cost=${cost:.4f}")
    print(f"  log: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
