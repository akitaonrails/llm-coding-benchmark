#!/usr/bin/env python3
"""Run ONE v4.1 P1 (Raft) sprint for a model in its accumulating, isolated, git-sandboxed workspace.

Mirrors run_v4_sprint.py's shield/isolation discipline, adapted for v4.1:
- seeds the Go scaffold (harness minus porcupine + go.mod + CONTRACT) on the first sprint;
- shields the v4.1 answer key (benchmark-v4.1 grader/reference), docs, CLAUDE.md, .agents, and sibling
  results-v4.1 projects, so the model cannot read the hidden grader or peers;
- runs the sprint via the shared run_phase (opencode/codex/etc), then snapshot-commits if the model didn't.
NO sabotage injection (v4.1 is a pure accumulating build graded by the objective Go gauntlet).

Usage: run_v41_sprint.py --model <slug> --sprint 01_election [--config config/models_v2.json]
"""
from __future__ import annotations
import argparse, signal, subprocess, sys, uuid, shutil, json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
PROMPTS = REPO / "benchmark-v4.1" / "raft" / "prompts"
RAFT = REPO / "benchmark-v4.1" / "raft"
OUT = REPO / "results-v4.1"
SHIELD_BASE = REPO.parent
# Answer key + grading key the model must never see. benchmark-v4.1 holds grader/ + reference/.
SHIELD = ["benchmark-v4.1", "benchmark-v4", "docs", ".agents/skills/benchmark-audit", "CLAUDE.md"]


def shield(out_root: Path) -> Path:
    sh = SHIELD_BASE / f".v41shield_{uuid.uuid4().hex[:8]}"
    (sh / "misc").mkdir(parents=True)
    (sh / "results").mkdir(parents=True)
    for rel in SHIELD:
        src = REPO / rel
        if src.exists():
            dst = sh / "misc" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    if out_root.parent.exists():
        for d in out_root.parent.iterdir():
            if d.is_dir() and d.resolve() != out_root.resolve():
                shutil.move(str(d), str(sh / "results" / d.name))
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


def restore_stranded() -> None:
    for sh in sorted(SHIELD_BASE.glob(".v41shield_*")):
        if not sh.is_dir():
            continue
        try:
            n = subprocess.run(["pgrep", "-fc", "run_v41_sprint.py"], capture_output=True, text=True).stdout.strip()
            if n and int(n) > 1:
                print(f"[shield-recover] another run active — skipping {sh.name}"); continue
        except Exception:
            pass
        ok = True
        for rel in SHIELD:
            src = sh / "misc" / rel
            if src.exists():
                if (REPO / rel).exists():
                    ok = False
                else:
                    (REPO / rel).parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src), str(REPO / rel))
        res = sh / "results"
        if res.exists():
            for d in res.iterdir():
                if (OUT / d.name).exists(): ok = False
                else: OUT.mkdir(parents=True, exist_ok=True); shutil.move(str(d), str(OUT / d.name))
        if ok:
            shutil.rmtree(sh, ignore_errors=True); print(f"[shield-recover] restored {sh.name}")
        else:
            print(f"[shield-recover] LEFT IN PLACE (conflicts): {sh.name}")


def seed_project(project: Path) -> None:
    """Copy the provided scaffold into a fresh project: harness (minus porcupine) + go.mod + CONTRACT."""
    shutil.copy2(RAFT / "go.mod", project / "go.mod")
    shutil.copy2(RAFT / "CONTRACT.md", project / "CONTRACT.md")
    hdst = project / "harness"
    hdst.mkdir(parents=True, exist_ok=True)
    for item in (RAFT / "harness").iterdir():
        if item.name == "porcupine":      # grader-only; never seed it
            continue
        if item.is_dir():
            shutil.copytree(item, hdst / item.name)
        else:
            shutil.copy2(item, hdst / item.name)
    # placeholder package dirs the model will fill (keep empty, tracked)
    for pkg in ("raft", "kvraft"):
        (project / pkg).mkdir(exist_ok=True)
        (project / pkg / ".gitkeep").write_text("")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--sprint", required=True, help="e.g. 01_election")
    ap.add_argument("--config", default=str(REPO / "config" / "models_v2.json"))
    a = ap.parse_args()

    prompt_file = PROMPTS / f"sprint{a.sprint}.txt"
    if not prompt_file.exists():
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
    sprint_tag = prompt_file.stem
    out_dir = out_root / "sprints" / sprint_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    first = not proj.exists()
    if first:
        proj.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=proj)
        subprocess.run(["git", "config", "user.email", "sprinter@example.com"], cwd=proj)
        subprocess.run(["git", "config", "user.name", "Sprinter"], cwd=proj)
        seed_project(proj)
        subprocess.run(["git", "add", "-A"], cwd=proj)
        subprocess.run(["git", "-c", "user.name=Sprinter", "-c", "user.email=sprinter@example.com",
                        "commit", "-q", "-m", "Seed: v4.1 Raft scaffold (harness + go.mod + CONTRACT)"], cwd=proj)

    restore_stranded()
    sh = shield(out_root)
    def _sig(signum, _f):
        unshield(sh); raise SystemExit(128 + signum)
    prev = {s: signal.signal(s, _sig) for s in (signal.SIGTERM, signal.SIGINT)}
    try:
        rec = run_phase(model, sprint_tag, prompt, proj, out_dir)
    finally:
        for s, h in prev.items():
            signal.signal(s, h)
        unshield(sh)

    # snapshot-commit if the model left uncommitted work (common; keeps sprints diffable)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=proj, capture_output=True, text=True).stdout.strip()
    if status:
        subprocess.run(["git", "add", "-A"], cwd=proj)
        subprocess.run(["git", "-c", "user.name=Sprinter", "-c", "user.email=sprinter@example.com",
                        "commit", "-q", "-m", f"SPRINT {sprint_tag} snapshot (model did not self-commit)"], cwd=proj)
    tok = (rec.get("tokens") or {}).get("total")
    print(f"[{model['slug']}] v4.1 sprint {sprint_tag} done elapsed={rec.get('elapsed_seconds')}s "
          f"exit={rec.get('exit_code')} tokens={tok} cost=${rec.get('cost_usd') or 0}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
