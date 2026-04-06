"""Warmup probe for llama-swap models.

Loads each model defined in a benchmark models config (default: NVIDIA profile),
preloads it through llama-swap, and reports preflight tok/s. This is the local
equivalent of `warmup_ollama_models.py` for the llama-swap backend.

Unlike the Ollama warmup which probes context sizes via `/api/generate` with
`num_ctx`, llama-swap configures context server-side, so we only verify that
each model loads and produces a response. The benchmark_context_override field
in the models config is honored as documentation but not enforced here.

Usage:
    python scripts/warmup_llama_swap.py \
        --api-base http://localhost:11435 \
        --config config/models.nvidia.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from benchmark.backends import LlamaSwapBackend
from benchmark.util import load_json, print_line, save_json, utc_now


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--api-base",
        default="http://localhost:11435",
        help="llama-swap base URL (no /v1 suffix). Default: localhost:11435",
    )
    p.add_argument(
        "--config",
        default="config/models.nvidia.json",
        help="Models config file to read (default: config/models.nvidia.json)",
    )
    p.add_argument(
        "--output",
        default="results/llama_swap_warmup.json",
        help="Where to write the warmup results JSON",
    )
    p.add_argument(
        "--report",
        default="docs/llama_swap_warmup.md",
        help="Where to write the warmup markdown report",
    )
    p.add_argument(
        "--model",
        action="append",
        default=None,
        help="Limit to specific model slug(s). Can be passed multiple times.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    config = load_json(Path(args.config))
    backend = LlamaSwapBackend(args.api_base)

    if not backend.health_check():
        print_line(f"FATAL: cannot reach llama-swap at {args.api_base}")
        return 2

    available = backend.list_available() or []
    print_line(f"llama-swap reachable at {args.api_base}, {len(available)} models configured server-side")

    selected = config["models"]
    if args.model:
        selected = [m for m in selected if m["slug"] in set(args.model)]
        if not selected:
            print_line("no matching models")
            return 1

    results: list[dict] = []
    for model in selected:
        slug = model["slug"]
        target = model.get("llama_swap_model")
        if not target:
            print_line(f"[{slug}] skip: no llama_swap_model field")
            results.append({
                "slug": slug,
                "status": "skipped",
                "reason": "no llama_swap_model in config",
            })
            continue

        if target not in available:
            print_line(f"[{slug}] skip: {target} not configured on llama-swap server")
            results.append({
                "slug": slug,
                "llama_swap_model": target,
                "status": "skipped",
                "reason": f"{target} not in /v1/models",
            })
            continue

        print_line(f"[{slug}] preloading {target} ...")
        started = time.monotonic()
        ok, message = backend.preload(target)
        elapsed = round(time.monotonic() - started, 2)

        # Try to extract tps from message tail like "(47.6 tok/s)"
        tps = None
        if "tok/s" in message:
            try:
                tps = float(message.rsplit("(", 1)[1].split(" tok/s")[0])
            except (IndexError, ValueError):
                tps = None

        result = {
            "slug": slug,
            "llama_swap_model": target,
            "status": "ok" if ok else "failed",
            "elapsed_seconds": elapsed,
            "preflight_tps": tps,
            "message": message,
            "context_override": model.get("benchmark_context_override"),
        }
        results.append(result)
        marker = "OK" if ok else "FAIL"
        tps_str = f" {tps:.1f} tok/s" if tps else ""
        print_line(f"[{slug}] {marker}{tps_str} elapsed={elapsed:.1f}s — {message}")

        # Unload between models so the next preload starts cold
        backend.unload_all()

    payload = {
        "generated_at": utc_now(),
        "api_base": args.api_base,
        "config_file": str(args.config),
        "results": results,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, payload)
    print_line(f"\nwrote {output_path}")

    # Render a small markdown report
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# llama-swap Warmup Report",
        "",
        f"Generated at: {payload['generated_at']}",
        f"API base: `{args.api_base}`",
        f"Config: `{args.config}`",
        "",
        "| Slug | llama-swap model | Status | Elapsed (s) | Preflight tok/s | Notes |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for r in results:
        tps = f"{r['preflight_tps']:.1f}" if r.get("preflight_tps") is not None else "—"
        elapsed = f"{r.get('elapsed_seconds', 0):.1f}" if r.get("elapsed_seconds") is not None else "—"
        notes = r.get("message", "") or r.get("reason", "")
        notes = notes.replace("|", "\\|")
        lines.append(
            f"| {r['slug']} | {r.get('llama_swap_model', '—')} | {r['status']} | {elapsed} | {tps} | {notes} |"
        )
    report_path.write_text("\n".join(lines) + "\n")
    print_line(f"wrote {report_path}")

    failures = sum(1 for r in results if r["status"] == "failed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
