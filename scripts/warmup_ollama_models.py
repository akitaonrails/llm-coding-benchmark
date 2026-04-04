#!/usr/bin/env python3
"""Probe Ollama models at candidate context sizes to find the highest working context."""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from benchmark.backends import OllamaBackend, _get_json, _post_json, _api_url
from benchmark.util import load_json, load_optional_json, print_line, save_json, utc_now


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "models.json"
OUTPUT_JSON = ROOT / "results" / "ollama_warmup.json"
OUTPUT_MD = ROOT / "docs" / "ollama_warmup.md"
KNOWN_RESULTS_PATH = ROOT / "config" / "warmup_known.json"
OPENCODE_CONFIG_PATH = Path.home() / ".config" / "opencode" / "opencode.json"
MIN_USEFUL_CONTEXT = 32768
MAX_PRACTICAL_CONTEXT = 262144
PER_ATTEMPT_TIMEOUT = 180.0


def load_existing_results() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    # Load known results from config file if present
    known = load_optional_json(KNOWN_RESULTS_PATH)
    if isinstance(known, dict):
        for slug, value in known.items():
            if isinstance(value, dict):
                results[slug] = dict(value)
    # Merge with previously saved warmup output
    if OUTPUT_JSON.exists():
        payload = load_json(OUTPUT_JSON)
        for result in payload.get("results", []):
            slug = result.get("slug")
            if isinstance(slug, str) and slug:
                results[slug] = result
    return results


def persist_results(results_by_slug: dict[str, dict[str, Any]]) -> None:
    ordered_results = [results_by_slug[slug] for slug in sorted(results_by_slug)]
    payload = {
        "generated_at": utc_now(),
        "minimum_useful_context": MIN_USEFUL_CONTEXT,
        "results": ordered_results,
    }
    save_json(OUTPUT_JSON, payload)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(build_report(ordered_results))


def try_context(api_base: str, model_name: str, num_ctx: int) -> dict[str, Any]:
    payload = {
        "model": model_name,
        "prompt": "ping",
        "stream": False,
        "keep_alive": 0,
        "options": {
            "num_ctx": num_ctx,
            "num_predict": 32,
        },
    }
    started = time.monotonic()
    response = _post_json(
        _api_url(api_base, "/api/generate"),
        payload,
        timeout=PER_ATTEMPT_TIMEOUT,
    )
    elapsed = round(time.monotonic() - started, 2)
    if response is None:
        return {
            "num_ctx": num_ctx,
            "ok": False,
            "elapsed_seconds": elapsed,
            "error": "no response from ollama",
        }
    if response.get("error"):
        return {
            "num_ctx": num_ctx,
            "ok": False,
            "elapsed_seconds": elapsed,
            "error": str(response["error"]),
        }
    return {
        "num_ctx": num_ctx,
        "ok": bool(response.get("done") is True),
        "elapsed_seconds": elapsed,
        "response_excerpt": str(response.get("response", ""))[:200],
        "load_duration_ns": response.get("load_duration"),
        "total_duration_ns": response.get("total_duration"),
        "prompt_eval_count": response.get("prompt_eval_count"),
        "eval_count": response.get("eval_count"),
    }


def candidate_contexts(configured_context: int) -> list[int]:
    capped = configured_context or MIN_USEFUL_CONTEXT
    capped = min(capped, MAX_PRACTICAL_CONTEXT)
    candidates = [capped, 131072, 65536, 32768]
    ordered: list[int] = []
    for value in candidates:
        if value < MIN_USEFUL_CONTEXT:
            continue
        if value > capped:
            continue
        if value not in ordered:
            ordered.append(value)
    return ordered


def fallback_ollama_entry(model: dict[str, Any]) -> dict[str, Any] | None:
    model_name = model.get("ollama_model_name")
    if not isinstance(model_name, str) or not model_name:
        return None
    context = model.get("ollama_limit_context")
    output = model.get("ollama_limit_output")
    entry: dict[str, Any] = {
        "id": model_name,
        "name": f"{model['label']} (Ollama)",
        "limit": {},
    }
    if isinstance(context, int) and context > 0:
        entry["limit"]["context"] = context
    if isinstance(output, int) and output > 0:
        entry["limit"]["output"] = output
    if model.get("ollama_tool_call") is True:
        entry["tool_call"] = True
    if model.get("ollama_reasoning") is True:
        entry["reasoning"] = True
    return entry


def load_opencode_ollama(api_base_override: str | None) -> tuple[str, dict[str, Any]]:
    payload = load_json(OPENCODE_CONFIG_PATH)
    base_url = payload["provider"]["ollama"]["options"]["baseURL"]
    api_base = base_url[:-3] if base_url.endswith("/v1") else base_url
    if api_base_override:
        api_base = api_base_override
    models = payload["provider"]["ollama"]["models"]
    return api_base, models


