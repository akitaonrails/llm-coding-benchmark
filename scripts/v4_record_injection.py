#!/usr/bin/env python3
"""Operator helper for v4 release-wave injection gates (grade-only boundaries).

  v4_record_injection.py status                       open gates and where each project is
  v4_record_injection.py where <slug>                 current project path (repo or shield)
  v4_record_injection.py add <slug> <item> <commit>   record a human-planted Casey commit
  v4_record_injection.py add <slug> <item> "N/A: why" record that no target exists

The record lives in results-v4/<slug>/boundaries/human_injections.json, which the
sprint shield hides from the candidate. Recording a newer entry lets the next
wave pass re-run the grade-only reviewer for that gate.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results-v4"
SHIELD_BASE = REPO.parent
GATE_ITEMS = {2: range(1, 4), 3: range(4, 7), 4: range(7, 10), 5: range(10, 15)}
CASEY = "Casey <casey@example.com>"


def model_root(slug: str) -> Path:
    """The model's results dir, wherever the serial sprint shield put it."""
    candidates = [OUT / slug]
    for shield in sorted(SHIELD_BASE.glob(".v4shield_*")):
        candidates.append(shield / "results" / slug)
        if (shield / "current-evidence.json").is_file():
            owner = json.loads((shield / "current-evidence.json").read_text()).get("slug")
            if owner == slug:
                raise SystemExit(f"{slug} is the model in an active sprint; wait for its boundary")
    for root in candidates:
        if (root / "project").is_dir():
            return root
    raise SystemExit(f"no project found for {slug}")


def gate(root: Path) -> dict | None:
    marker = root / "boundaries" / "AWAITING_INJECTION.json"
    return json.loads(marker.read_text()) if marker.is_file() else None


def status() -> int:
    roots = [p for p in OUT.glob("v2_*") if (p / "boundaries").is_dir()]
    for shield in SHIELD_BASE.glob(".v4shield_*"):
        roots += [p for p in (shield / "results").glob("v2_*") if (p / "boundaries").is_dir()]
    found = False
    for root in sorted(roots, key=lambda p: p.name):
        info = gate(root)
        if info:
            found = True
            print(f"{root.name}: after sprint {info['sprint']:02d} needs {info['items']}")
            print(f"  project: {root / 'project'}")
            print(f"  reviewer: {info['reason']}")
    if not found:
        print("no open injection gates")
    return 0


def add(slug: str, item: int, value: str) -> int:
    root = model_root(slug)
    info = gate(root)
    if not info:
        raise SystemExit(f"{slug} has no open injection gate")
    if item not in GATE_ITEMS[info["sprint"]]:
        raise SystemExit(f"item {item} does not belong to the sprint-{info['sprint']:02d} gate "
                         f"({info['items']})")
    if not value.startswith("N/A:"):
        project = root / "project"
        sha = subprocess.run(["git", "-C", str(project), "rev-parse", "--verify",
                              f"{value}^{{commit}}"], capture_output=True, text=True)
        if sha.returncode:
            raise SystemExit(f"{value} is not a commit in {project}")
        value = sha.stdout.strip()
        author = subprocess.run(["git", "-C", str(project), "log", "-1",
                                 "--format=%an <%ae>", value],
                                capture_output=True, text=True).stdout.strip()
        if author != CASEY:
            raise SystemExit(f"{value[:7]} is authored by {author!r}; injections must be by {CASEY}")
    record = root / "boundaries" / "human_injections.json"
    data = json.loads(record.read_text()) if record.is_file() else {}
    data[str(item)] = value
    record.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    missing = [n for n in GATE_ITEMS[info["sprint"]] if str(n) not in data]
    print(f"recorded #{item} for {slug}: {value[:60]}")
    print("gate ready for re-check" if not missing else f"still to record: {missing}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["status"]:
        return status()
    if argv[:1] == ["where"] and len(argv) == 2:
        print(model_root(argv[1]) / "project")
        return 0
    if argv[:1] == ["add"] and len(argv) == 4:
        return add(argv[1], int(argv[2].lstrip("#")), argv[3])
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
