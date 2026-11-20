#!/usr/bin/env python3
"""Generate Benchmark v5 Cost, Speed & Prompt-Caching reports from results-v5/."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results-v5"
PRICING_PATH = REPO_ROOT / "config" / "pricing_v5.json"
MODELS_PATH = REPO_ROOT / "config" / "models_v5.json"

LEAK_PATTERNS = [
    re.compile(r"CLAUDE\.md", re.IGNORECASE),
    re.compile(r"success_report", re.IGNORECASE),
    re.compile(r"benchmark-audit", re.IGNORECASE),
    re.compile(r"audit_prompt_template", re.IGNORECASE),
    re.compile(r"\.v5_iso_", re.IGNORECASE),
]


def fmt_tok(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def fmt_min(sec: float) -> str:
    return f"{sec / 60:.1f}m"


def scan_for_leaks(slug_dir: Path, slug: str) -> list[str]:
    """Scan phase NDJSON files for any reference to shielded paths or sibling slugs."""
    hits: list[str] = []
    sibling_re = re.compile(r"v5_[a-z0-9_]+")
    for nd in sorted(slug_dir.glob("*.ndjson")):
        txt = nd.read_text(errors="replace")
        for pat in LEAK_PATTERNS:
            if pat.pattern == r"CLAUDE\.md":
                continue  # Harnesses routinely mention CLAUDE.md in system prompts
            if pat.search(txt):
                hits.append(f"{nd.name}:{pat.pattern}")
        for m in set(sibling_re.findall(txt)):
            if m != slug and not slug.startswith(m):
                hits.append(f"{nd.name}:sibling:{m}")
    return hits


def load_v5_results() -> list[dict[str, Any]]:
    models_cfg = json.loads(MODELS_PATH.read_text())["models"]
    order = {m["slug"]: i for i, m in enumerate(models_cfg)}
    rows: list[dict[str, Any]] = []
    for res_file in sorted(RESULTS_DIR.glob("*/result.json")):
        if "." in res_file.parent.name:
            continue
        data = json.loads(res_file.read_text())
        data["leak_scan"] = scan_for_leaks(res_file.parent, data["slug"])
        rows.append(data)
    rows.sort(key=lambda r: (
        0 if (r.get("quality_gate") or {}).get("passed") else 1,
        (r.get("cost_breakdown") or {}).get("actual_cost_usd", 999999),
        order.get(r["slug"], 999),
    ))
    return rows


def build_report(rows: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        "# Benchmark v5 — Cost, Speed & Prompt-Caching Report",
        "",
        f"Models completed: **{len(rows)}** · Task: 14-goal greenfield Rails RubyLLM SPA (2 phases + up to 2 standardized nudges).",
        "All costs are computed from verified November 19, 2026 official first-party rates (`config/pricing_v5.json`) using exact 5-bucket token accounting (`input_uncached`, `cache_read`, `cache_write`, `output`, `reasoning`).",
        "",
        "## 1. Cost × Time × Quality Gate Leaderboard",
        "",
        "| Rank | Model | Family | Harness | Gate | Nudges | Wall | Actual $ | No-Cache $ | Cache Saved | Cache Hit % | Total Tok |",
        "|---:|---|---|---|:---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for i, r in enumerate(rows, 1):
        gate = "PASS" if (r.get("quality_gate") or {}).get("passed") else "FAIL"
        cb = r.get("cost_breakdown") or {}
        tok = r.get("tokens_total") or {}
        actual = cb.get("actual_cost_usd", 0.0)
        nocache = cb.get("no_cache_cost_usd", 0.0)
        saved_pct = cb.get("cache_savings_pct", 0.0)
        hit_pct = (tok.get("cache_hit_ratio") or 0.0) * 100.0
        lines.append(
            f"| {i} | {r['label']} | {r['family']} | `{r['harness']}` | **{gate}** | {r.get('nudges_used', 0)} | "
            f"{fmt_min(r.get('elapsed_seconds_total', 0))} | **${actual:.2f}** | ${nocache:.2f} | "
            f"-{saved_pct:.1f}% | {hit_pct:.1f}% | {fmt_tok(tok.get('total', 0))} |"
        )

    lines += [
        "",
        "## 2. Token & Prompt-Caching Breakdown",
        "",
        "| Model | Uncached In | Cache Read | Cache Write | Out (incl. Reas.) | Reasoning | In $ | Cache Read $ | Cache Write $ | Out $ | Native CLI $ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        tok = r.get("tokens_total") or {}
        comp = (r.get("cost_breakdown") or {}).get("components_usd") or {}
        nat = r.get("native_cost_usd_total")
        nat_s = f"${nat:.2f}" if nat is not None else "—"
        lines.append(
            f"| {r['label']} | {fmt_tok(tok.get('input_uncached', 0))} | {fmt_tok(tok.get('cache_read', 0))} | "
            f"{fmt_tok(tok.get('cache_write', 0))} | {fmt_tok(tok.get('billable_output', 0))} | {fmt_tok(tok.get('reasoning', 0))} | "
            f"${comp.get('input_uncached', 0):.2f} | ${comp.get('cache_read', 0):.2f} | "
            f"${comp.get('cache_write', 0):.2f} | ${comp.get('output', 0):.2f} | {nat_s} |"
        )

    lines += [
        "",
        "## 3. Alternate Rate Views (Post-Dec-1 Gemini 4 Carbon & OpenRouter Rates)",
        "",
        "| Model | Scenario | Actual $ | No-Cache $ | Cache Saved |",
        "|---|---|---:|---:|---:|",
    ]
    for r in rows:
        for name, cb in (r.get("alt_cost_breakdowns") or {}).items():
            lines.append(
                f"| {r['label']} | `{name}` | ${cb['actual_cost_usd']:.2f} | "
                f"${cb['no_cache_cost_usd']:.2f} | -{cb['cache_savings_pct']:.1f}% |"
            )

    lines += [
        "",
        "## 4. Integrity & Quality-Gate Diagnostics",
        "",
        "| Model | Gemfile | Dockerfile | Compose | Tests | RuboCop | Brakeman | Leak Scan |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|---|",
    ]
    for r in rows:
        c = (r.get("quality_gate") or {}).get("checks") or {}
        yn = lambda k: "ok" if c.get(k) else "FAIL"
        leaks = r.get("leak_scan") or []
        leak_s = "CLEAN" if not leaks else f"FLAG ({len(leaks)}): {', '.join(leaks[:3])}"
        lines.append(
            f"| {r['label']} | {yn('gemfile_present')} | {yn('dockerfile_present')} | {yn('compose_present')} | "
            f"{yn('tests_pass')} | {yn('rubocop_pass')} | {yn('brakeman_pass')} | {leak_s} |"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    rows = load_v5_results()
    out = REPO_ROOT / "docs" / "report.v5.md"
    out.write_text(build_report(rows))
    print(f"Wrote {out} ({len(rows)} models)")


if __name__ == "__main__":
    main()
