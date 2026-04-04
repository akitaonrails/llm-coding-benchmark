#!/usr/bin/env python3
"""Benchmark coding models through opencode."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from benchmark.backends import create_backend
from benchmark.config import (
    BenchmarkConfig,
    load_ollama_warmup_payload,
    load_opencode_ollama_api_base,
    print_local_opencode_config_summary,
    write_local_opencode_config,
)
from benchmark.report import build_report, load_results
from benchmark.runner import run_model
from benchmark.util import load_json, print_line

DEFAULT_NO_PROGRESS_MINUTES = 6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark coding models through opencode.")
    parser.add_argument("--config", default="config/models.json")
    parser.add_argument("--opencode-config", default="config/opencode.benchmark.json")
    parser.add_argument("--prompt", default="prompts/benchmark_prompt.txt")
    parser.add_argument(
        "--followup-prompt",
        default="prompts/benchmark_followup_prompt.txt",
        help="Optional second-phase prompt that continues the same session after the primary prompt completes.",
    )
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
        "--no-followup",
        action="store_true",
        help="Disable the second-phase follow-up prompt.",
    )
    parser.add_argument(
        "--min-preview-output-tps",
        type=float,
        default=10.0,
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
    parser.add_argument(
        "--local-backend",
        choices=["ollama", "llama-swap"],
        default="ollama",
        help="Backend for local model serving (default: ollama).",
    )
    parser.add_argument(
        "--local-api-base",
        default=None,
        help="API base URL for the local backend. Defaults to the Ollama URL from the opencode config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    opencode_config_path = Path(args.opencode_config)
    prompt_path = Path(args.prompt)
    followup_prompt_path = Path(args.followup_prompt)
    results_dir = Path(args.results_dir)
    report_path = Path(args.report)
    warmup_path = Path(args.ollama_warmup_results)

    if shutil.which("opencode") is None:
        print("opencode is not available on PATH", file=sys.stderr)
        return 1

    config = load_json(config_path)
    prompt = prompt_path.read_text().strip()
    followup_prompt = None
    if not args.no_followup and followup_prompt_path.exists():
        followup_prompt = followup_prompt_path.read_text().strip()
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

    # Resolve local backend
    api_base = args.local_api_base or load_opencode_ollama_api_base()
    backend = None
    has_local_models = any(m["provider"] == "ollama" for m in selected_models)
    if has_local_models and api_base:
        backend = create_backend(args.local_backend, api_base)
        print_line(f"Local backend: {backend.backend_name} at {api_base}")

    if not args.report_only:
        config_summary = write_local_opencode_config(opencode_config_path, selected_models, warmup_payload)
        print_local_opencode_config_summary(config_summary)
        opencode_override = opencode_config_path if config_summary.get("path") else None

        bench = BenchmarkConfig(
            runner=config["runner"],
            config_path=config_path,
            results_dir=results_dir,
            opencode_config_path=opencode_override,
            timeout_seconds=args.timeout_minutes * 60,
            no_progress_timeout_seconds=args.no_progress_minutes * 60,
            min_preview_output_tps=args.min_preview_output_tps,
            min_preview_samples=args.min_preview_samples,
            auto_skip_slow_preview=args.auto_skip_slow_preview,
            force=args.force,
            backend=backend,
            selected_models=selected_models,
            prompt=prompt,
            followup_prompt=followup_prompt,
        )

        total_models = len(selected_models)
        print_line(
            f"Benchmark run starting: models={total_models} timeout={bench.timeout_seconds}s "
            f"no_progress_timeout={bench.no_progress_timeout_seconds}s force={bench.force}"
        )
        for index, model in enumerate(selected_models, start=1):
            run_model(model, bench, index, total_models)

    results = load_results(config, results_dir, warmup_payload)
    report_path.write_text(build_report(config, results, prompt, warmup_payload, warmup_path))
    completed = sum(1 for result in results if result["status"] != "not_run")
    print_line(f"Report updated: {report_path}")
    print_line(f"Progress snapshot: completed_or_attempted={completed}/{len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
