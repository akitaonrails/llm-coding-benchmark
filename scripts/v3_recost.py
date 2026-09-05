#!/usr/bin/env python3
"""Re-derive cost for existing codex/kimi v3 runs from their raw streams, using the
fixed cache-aware token extractor + the model's rate card. Claude/opencode costs are
authoritative (harness-reported) and left untouched. No model spend.

Usage: v3_recost.py [--results results-v3] [--config config/models_v2.json]
"""
from __future__ import annotations
import argparse, glob, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from benchmark.runner import extract_codex_metrics  # noqa: E402

RATE_DERIVED = {"codex", "kimi"}


def cost_from_tokens(tokens: dict, rates: dict) -> float:
    cache = tokens.get("cache") or {}
    return round(
        (tokens.get("input", 0) or 0) / 1e6 * rates.get("input", 0)
        + ((tokens.get("output", 0) or 0) + (tokens.get("reasoning", 0) or 0)) / 1e6 * rates.get("output", 0)
        + (cache.get("read", 0) or 0) / 1e6 * rates.get("cache_read", 0)
        + (cache.get("write", 0) or 0) / 1e6 * rates.get("cache_write", 0),
        4,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results-v3")
    ap.add_argument("--config", default=str(REPO / "config" / "models_v2.json"))
    a = ap.parse_args()
    models = {m["slug"]: m for m in json.loads(Path(a.config).read_text())["models"]}

    for pr in sorted(glob.glob(f"{a.results}/*/*/*.result.json")):
        d = json.loads(Path(pr).read_text())
        harness = d.get("harness")
        if harness not in RATE_DERIVED:
            continue
        slug = Path(pr).parents[1].name
        rates = (models.get(slug) or {}).get("rates_per_m") or {}
        nd = Path(pr).with_suffix("").with_suffix(".ndjson")  # <task>.ndjson
        if not nd.exists() or not rates:
            continue
        events = []
        for line in nd.read_text().splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        if harness == "codex":
            m = extract_codex_metrics(events)
        else:
            continue
        tokens = m["tokens"]
        old = d.get("cost_usd")
        new = cost_from_tokens(tokens, rates)
        d["tokens"] = tokens
        d["cost_usd"] = new
        Path(pr).write_text(json.dumps(d, indent=2))
        print(f"  {slug:22} {Path(pr).parents[0].name:24} ${old} -> ${new}  "
              f"(cache_read={tokens['cache']['read']}, reasoning={tokens.get('reasoning')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
