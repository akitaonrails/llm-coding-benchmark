#!/usr/bin/env python3
"""Benchmark Claude Code (not opencode) with different model/subagent combinations.

Measures whether Opus+Sonnet or Opus+Haiku delegation is more cost-effective
than pure Opus for the same Rails chat-app prompt used by the main benchmark.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from benchmark.claude_code_runner import run_variant  # noqa: E402
from benchmark.util import load_json, print_line, save_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Claude Code subagent benchmark")
    parser.add_argument("--config", default=str(REPO_ROOT / "config" / "claude_code_models.json"))
    parser.add_argument("--prompt", default=str(REPO_ROOT / "prompts" / "benchmark_prompt.txt"))
    parser.add_argument("--results-dir", default=str(REPO_ROOT / "results-claude-code"))
    parser.add_argument("--report", default=str(REPO_ROOT / "docs" / "report.claude-code.md"))
    parser.add_argument("--variant", action="append", default=None,
                        help="Run specific variant(s) by slug. Repeatable. Default: all.")
    parser.add_argument("--timeout-minutes", type=int, default=90)
    parser.add_argument("--no-progress-minutes", type=int, default=6)
    parser.add_argument("--force", action="store_true", help="Re-run even if cached result exists")
    parser.add_argument("--report-only", action="store_true", help="Rebuild report without running")
    return parser.parse_args()


def build_report(config: dict, results: list[dict]) -> str:
    lines = [
        "# Claude Code Subagent Benchmark Report",
        "",
        "This benchmark compares three configurations of Claude Code on the same Rails chat-app prompt:",
        "",
        "- `claude_opus_alone` — baseline, pure Opus 4.7 (no subagent delegation)",
        "- `claude_opus_sonnet` — Opus 4.7 main + Sonnet 4.6 coding subagent",
        "- `claude_opus_haiku` — Opus 4.7 main + Haiku 4.5 coding subagent",
        "",
        "Same prompt as the main benchmark (`prompts/benchmark_prompt.txt`). Phase 1 only.",
        "",
        "Runner: `claude -p --output-format stream-json --dangerously-skip-permissions`",
        "",
        "## Summary",
        "",
        "| Variant | Status | Time | Files | Turns | Delegations | Total Cost |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        status = r.get("status", "not_run")
        elapsed = r.get("elapsed_seconds") or 0
        files = r.get("file_count") or 0
        turns = r.get("num_turns") or 0
        delegations = sum((r.get("subagent_invocation_counts") or {}).values())
        cost = r.get("total_cost_usd")
        cost_str = f"${cost:.4f}" if isinstance(cost, (int, float)) else "—"
        lines.append(
            f"| {r['slug']} | {status} | {elapsed:.0f}s | {files} | {turns} | {delegations} | {cost_str} |"
        )

    lines.extend(["", "## Per-Model Token Usage", ""])
    lines.append("Extracted from Claude Code's `modelUsage` field. Cost is computed server-side by the SDK.")
    lines.append("")
    for r in results:
        mu = r.get("model_usage") or {}
        if not mu:
            continue
        lines.append(f"### {r['slug']}")
        lines.append("")
        lines.append("| Model | Input | Output | Cache Read | Cache Create | Cost |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for model, u in mu.items():
            in_t = u.get("inputTokens", 0)
            out_t = u.get("outputTokens", 0)
            cr = u.get("cacheReadInputTokens", 0)
            cc = u.get("cacheCreationInputTokens", 0)
            cost = u.get("costUSD", 0)
            lines.append(f"| {model} | {in_t:,} | {out_t:,} | {cr:,} | {cc:,} | ${cost:.4f} |")
        lines.append("")

    lines.extend(["## Delegation Details", ""])
    for r in results:
        invocations = r.get("subagent_invocations") or []
        if not invocations:
            continue
        lines.append(f"### {r['slug']} ({len(invocations)} delegations)")
        lines.append("")
        for i, inv in enumerate(invocations, 1):
            desc = (inv.get("description") or "").replace("\n", " ")[:200]
            lines.append(f"{i}. `{inv.get('subagent_type')}` — {desc}")
        lines.append("")

    lines.extend([
        "## Comparison vs Opencode Baseline",
        "",
        "The main benchmark runs Opus 4.7 through opencode (different runner, different harness). "
        "Cross-profile comparison is approximate since the tooling overhead and token accounting differ, "
        "but cost-per-run is directly comparable.",
        "",
        "Reference: Opus 4.7 via opencode — ~$1.10/run, 18m, 28 tests (see `docs/success_report.md`).",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    prompt_path = Path(args.prompt)
    results_dir = Path(args.results_dir)
    report_path = Path(args.report)

    if shutil.which("claude") is None:
        print("claude (Claude Code CLI) is not available on PATH", file=sys.stderr)
        return 1

    config = load_json(config_path)
    prompt = prompt_path.read_text().strip()
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    variants = config["variants"]
    if args.variant:
        wanted = set(args.variant)
        variants = [v for v in variants if v["slug"] in wanted]
        missing = wanted - {v["slug"] for v in variants}
        if missing:
            print(f"Unknown variant slug(s): {', '.join(sorted(missing))}", file=sys.stderr)
            return 1

    if not args.report_only:
        timeout_seconds = args.timeout_minutes * 60
        no_progress_timeout_seconds = args.no_progress_minutes * 60
        print_line(f"Claude Code benchmark: {len(variants)} variants, timeout={timeout_seconds}s")
        for v in variants:
            run_variant(
                variant=v,
                prompt=prompt,
                results_dir=results_dir,
                timeout_seconds=timeout_seconds,
                no_progress_timeout_seconds=no_progress_timeout_seconds,
                force=args.force,
            )

    # Load all existing results to build the report (including cached ones not in this run)
    all_results = []
    for v in config["variants"]:
        rp = results_dir / v["slug"] / "result.json"
        if rp.exists():
            try:
                all_results.append(json.loads(rp.read_text()))
            except json.JSONDecodeError:
                continue

    report_path.write_text(build_report(config, all_results))
    print_line(f"Report updated: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
