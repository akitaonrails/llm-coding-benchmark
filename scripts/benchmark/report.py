"""Benchmark report generation."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from benchmark.util import format_value, load_json, prompt_sha256, utc_now


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
    lines.append("- `followup-prompt.txt`: second-phase validation prompt for continuations when enabled")
    lines.append("- `followup-opencode-output.ndjson`: raw JSON event stream from the follow-up continuation")
    lines.append("- `followup-opencode-stderr.log`: stderr from the follow-up continuation")
    lines.append("- `session-export.json`: exported opencode session snapshot when available")
    lines.append("- `result.json`: normalized metadata used for this report")
    lines.append("")
    return "\n".join(lines) + "\n"
