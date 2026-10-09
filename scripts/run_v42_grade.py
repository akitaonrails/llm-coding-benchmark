#!/usr/bin/env python3
"""Grade a v4.2 continuous-scoring submission (0-100), problem-parameterized.

score = 100 * correctness * quality
  correctness = 1 - mismatches/total over conformance + adversarial workloads.
  quality     = log-position of the candidate's counted-op total between a naive
                baseline (quality 0) and a sub-linear reference (quality 1), at
                the largest sweep size where the candidate is correct and all
                three impls complete within the time budget.

Isolation: candidate, reference, and naive each run in their own temp workspace
(go.mod + harness/ + runner/main.go + ds/<impl>). Identical seeded workloads
make the counted-op totals directly comparable.

Each problem supplies: its module name, correctness configs, and a sweep-arg
builder (problems differ in runner flags, e.g. complexity uses -fullrange,
slidingkth uses -w). All share this scoring machinery.

Usage:
  run_v42_grade.py --problem complexity --slug v42_fable
  run_v42_grade.py --problem slidingkth --impl-dir benchmark-v4.2/slidingkth/reference
"""
from __future__ import annotations
import argparse, json, math, shutil, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUN_TIMEOUT = 120  # seconds per runner invocation

# Per-problem spec. `module` must match the go.mod in benchmark-v4.2/<dir>.
# `correctness` is a list of runner flag-dicts. `sweep_sizes`/`sweep_q`/
# `sweep_seed` define the quality sweep; `sweep_args(n)` returns the flag-dict
# for one sweep size (fixed q, growing n).
PROBLEMS = {
    "complexity": {
        "module": "v42complexity",
        "correctness": [
            {"seed": 1, "n": 500, "q": 4000},
            {"seed": 2, "n": 1000, "q": 6000, "fullrange": True},
            {"seed": 3, "n": 800, "q": 6000, "dup": True},
            {"seed": 4, "n": 1500, "q": 8000, "dup": True, "fullrange": True},
            {"seed": 5, "n": 50, "q": 4000, "dup": True},
            {"seed": 6, "n": 2000, "q": 8000},
        ],
        "sweep_sizes": [2000, 4000, 8000, 16000, 32000, 64000, 128000],
        "sweep_q": 2000, "sweep_seed": 99,
        "sweep_args": lambda n: {"seed": 99, "n": n, "q": 2000},
    },
    "slidingkth": {
        "module": "v42slidingkth",
        "correctness": [
            {"seed": 1, "n": 3000, "w": 200, "q": 1500},
            {"seed": 2, "n": 4000, "w": 500, "q": 2000, "dup": True},
            {"seed": 3, "n": 2000, "w": 64, "q": 1500, "dup": True},
            {"seed": 4, "n": 5000, "w": 1000, "q": 2500},
            {"seed": 5, "n": 1500, "w": 8, "q": 1200, "dup": True},
        ],
        "sweep_sizes": [4000, 8000, 16000, 32000, 64000, 128000, 200000],
        "sweep_q": 2000, "sweep_seed": 99,
        "sweep_args": lambda n: {"seed": 99, "n": n, "w": n // 2, "q": 2000},
    },
}


def prob_dir(problem: str) -> Path:
    return REPO / "benchmark-v4.2" / problem


def make_ws(module: str, harness: Path, runner: Path, ds_dir: Path) -> Path:
    ws = Path(tempfile.mkdtemp(prefix="v42g_"))
    (ws / "go.mod").write_text(f"module {module}\n\ngo 1.22\n")
    shutil.copytree(harness, ws / "harness")
    (ws / "runner").mkdir()
    shutil.copy2(runner, ws / "runner" / "main.go")
    (ws / "ds").mkdir()
    gofiles = [p for p in ds_dir.glob("*.go") if not p.name.endswith("_test.go")]
    if not gofiles:
        raise SystemExit(f"no .go files in {ds_dir}")
    for p in gofiles:
        shutil.copy2(p, ws / "ds" / p.name)
    return ws


def build(ws: Path) -> tuple[bool, str]:
    r = subprocess.run(["go", "build", "-o", "runbin", "./runner"],
                       cwd=ws, capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


def run(ws: Path, flags: dict) -> dict | None:
    args = ["./runbin"]
    for k, v in flags.items():
        if isinstance(v, bool):
            if v:
                args.append(f"-{k}")
        else:
            args.append(f"-{k}={v}")
    try:
        r = subprocess.run(args, cwd=ws, capture_output=True, text=True, timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0:
        return {"_crash": r.stderr.strip()[:400]}
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"_crash": "unparseable: " + r.stdout.strip()[:200]}


def grade(problem: str, cand_dir: Path) -> dict:
    spec = PROBLEMS[problem]
    pdir = prob_dir(problem)
    harness, runner = pdir / "harness", pdir / "grader" / "runner.go"
    ref_ds, naive_ds = pdir / "reference", pdir / "broken" / "naive"
    res: dict = {"problem": problem, "impl": str(cand_dir), "correctness": 0.0,
                 "quality": 0.0, "score": 0.0, "build_ok": False, "notes": [], "sweep": []}
    try:
        cand_ws = make_ws(spec["module"], harness, runner, cand_dir)
    except SystemExit as e:
        res["notes"].append(str(e)); return res
    ok, err = build(cand_ws)
    res["build_ok"] = ok
    if not ok:
        res["notes"].append("candidate build failed: " + err[:400]); return res
    ref_ws = make_ws(spec["module"], harness, runner, ref_ds)
    naive_ws = make_ws(spec["module"], harness, runner, naive_ds)
    for w, nm in ((ref_ws, "reference"), (naive_ws, "naive")):
        bok, berr = build(w)
        if not bok:
            res["notes"].append(f"{nm} baseline build failed: {berr[:200]}"); return res

    # ---- correctness ----
    tot = mism = 0
    for cfg in spec["correctness"]:
        o = run(cand_ws, cfg)
        if o is None:
            res["notes"].append(f"correctness timeout {cfg}"); continue
        if "_crash" in o:
            res["notes"].append(f"correctness crash {cfg}: {o['_crash']}"); continue
        tot += o["total"]; mism += o["mismatch"]
    res["correctness"] = round(1 - mism / tot, 4) if tot else 0.0
    res["corr_total"], res["corr_mism"] = tot, mism

    # ---- quality sweep ----
    best = None
    for n in spec["sweep_sizes"]:
        fl = spec["sweep_args"](n)
        c = run(cand_ws, fl)
        rf = run(ref_ws, fl)
        nv = run(naive_ws, fl)
        row = {"n": n,
               "cand": None if (c is None or "_crash" in c) else c["cmp"],
               "cand_mism": None if (c is None or "_crash" in c) else c["mismatch"],
               "ref": None if (rf is None or "_crash" in rf) else rf["cmp"],
               "naive": None if (nv is None or "_crash" in nv) else nv["cmp"]}
        res["sweep"].append(row)
        if None in (row["cand"], row["ref"], row["naive"]):
            break
        if row["cand_mism"] and row["cand_mism"] > 0:
            break
        best = row

    if best is None:
        res["notes"].append("no sweep size completed correctly for all three impls")
        res["score"] = 0.0; return res

    cand, ref, naive = best["cand"], best["ref"], best["naive"]
    res["quality_at_n"] = best["n"]
    res["quality_counts"] = {"cand": cand, "ref": ref, "naive": naive}
    if cand < spec["sweep_q"]:
        res["notes"].append(f"ANOMALY: cand cmp ({cand}) < q ({spec['sweep_q']}) — audit source for raw (<,>) bypassing harness.Cmp")
    if naive <= ref:
        res["notes"].append("degenerate baselines (naive<=ref)")
        q = 1.0 if cand <= ref else 0.0
    elif cand <= ref:
        q = 1.0
    else:
        q = (math.log(naive) - math.log(cand)) / (math.log(naive) - math.log(ref))
    q = max(0.0, min(1.0, q))
    res["quality"] = round(q, 4)
    res["score"] = round(100 * res["correctness"] * q, 2)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", default="complexity", choices=list(PROBLEMS))
    ap.add_argument("--slug")
    ap.add_argument("--impl-dir", help="grade a specific ds dir (grader validation)")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.impl_dir:
        cand = Path(a.impl_dir)
        if not cand.is_absolute():
            cand = REPO / cand
    elif a.slug:
        cand = REPO / "results-v4.2" / a.problem / a.slug / "project" / "ds"
    else:
        ap.error("need --slug or --impl-dir")
    res = grade(a.problem, cand)
    print(json.dumps(res, indent=2))
    outp = Path(a.out) if a.out else (
        (REPO / "results-v4.2" / a.problem / a.slug / "grade.json") if a.slug else None)
    if outp:
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
