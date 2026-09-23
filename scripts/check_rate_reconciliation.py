#!/usr/bin/env python3
"""Guard against unreconciled / copy-pasted cost rates in config/models_v2.json.

Root cause it prevents (2026-09-23): GPT-6 Astra's placeholder rate_per_m
(input 5 / output 30, notes flagged "ESTIMATED … reconcile") was silently
copied onto v2_gpt_6_sol and v2_gpt_6_luna when those were added, so published
costs were overstated ~2.6x (sol) and ~53x (luna). See feedback_recheck_prices.

BLOCKING (exit 1): an entry whose notes self-admit the rate is unreconciled
  (estimated / placeholder / "reconcile" / TODO) WITHOUT a reconciliation marker
  (reconciled / verified / confirmed). This is the exact failure mode that let
  Astra's placeholder ride onto Sol/Luna. Same-vendor tiers legitimately SHARE a
  real price, so a byte-identical rate block alone is NOT blocking — it is printed
  as an ADVISORY for a human to eyeball (esp. across different providers).

Run before any cost analysis / re-ranking, and whenever a model is added.
"""
from __future__ import annotations
import json, sys, re
from collections import defaultdict
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config" / "models_v2.json"
UNRECONCILED = re.compile(r"\b(estimated|placeholder|reconcile|unreconciled|todo)\b", re.I)
RECONCILED = re.compile(r"\b(reconciled|verified|confirmed)\b", re.I)


def provider_of(mid: str) -> str:
    return mid.split("/", 1)[0] if "/" in mid else mid


def main() -> int:
    d = json.loads(CONFIG.read_text())
    models = d["models"] if isinstance(d, dict) else d
    blocking: list[str] = []
    advisory: list[str] = []

    # ADVISORY: identical non-zero rate blocks shared across DIFFERENT providers
    # (same-provider tier sharing is normal and skipped).
    by_rate: dict[str, list[str]] = defaultdict(list)
    for m in models:
        r = m.get("rates_per_m")
        if not r or all((v or 0) == 0 for v in r.values()):
            continue
        by_rate[json.dumps(r, sort_keys=True)].append(m.get("model_id", m.get("slug", "?")))
    for key, ids in by_rate.items():
        uniq = sorted(set(ids))
        if len(uniq) > 1 and len({provider_of(i) for i in uniq}) > 1:
            advisory.append(f"same rate across DIFFERENT providers {uniq}: {key}")

    # BLOCKING: notes admit an unreconciled rate and lack a reconciliation marker.
    for m in models:
        note = m.get("notes", "") or ""
        r = m.get("rates_per_m")
        if not r or all((v or 0) == 0 for v in r.values()):
            continue
        mo = UNRECONCILED.search(note)
        if mo and not RECONCILED.search(note):
            hit = mo.group(0)
            blocking.append(f"{m.get('slug')}: notes flag its rate as '{hit}' with no reconciliation marker — verify vs provider price before using its cost")

    if advisory:
        print("RATE-RECONCILIATION advisory (eyeball, not blocking):")
        for a in advisory:
            print("  ~", a)
    if blocking:
        print("RATE-RECONCILIATION: FAIL")
        for p in blocking:
            print("  -", p)
        print(f"\n{len(blocking)} unreconciled rate(s). Verify against the provider's published price (see feedback_recheck_prices).")
        return 1
    print(f"RATE-RECONCILIATION: OK — {sum(len(v) for v in by_rate.values())} priced entries; no unreconciled-rate notes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
