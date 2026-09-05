#!/usr/bin/env python3
"""Benchmark-v3 runner: run one model across the hidden-graded v3 task suite.

Each task runs in its OWN isolated, git-sandboxed workspace (a copy of the task's
starter files only — the hidden tests and reference solutions are shielded out of
the filesystem during the run). Grading is objective (grade.py against the hidden
suite), so scores cannot drift by attention the way a rubric can.

Usage:
  run_v3.py --model <slug> [--tasks all|01,03] [--config config/models_v2.json]
  run_v3.py --self-test            # copy each reference in as the "candidate" and
                                   # grade — proves the plumbing (no model spend)
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
TASKS_DIR = REPO / "benchmark-v3" / "tasks"
GRADER = REPO / "benchmark-v3" / "grade.py"


def load_tasks(which: str) -> list[Path]:
    all_tasks = sorted(p for p in TASKS_DIR.iterdir() if (p / "meta.json").exists())
    if which == "all":
        return all_tasks
    want = set(which.split(","))
    return [t for t in all_tasks if any(t.name.startswith(w) or t.name == w for w in want)]


def build_prompt(task_dir: Path) -> str:
    task_md = (task_dir / "TASK.md").read_text()
    files = []
    ws = task_dir / "workspace"
    for f in sorted(ws.rglob("*")):
        if f.is_file():
            files.append(str(f.relative_to(ws)))
    listing = "\n".join(f"  - {f}" for f in files)
    return (
        "You are working in the CURRENT directory on a single, self-contained coding "
        "task. The files already present are:\n" + listing + "\n\n"
        "Edit those files IN PLACE to solve the task. Do NOT create a nested project "
        "directory or a second copy of the app. Do NOT add external dependencies — "
        "standard library only unless the task explicitly allows otherwise. Do not "
        "stop to ask questions; implement the solution and finish.\n\n"
        "Your solution is graded by a hidden, adversarial test suite you cannot see, "
        "weighted toward edge cases — make the solution correct in general, not just "
        "for any examples shown.\n\n"
        "================ TASK ================\n\n" + task_md
    )


def grade(task_dir: Path, candidate_project: Path, timeout: int) -> dict:
    p = subprocess.run(
        ["python3", str(GRADER), str(task_dir), "--candidate", str(candidate_project),
         "--timeout", str(timeout)],
        capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"correctness": 0.0, "load_error": f"grader error: {p.stdout[-200:]} {p.stderr[-200:]}"}


GRADING_KEY = ["docs", ".agents/skills/benchmark-audit", "CLAUDE.md"]


def shield(out_root: Path) -> Path:
    """Remove EVERYTHING a running model could cheat from out of the repo tree, for
    the duration of the run. Guarantees zero contamination between test runs:

      * every task's hidden/ and reference/  (ALL tasks, not just the ones being run,
        so a subset run can't read another task's grader/answer)
      * the v2 grading key (docs/, CLAUDE.md, benchmark-audit skill)
      * every OTHER model's results-v3/<slug> solution dir (so this model can never
        read a prior model's fix and copy it)

    Returns the shield dir; pass it to unshield() to restore atomically in a finally.
    """
    sh = Path.home() / ".cache" / f".v3shield_{uuid.uuid4().hex[:8]}"
    (sh / "tasks").mkdir(parents=True)
    (sh / "misc").mkdir(parents=True)
    (sh / "results").mkdir(parents=True)
    for t in sorted(p for p in TASKS_DIR.iterdir() if (p / "meta.json").exists()):
        for sub in ("hidden", "reference"):
            src = t / sub
            if src.exists():
                dst = sh / "tasks" / t.name / sub
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
    for rel in GRADING_KEY:
        src = REPO / rel
        if src.exists():
            dst = sh / "misc" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    # other models' outputs (never the current run's own dir)
    if out_root.parent.exists():
        for d in out_root.parent.iterdir():
            if d.is_dir() and d.resolve() != out_root.resolve():
                shutil.move(str(d), str(sh / "results" / d.name))
    _assert_clean(out_root)
    return sh


def _assert_clean(out_root: Path) -> None:
    """Fail loudly rather than run a contaminated benchmark."""
    leaks = []
    for t in TASKS_DIR.iterdir():
        for sub in ("hidden", "reference"):
            if (t / sub).exists():
                leaks.append(str((t / sub).relative_to(REPO)))
    for rel in GRADING_KEY:
        if (REPO / rel).exists():
            leaks.append(rel)
    if out_root.parent.exists():
        for d in out_root.parent.iterdir():
            if d.is_dir() and d.resolve() != out_root.resolve():
                leaks.append(str(d.relative_to(REPO)))
    if leaks:
        raise RuntimeError(f"shield incomplete, refusing to run — still exposed: {leaks}")


def unshield(sh: Path) -> None:
    for tdir in (sh / "tasks").iterdir() if (sh / "tasks").exists() else []:
        for sub in ("hidden", "reference"):
            src = tdir / sub
            if src.exists():
                shutil.move(str(src), str(TASKS_DIR / tdir.name / sub))
    for rel in GRADING_KEY:
        src = sh / "misc" / rel
        if src.exists():
            (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(REPO / rel))
    res = sh / "results"
    if res.exists():
        for d in res.iterdir():
            shutil.move(str(d), str(REPO / "results-v3" / d.name))
    shutil.rmtree(sh, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--config", default=str(REPO / "config" / "models_v2.json"))
    ap.add_argument("--tasks", default="all")
    ap.add_argument("--out", default=str(REPO / "results-v3"))
    ap.add_argument("--grade-timeout", type=int, default=240)
    a = ap.parse_args()
    tasks = load_tasks(a.tasks)
    if not tasks:
        ap.error("no matching tasks")
    # Preflight: fail fast (before any run/spend or shield) on malformed tasks.
    bad = [t.name for t in tasks
           if not (t / "TASK.md").exists() or not (t / "workspace").is_dir()
           or not (t / "hidden").exists() or not (t / "reference").exists()]
    if bad:
        ap.error(f"tasks missing TASK.md/workspace/hidden/reference: {bad}")

    if a.self_test:
        scores = []
        for t in tasks:
            meta = json.loads((t / "meta.json").read_text())
            with __import__("tempfile").TemporaryDirectory() as d:
                proj = Path(d) / "project"
                shutil.copytree(t / "workspace", proj)
                # overlay the reference file(s) onto the workspace
                for rf in (t / "reference").iterdir():
                    tgt = proj / meta["entrypoint"]
                    if rf.name == Path(meta["entrypoint"]).name:
                        tgt.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(rf, tgt)
                r = grade(t, proj, a.grade_timeout)
            print(f"{t.name:34} {r.get('correctness'):>6}  {r.get('by_tag', {})}")
            scores.append(r.get("correctness") or 0.0)
        print(f"{'MEAN (self-test, references)':34} {sum(scores)/len(scores):>6.1f}")
        return 0

    if not a.model:
        ap.error("--model required unless --self-test")
    from run_benchmark_v2 import run_phase  # reuse the full harness
    models = json.loads(Path(a.config).read_text())["models"]
    model = next((m for m in models if m["slug"] == a.model), None)
    if not model:
        ap.error(f"model {a.model} not in {a.config}")

    out_root = Path(a.out) / model["slug"]
    out_root.mkdir(parents=True, exist_ok=True)
    sh = shield(out_root)
    phase_records = []
    try:
        for t in tasks:
            out_dir = out_root / t.name
            proj = out_dir / "project"
            if proj.exists():
                shutil.rmtree(proj)
            shutil.copytree(t / "workspace", proj)
            prompt = build_prompt(t)
            print(f"[{model['slug']}] running task {t.name} ...")
            rec = run_phase(model, t.name, prompt, proj, out_dir)
            phase_records.append((t, rec))
    finally:
        unshield(sh)

    # grade (hidden restored)
    results = []
    for t, rec in phase_records:
        proj = out_root / t.name / "project"
        g = grade(t, proj, a.grade_timeout)
        meta = json.loads((t / "meta.json").read_text())
        results.append({
            "task": t.name, "category": meta["category"], "language": meta["language"],
            "correctness": g.get("correctness"), "by_tag": g.get("by_tag"),
            "capped_by": g.get("capped_by"), "load_error": g.get("load_error"),
            "elapsed_seconds": rec.get("elapsed_seconds"), "stall_aborted": rec.get("stall_aborted"),
        })
        print(f"  {t.name:30} correctness={g.get('correctness')}  {g.get('by_tag')}  "
              f"{'CAP:'+g['capped_by'] if g.get('capped_by') else ''}")
    mean = round(sum((r["correctness"] or 0.0) for r in results) / len(results), 1)
    summary = {
        "slug": model["slug"], "label": model.get("label"), "harness": model["harness"],
        "v3_score": mean, "tasks": results,
        "elapsed_seconds_total": round(sum((r["elapsed_seconds"] or 0) for r in results), 1),
    }
    (out_root / "result.json").write_text(json.dumps(summary, indent=2))
    print(f"[{model['slug']}] V3 SCORE = {mean}  ({len(results)} tasks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
