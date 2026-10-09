#!/usr/bin/env python3
"""Run ONE v4.2 sprint for a model in an isolated, git-sandboxed, shielded workspace.

v4.2 problems are (mostly) one-shot Track-B density tests: seed harness/ + go.mod + CONTRACT.md
(+ SPEC.md if present), NOT grader/reference/broken/prompts. Shields the FULL answer key for every
benchmark generation (v4.2 AND v4.1 AND v4), docs, CLAUDE.md, .agents, and sibling results.

Usage: run_v42_sprint.py --problem complexity --model <slug> --sprint 01_rangekth [--config ...]
"""
from __future__ import annotations
import argparse, signal, subprocess, sys, uuid, shutil, json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
SHIELD_BASE = REPO.parent
SHIELD = ["benchmark-v4.2", "benchmark-v4.1", "benchmark-v4", "docs",
          ".agents/skills/benchmark-audit", "CLAUDE.md"]
SEED_EXCLUDE_DIRS = {"grader", "reference", "prompts", "broken"}


def out_dir_for(problem: str) -> Path:
    return REPO / "results-v4.2" / problem


def shield(out_root: Path, OUT: Path) -> Path:
    sh = SHIELD_BASE / f".v42shield_{uuid.uuid4().hex[:8]}"
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


def unshield(sh: Path, OUT: Path) -> None:
    for rel in SHIELD:
        src = sh / "misc" / rel
        if src.exists():
            (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(REPO / rel))
    res = sh / "results"
    if res.exists():
        OUT.mkdir(parents=True, exist_ok=True)
        for d in res.iterdir():
            shutil.move(str(d), str(OUT / d.name))
    shutil.rmtree(sh, ignore_errors=True)


def restore_stranded(OUT: Path) -> None:
    for sh in sorted(SHIELD_BASE.glob(".v42shield_*")):
        if not sh.is_dir():
            continue
        try:
            n = subprocess.run(["pgrep", "-fc", "run_v42_sprint.py"], capture_output=True, text=True).stdout.strip()
            if n and int(n) > 1:
                print(f"[shield-recover] another run active — skipping {sh.name}"); continue
        except Exception:
            pass
        ok = True
        for rel in SHIELD:
            src = sh / "misc" / rel
            if src.exists():
                if (REPO / rel).exists(): ok = False
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


def seed_project(project: Path, pdir: Path) -> None:
    for f in ("go.mod", "CONTRACT.md", "SPEC.md"):
        if (pdir / f).exists():
            shutil.copy2(pdir / f, project / f)
    hsrc = pdir / "harness"
    if hsrc.exists():
        hdst = project / "harness"; hdst.mkdir(parents=True, exist_ok=True)
        for item in hsrc.iterdir():
            if item.name in SEED_EXCLUDE_DIRS:
                continue
            if item.is_dir():
                shutil.copytree(item, hdst / item.name)
            else:
                shutil.copy2(item, hdst / item.name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", default="complexity")
    ap.add_argument("--model", required=True)
    ap.add_argument("--sprint", required=True, help="e.g. 01_rangekth")
    ap.add_argument("--config", default=str(REPO / "config" / "models_v42.json"))
    a = ap.parse_args()

    pdir = REPO / "benchmark-v4.2" / a.problem
    PROMPTS = pdir / "prompts"
    OUT = out_dir_for(a.problem)

    prompt_file = PROMPTS / f"sprint{a.sprint}.txt"
    if not prompt_file.exists():
        cand = list(PROMPTS.glob(f"sprint{a.sprint}*.txt")) or list(PROMPTS.glob(f"*{a.sprint}*.txt"))
        if not cand:
            ap.error(f"no prompt for sprint {a.sprint} in {PROMPTS}")
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
    sprint_out = out_root / "sprints" / sprint_tag
    sprint_out.mkdir(parents=True, exist_ok=True)

    if not proj.exists():
        proj.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=proj)
        subprocess.run(["git", "config", "user.email", "sprinter@example.com"], cwd=proj)
        subprocess.run(["git", "config", "user.name", "Sprinter"], cwd=proj)
        seed_project(proj, pdir)
        subprocess.run(["git", "add", "-A"], cwd=proj)
        subprocess.run(["git", "-c", "user.name=Sprinter", "-c", "user.email=sprinter@example.com",
                        "commit", "-q", "-m", f"Seed: v4.2 {a.problem} scaffold"], cwd=proj)

    restore_stranded(OUT)
    sh = shield(out_root, OUT)
    def _sig(signum, _f):
        unshield(sh, OUT); raise SystemExit(128 + signum)
    prev = {s: signal.signal(s, _sig) for s in (signal.SIGTERM, signal.SIGINT)}
    try:
        rec = run_phase(model, sprint_tag, prompt, proj, sprint_out)
    finally:
        for s, h in prev.items():
            signal.signal(s, h)
        unshield(sh, OUT)

    status = subprocess.run(["git", "status", "--porcelain"], cwd=proj, capture_output=True, text=True).stdout.strip()
    if status:
        subprocess.run(["git", "add", "-A"], cwd=proj)
        subprocess.run(["git", "-c", "user.name=Sprinter", "-c", "user.email=sprinter@example.com",
                        "commit", "-q", "-m", f"SPRINT {sprint_tag} snapshot (model did not self-commit)"], cwd=proj)
    tok = (rec.get("tokens") or {}).get("total")
    print(f"[{model['slug']}] v4.2/{a.problem} sprint {sprint_tag} done elapsed={rec.get('elapsed_seconds')}s "
          f"exit={rec.get('exit_code')} tokens={tok} cost=${rec.get('cost_usd') or 0}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
