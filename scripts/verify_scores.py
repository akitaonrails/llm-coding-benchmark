#!/usr/bin/env python3
"""Score-consistency verifier for docs/success_report.v2.md.

Run this AFTER adding or re-scoring any model, and BEFORE declaring a wave done.
It catches the exact slippage classes that bit us on 2026-07-30:
  1. a dimension breakdown that does not sum to the stated total
  2. an explicit "Total NN" that disagrees with the section header
  3. a FINAL STANDINGS row whose score no section supports
  4. rank numbers that don't follow score order / tie rules
  5. isolation or wave-4 A/B rows whose (baseline -> result) != stated delta

Exit code 0 = consistent; 1 = at least one real inconsistency (printed).
False-positive guard: a model may legitimately appear in several sections
(orchestrator / clean / native-CLI). Check 3 passes if ANY section matches the
standings score, so multi-condition models don't trip it.

Usage: python scripts/verify_scores.py [path-to-report]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DIM_PATTERNS = [
    ("gates", r"gates\s+(\d+)"),
    ("streaming", r"streaming\s+(\d+)"),
    ("payload", r"payload\s+(\d+)"),
    ("concurrency", r"concurrency\s+(\d+)"),
    ("tools", r"tools\s+(\d+)"),
    ("schema", r"schema\s+(\d+)"),
    ("budget", r"budget\s+(\d+)"),
    ("robustness", r"robustness\s+(\d+)"),
    ("tests", r"tests\+?gates?\s+(\d+)"),
    ("fidelity", r"fidelity\s+(\d+)"),
]


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/success_report.v2.md")
    s = path.read_text()
    problems: list[str] = []

    # ---- section arithmetic (checks 1 + 2) ----
    section_scores: dict[str, list[int]] = {}
    for sec in re.split(r"\n### ", s):
        m = re.match(r"([^\n—]+?)—\s*(\d+)", sec)
        if not m:
            continue
        name, total = m.group(1).strip(), int(m.group(2))
        section_scores.setdefault(norm(name.split("(")[0]), []).append(total)
        scoring = re.search(r"\*\*Scoring[^*]*\*\*:?(.*?)(?:\*\*Total|\n\n|\Z)", sec, re.S)
        if not scoring:
            continue
        text = scoring.group(1).replace("**", "")
        dims = {k: int(mm.group(1)) for k, pat in DIM_PATTERNS
                if (mm := re.search(pat, text))}
        if len(dims) == 10 and sum(dims.values()) != total:
            problems.append(f"[arith] {name}: dims sum {sum(dims.values())} != header {total}")
        tm = re.search(r"\*\*Total\s+(\d+)", sec)
        if tm and int(tm.group(1)) != total:
            problems.append(f"[arith] {name}: explicit Total {tm.group(1)} != header {total}")

    # ---- FINAL STANDINGS vs supporting evidence + ordering (checks 3 + 4) ----
    # Evidence = the score appears anywhere the model is named: a ### section
    # header, the Wave-1 results table, or an isolation/wave-4 A/B table row.
    # (Not every official score has a prose ### section — wave-1 breakdowns and
    # the clean-isolation re-run scores are documented in tables.)
    tbl = re.search(r"## FINAL v2 STANDINGS.*?\n\n(\|.*?)\n\n", s, re.S)
    standings_block = tbl.group(1) if tbl else ""
    rows = []
    for line in standings_block.splitlines():
        # columns: rank | model | score | tier | harness | v1 | move
        m = re.match(r"\|\s*(\d+)\s*\|\s*\*{0,2}([^|*]+?)\*{0,2}\s*\|\s*\*{0,2}(\d+)[^|]*\|\s*([ABCD])?\s*\|", line)
        if m:
            rows.append((int(m.group(1)), m.group(2).strip(), int(m.group(3)), m.group(4)))
    scores = [r[2] for r in rows]

    # ---- tier column matches the score thresholds (A>=83, B 73-82, C 51-72, D<=50) ----
    def tier_for(sc: int) -> str:
        return "A" if sc >= 83 else "B" if sc >= 73 else "C" if sc >= 51 else "D"
    for rank, name, score, tier in rows:
        if tier and tier != tier_for(score):
            problems.append(f"[tier] {name} score {score} labeled Tier {tier}, threshold says {tier_for(score)}")
    body_outside_standings = s.replace(standings_block, "")
    for rank, name, score, _tier in rows:
        key = norm(name)
        in_section = any((key in sk or sk in key) and score in vals
                         for sk, vals in section_scores.items())
        # fallback: the model name and this score co-occur on some other line
        in_table = any(
            key in norm(line) and re.search(rf"\b{score}\b", line)
            for line in body_outside_standings.splitlines()
        )
        if not (in_section or in_table):
            problems.append(f"[table] rank {rank} {name} = {score}: no section OR table supports this score")
        correct = 1 + sum(1 for sc in scores if sc > score)
        if rank != correct:
            problems.append(f"[rank] {name} labeled rank {rank}, should be {correct} (score {score})")
    for a, b in zip(rows, rows[1:]):
        if b[2] > a[2]:
            problems.append(f"[order] {b[1]} ({b[2]}) ranked below {a[1]} ({a[2]})")

    # ---- A/B delta arithmetic (check 5) ----
    for line in s.splitlines():
        m = re.match(
            r"\|\s*\*{0,2}([^|(*]+?)\*{0,2}\s*\([^)]*\)\s*\|\s*(\d+)[^|]*\|\s*\*{0,2}(\d+)"
            r"[^|]*\*{0,2}[^|]*\|\s*([+\-−]?\d+)\s*\|",
            line,
        )
        if not m:
            continue
        name, base, res, delta = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4)
        d = int(delta.replace("−", "-"))
        if res - base != d:
            problems.append(f"[delta] {name}: {base}->{res} but Δ stated {delta} (should be {res-base:+d})")

    if problems:
        print(f"SCORE VERIFIER: {len(problems)} inconsistency(ies) found\n")
        for p in problems:
            print(" ", p)
        return 1
    print(f"SCORE VERIFIER: consistent — {len(rows)} standings rows, "
          f"{len(section_scores)} model sections, all arithmetic/ordering/deltas OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