def build_report(results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# Ollama Warmup Report")
    lines.append("")
    lines.append(f"Generated at: {utc_now()}")
    lines.append(f"Minimum useful context target: `{MIN_USEFUL_CONTEXT}`")
    lines.append(f"Maximum practical context tested: `{MAX_PRACTICAL_CONTEXT}`")
    lines.append(f"Per-attempt timeout: `{int(PER_ATTEMPT_TIMEOUT)}` seconds")
    lines.append("")
    lines.append("| Model | Ollama name | Config ctx | Highest verified ctx | Recommendation |")
    lines.append("| --- | --- | ---: | ---: | --- |")
    for result in results:
        recommendation = result["recommendation"]
        highest = result.get("highest_verified_context")
        lines.append(
            f"| {result['slug']} | `{result['ollama_model']}` | {result['configured_context']} | "
            f"{highest if highest is not None else '-'} | {recommendation} |"
        )
    lines.append("")
    lines.append("## Attempt Log")
    lines.append("")
    for result in results:
        lines.append(f"### {result['slug']}")
        lines.append("")
        for attempt in result["attempts"]:
            if attempt["ok"]:
                detail = f"ok in {attempt['elapsed_seconds']:.2f}s"
            else:
                detail = f"fail: {attempt.get('error', 'unknown')}"
            lines.append(f"- `num_ctx={attempt['num_ctx']}`: {detail}")
        lines.append("")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Warm up Ollama models and probe context sizes.")
    parser.add_argument(
        "--api-base",
        default=None,
        help="Ollama API base URL. Defaults to the URL from the opencode config.",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help="Path to models.json config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark_config = load_json(Path(args.config))
    api_base, opencode_models = load_opencode_ollama(args.api_base)
    ollama_models = [model for model in benchmark_config["models"] if model["provider"] == "ollama"]
    results_by_slug = load_existing_results()
    backend = OllamaBackend(api_base)

    for index, model in enumerate(ollama_models, start=1):
        existing = results_by_slug.get(model["slug"])
        if existing and existing.get("highest_verified_context", 0) >= MIN_USEFUL_CONTEXT:
            print_line("")
            print_line(
                f"[{index}/{len(ollama_models)}] skipping {model['slug']} already verified at {existing['highest_verified_context']}"
            )
            continue
        normalized_id = model["id"].split("/", 1)[1]
        opencode_entry = opencode_models.get(normalized_id) or fallback_ollama_entry(model)
        if not isinstance(opencode_entry, dict):
            print_line("")
            print_line(f"[{index}/{len(ollama_models)}] skipping {model['slug']} missing ollama mapping")
            continue
        ollama_model = opencode_entry["id"]
        configured_context = int(opencode_entry.get("limit", {}).get("context", 0))
        attempts: list[dict[str, Any]] = []

        print_line("")
        print_line(f"[{index}/{len(ollama_models)}] warming {model['slug']} -> {ollama_model}")
        backend.unload_all()

        contexts_to_try = candidate_contexts(configured_context)

        for num_ctx in contexts_to_try:
            print_line(f"[{model['slug']}] trying num_ctx={num_ctx}")
            attempt = try_context(api_base, ollama_model, num_ctx)
            attempts.append(attempt)
            if attempt["ok"]:
                print_line(f"[{model['slug']}] ok num_ctx={num_ctx} elapsed={attempt['elapsed_seconds']:.2f}s")
                break
            else:
                print_line(f"[{model['slug']}] fail num_ctx={num_ctx}: {attempt.get('error', 'unknown')}")

        successful_contexts = [attempt["num_ctx"] for attempt in attempts if attempt["ok"]]
        highest_verified_context = max(successful_contexts) if successful_contexts else None
        if any(ctx >= MIN_USEFUL_CONTEXT for ctx in successful_contexts):
            recommendation = f"keep in benchmark at {highest_verified_context}"
        else:
            recommendation = "remove from benchmark; no verified context >= 32768"

        results_by_slug[model["slug"]] = {
            "slug": model["slug"],
            "label": model["label"],
            "ollama_model": ollama_model,
            "configured_context": configured_context,
            "attempts": attempts,
            "highest_verified_context": highest_verified_context,
            "recommendation": recommendation,
        }
        persist_results(results_by_slug)

    persist_results(results_by_slug)
    print_line("")
    print_line(f"Wrote {OUTPUT_JSON}")
    print_line(f"Wrote {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
