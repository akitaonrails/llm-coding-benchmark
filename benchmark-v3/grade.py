#!/usr/bin/env python3
"""Language-agnostic grader for benchmark-v3 tasks.

Every task ships a hidden runner (any language) that takes a candidate entrypoint
path and prints ONE json object to stdout:

    {"load_error": null|str, "results": [{"name":..,"tag":..,"pass":bool,"detail":..}, ...]}

Scoring (per task, 0-100):
  correctness = 100 * (sum of tag-weights over PASSED cases) / (sum over all cases)
  gates: for each meta.gates["<tag>_gate"], if ANY case with that tag failed,
         cap correctness at the gate's "cap".

Usage:
  grade.py <task_dir> --candidate <workspace_dir>   # score a model's edited workspace
  grade.py <task_dir> --validate                      # prove the task discriminates
  grade.py --all --candidates-root <dir>             # score every task for one model run
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path


def run_hidden(task_dir: Path, entrypoint_abs: Path, timeout: int) -> dict:
    meta = json.loads((task_dir / "meta.json").read_text())
    cmd = list(meta["hidden_runner"]) + [str(entrypoint_abs)]
    try:
        p = subprocess.run(cmd, cwd=task_dir, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"load_error": f"hidden runner timed out after {timeout}s", "results": []}
    out = p.stdout.strip()
    # the runner prints one JSON object (last line, to tolerate build chatter)
    for line in reversed(out.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {"load_error": f"no JSON from hidden runner (rc={p.returncode}); stderr: {p.stderr[-400:]}", "results": []}


def score(task_dir: Path, data: dict) -> dict:
    meta = json.loads((task_dir / "meta.json").read_text())
    weights = meta.get("weights", {})
    # Continuous tasks: the hidden runner emits a numeric 0-100 `score` directly
    # (measured speed, exploit-coverage %, optimality ratio, composite metric, ...).
    if data.get("score") is not None and not data.get("load_error"):
        return {"correctness": round(float(data["score"]), 1), "continuous": True,
                "load_error": None, "capped_by": None,
                "by_tag": data.get("breakdown", {}), "failures": []}
    results = data.get("results", [])
    if data.get("load_error") or not results:
        return {"correctness": 0.0, "passed": 0, "total": len(results),
                "load_error": data.get("load_error"), "capped_by": None, "by_tag": {}}

    def w(tag): return weights.get(tag, 1)
    total_w = sum(w(r["tag"]) for r in results)
    pass_w = sum(w(r["tag"]) for r in results if r["pass"])
    correctness = 100.0 * pass_w / total_w if total_w else 0.0

    capped_by = None
    for gname, gate in meta.get("gates", {}).items():
        tag = gname[:-5] if gname.endswith("_gate") else gname
        if any((r["tag"] == tag and not r["pass"]) for r in results):
            cap = float(gate["cap"])
            if correctness > cap:
                correctness = cap
                capped_by = gname

    by_tag = {}
    for r in results:
        d = by_tag.setdefault(r["tag"], [0, 0])
        d[1] += 1
        if r["pass"]:
            d[0] += 1
    return {"correctness": round(correctness, 1),
            "passed": sum(1 for r in results if r["pass"]), "total": len(results),
            "load_error": None, "capped_by": capped_by,
            "by_tag": {k: f"{v[0]}/{v[1]}" for k, v in by_tag.items()},
            "failures": [r["name"] for r in results if not r["pass"]]}


def grade_one(task_dir: Path, entrypoint_abs: Path, timeout: int) -> dict:
    return score(task_dir, run_hidden(task_dir, entrypoint_abs, timeout))


def validate(task_dir: Path, timeout: int) -> int:
    meta = json.loads((task_dir / "meta.json").read_text())
    v = meta["validation"]
    ref = grade_one(task_dir, (task_dir / v["reference_entrypoint"]).resolve(), timeout)
    naive = grade_one(task_dir, (task_dir / v["naive_entrypoint"]).resolve(), timeout)
    print(f"  reference: {ref['correctness']} (need >= {v['reference_min']})  by_tag={ref['by_tag']} capped={ref['capped_by']}")
    print(f"  naive:     {naive['correctness']} (need <= {v['naive_max']})   by_tag={naive['by_tag']} capped={naive['capped_by']} fails={naive.get('failures')}")
    ok = ref["correctness"] >= v["reference_min"] and naive["correctness"] <= v["naive_max"]
    spread = ref["correctness"] - naive["correctness"]
    print(f"  => {'ADMISSIBLE' if ok else 'REJECTED'} (discriminating spread = {spread:.1f} pts)")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir", nargs="?")
    ap.add_argument("--candidate", help="workspace dir the model edited")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--all", action="store_true", help="grade every task under tasks/")
    ap.add_argument("--candidates-root", help="with --all: dir containing <task-id>/ workspaces")
    ap.add_argument("--timeout", type=int, default=120)
    a = ap.parse_args()
    root = Path(__file__).parent

    if a.all:
        tasks = sorted((root / "tasks").glob("*/"))
        scores = []
        for t in tasks:
            meta = json.loads((t / "meta.json").read_text())
            if a.candidates_root:
                ws = Path(a.candidates_root) / t.name
                ep = (ws / meta["entrypoint"]).resolve()
            else:
                ep = (t / "reference" / Path(meta["entrypoint"]).name).resolve()
            r = grade_one(t, ep, a.timeout)
            scores.append(r["correctness"])
            print(f"{t.name:34} {r['correctness']:>6}  {r['by_tag']}  {'CAP:'+r['capped_by'] if r['capped_by'] else ''}")
        print(f"{'MEAN':34} {sum(scores)/len(scores):>6.1f}")
        return 0

    if not a.task_dir:
        ap.error("task_dir required unless --all")
    td = Path(a.task_dir)
    if a.validate:
        return validate(td, a.timeout)
    meta = json.loads((td / "meta.json").read_text())
    ep = (Path(a.candidate) / meta["entrypoint"]).resolve()
    r = grade_one(td, ep, a.timeout)
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
