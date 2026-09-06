#!/usr/bin/env python3
"""Run ONE v4 sprint for a model in its ACCUMULATING, isolated, git-sandboxed workspace.

Unlike run_v3 (which wiped project/ per task), v4 preserves and grows results-v4/<slug>/
project across sprints — the model builds on its own prior work. Between sprints, sabotage
is injected into that same project (separate tooling, per PROTOCOL.md).

Shields the v4 ANSWER artifacts (golden reference, INJECTION_PLAN, SABOTAGE_CATALOG,
PROTOCOL) + the v2/v3 grading key + sibling results, and git-sandboxes the project so the
model can't read the benchmark repo history. Captures cost/time/tokens per sprint.

Usage: run_v4_sprint.py --model <slug> --sprint <NN_name> [--config config/models_v2.json]
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
PROMPTS = REPO / "benchmark-v4" / "prompts"
OUT = REPO / "results-v4"

# answer artifacts + grading key the model must never see. Shield the WHOLE benchmark-v4
# dir (golden reference, injection plan, sabotage catalog, protocol, grading rubric/recipes)
# — the prompt is already read into memory before shield() runs, so the model never needs
# filesystem access to benchmark-v4.
SHIELD = [
    "benchmark-v4",
    "docs", ".agents/skills/benchmark-audit", "CLAUDE.md",
]


def shield(out_root: Path) -> Path:
    sh = Path.home() / ".cache" / f".v4shield_{uuid.uuid4().hex[:8]}"
    (sh / "misc").mkdir(parents=True)
    (sh / "results").mkdir(parents=True)
    for rel in SHIELD:
        src = REPO / rel
        if src.exists():
            dst = sh / "misc" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    # other models' v4 outputs
    if out_root.parent.exists():
        for d in out_root.parent.iterdir():
            if d.is_dir() and d.resolve() != out_root.resolve():
                shutil.move(str(d), str(sh / "results" / d.name))
    # verify clean
    leaks = [rel for rel in SHIELD if (REPO / rel).exists()]
    if leaks:
        raise RuntimeError(f"shield incomplete: {leaks}")
    return sh


def unshield(sh: Path) -> None:
    for rel in SHIELD:
        src = sh / "misc" / rel
        if src.exists():
            (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(REPO / rel))
    res = sh / "results"
    if res.exists():
        for d in res.iterdir():
            shutil.move(str(d), str(OUT / d.name))
    shutil.rmtree(sh, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--sprint", required=True, help="prompt basename, e.g. 01_foundation")
    ap.add_argument("--config", default=str(REPO / "config" / "models_v2.json"))
    a = ap.parse_args()

    prompt_file = PROMPTS / f"sprint{a.sprint}.txt"
    if not prompt_file.exists():
        # allow passing the full name
        cand = list(PROMPTS.glob(f"sprint{a.sprint}*.txt")) or list(PROMPTS.glob(f"*{a.sprint}*.txt"))
        if not cand:
            ap.error(f"no prompt for sprint {a.sprint}")
        prompt_file = cand[0]
    prompt = prompt_file.read_text()

    models = json.loads(Path(a.config).read_text())["models"]
    model = next((m for m in models if m["slug"] == a.model), None)
    if not model:
        ap.error(f"model {a.model} not in {a.config}")

    from run_benchmark_v2 import run_phase
    out_root = OUT / model["slug"]
    proj = out_root / "project"
    sprint_tag = prompt_file.stem  # sprintNN_name
    out_dir = out_root / "sprints" / sprint_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    first = not proj.exists()
    if first:
        proj.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=proj)
        subprocess.run(["git", "config", "user.email", "sprinter@example.com"], cwd=proj)
        subprocess.run(["git", "config", "user.name", "Sprinter"], cwd=proj)

    sh = shield(out_root)
    try:
        rec = run_phase(model, sprint_tag, prompt, proj, out_dir)
    finally:
        unshield(sh)

    # record git log for commit-hygiene dimension
    log = subprocess.run(["git", "log", "--oneline", "--stat", "-n", "40"],
                         cwd=proj, capture_output=True, text=True).stdout
    (out_dir / "gitlog.txt").write_text(log)
    summary = {
        "slug": model["slug"], "sprint": sprint_tag, "harness": model["harness"],
        "elapsed_seconds": rec.get("elapsed_seconds"), "cost_usd": rec.get("cost_usd"),
        "tokens_total": (rec.get("tokens") or {}).get("total"),
        "exit_code": rec.get("exit_code"), "stall_aborted": rec.get("stall_aborted"),
    }
    (out_dir / "sprint.result.json").write_text(json.dumps(summary, indent=2))
    print(f"[{model['slug']}] sprint {sprint_tag} done "
          f"elapsed={summary['elapsed_seconds']}s cost=${summary['cost_usd']} exit={summary['exit_code']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
