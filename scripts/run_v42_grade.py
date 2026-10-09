#!/usr/bin/env python3
"""Grade a v4.2/complexity submission (continuous, 0-100).

score = 100 * correctness * quality
  correctness = 1 - mismatches/total over conformance + adversarial workloads.
  quality     = log-position of the candidate's comparison count between the
                naive baseline (sort-per-query, quality 0) and the reference
                baseline (sub-linear, quality 1), at the largest sweep size
                where the candidate is correct and all three impls complete.

Isolation: candidate, reference, and naive each run in their own temp workspace
(module v42complexity: go.mod + harness/ + runner/main.go + ds/<impl>). Identical
seeded workloads make the Cmp counts directly comparable.

Usage:
  # grade a model run:
  run_v42_grade.py --slug v42_fable_5_1
  # validate the grader against a known impl:
  run_v42_grade.py --impl-dir benchmark-v4.2/complexity/reference
  run_v42_grade.py --impl-dir benchmark-v4.2/complexity/broken/naive
  run_v42_grade.py --impl-dir benchmark-v4.2/complexity/broken/wrong
"""
from __future__ import annotations
import argparse, json, math, shutil, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROB = REPO / "benchmark-v4.2" / "complexity"
HARNESS = PROB / "harness"
RUNNER = PROB / "grader" / "runner.go"
REF_DS = PROB / "reference"
NAIVE_DS = PROB / "broken" / "naive"

# correctness configs: (seed, n, q, dup, fullrange)
CORRECTNESS = [
    (1, 500, 4000, False, False),
    (2, 1000, 6000, False, True),
    (3, 800, 6000, True, False),    # many duplicates
    (4, 1500, 8000, True, True),    # duplicates + wide ranges
    (5, 50, 4000, True, False),     # tiny n, update-heavy, heavy dup
    (6, 2000, 8000, False, False),
]
# quality sweep: fixed q, growing n, one seed. Largest size where all complete.
SWEEP_SIZES = [2000, 4000, 8000, 16000, 32000, 64000, 128000]
SWEEP_Q = 2000
SWEEP_SEED = 99
RUN_TIMEOUT = 120  # seconds per runner invocation


def make_ws(ds_dir: Path) -> Path:
    ws = Path(tempfile.mkdtemp(prefix="v42c_"))
    (ws / "go.mod").write_text("module v42complexity\n\ngo 1.22\n")
    shutil.copytree(HARNESS, ws / "harness")
    (ws / "runner").mkdir()
    shutil.copy2(RUNNER, ws / "runner" / "main.go")
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


def run(ws: Path, seed, n, q, dup=False, fullrange=False) -> dict | None:
    args = ["./runbin", f"-seed={seed}", f"-n={n}", f"-q={q}"]
    if dup:
        args.append("-dup")
    if fullrange:
        args.append("-fullrange")
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


def grade(cand_dir: Path) -> dict:
    res: dict = {"impl": str(cand_dir), "correctness": 0.0, "quality": 0.0, "score": 0.0,
                 "build_ok": False, "notes": [], "sweep": []}
    try:
        cand_ws = make_ws(cand_dir)
    except SystemExit as e:
        res["notes"].append(str(e)); return res
    ok, err = build(cand_ws)
    res["build_ok"] = ok
    if not ok:
        res["notes"].append("candidate build failed: " + err[:400]); return res
    ref_ws, naive_ws = make_ws(REF_DS), make_ws(NAIVE_DS)
    for w, nm in ((ref_ws, "reference"), (naive_ws, "naive")):
        bok, berr = build(w)
        if not bok:
            res["notes"].append(f"{nm} baseline build failed: {berr[:200]}"); return res

    # ---- correctness ----
    tot = mism = 0
    for (seed, n, q, dup, fr) in CORRECTNESS:
        o = run(cand_ws, seed, n, q, dup, fr)
        if o is None:
            res["notes"].append(f"correctness timeout seed={seed} n={n}"); continue
        if "_crash" in o:
            res["notes"].append(f"correctness crash seed={seed}: {o['_crash']}"); continue
        tot += o["total"]; mism += o["mismatch"]
    res["correctness"] = round(1 - mism / tot, 4) if tot else 0.0
    res["corr_total"], res["corr_mism"] = tot, mism

    # ---- quality sweep ----
    best = None
    for n in SWEEP_SIZES:
        row = {"n": n}
        c = run(cand_ws, SWEEP_SEED, n, SWEEP_Q)
        rf = run(ref_ws, SWEEP_SEED, n, SWEEP_Q)
        nv = run(naive_ws, SWEEP_SEED, n, SWEEP_Q)
        row["cand"] = None if (c is None or "_crash" in c) else c["cmp"]
        row["cand_mism"] = None if (c is None or "_crash" in c) else c["mismatch"]
        row["ref"] = None if (rf is None or "_crash" in rf) else rf["cmp"]
        row["naive"] = None if (nv is None or "_crash" in nv) else nv["cmp"]
        res["sweep"].append(row)
        if None in (row["cand"], row["ref"], row["naive"]):
            break  # a larger size won't help (naive only gets slower)
        if row["cand_mism"] and row["cand_mism"] > 0:
            break  # candidate no longer correct at this size
        best = row

    if best is None:
        res["notes"].append("no sweep size completed correctly for all three impls")
        res["score"] = round(100 * res["correctness"] * 0.0, 2); return res

    cand, ref, naive = best["cand"], best["ref"], best["naive"]
    res["quality_at_n"] = best["n"]
    res["quality_counts"] = {"cand": cand, "ref": ref, "naive": naive}
    # anomaly: implausibly few comparisons for a comparison-based k-th structure
    if cand < SWEEP_Q:
        res["notes"].append(f"ANOMALY: cand cmp ({cand}) < q ({SWEEP_Q}) — audit source for raw (<,>) comparisons bypassing harness.Cmp")
    if naive <= ref:
        res["notes"].append("degenerate baselines (naive<=ref); quality=1 iff cand<=ref")
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
    ap.add_argument("--slug")
    ap.add_argument("--impl-dir", help="grade a specific ds dir (grader validation)")
    ap.add_argument("--out", help="write grade.json here")
    a = ap.parse_args()
    if a.impl_dir:
        cand = Path(a.impl_dir)
        if not cand.is_absolute():
            cand = REPO / cand
    elif a.slug:
        cand = REPO / "results-v4.2" / "complexity" / a.slug / "project" / "ds"
    else:
        ap.error("need --slug or --impl-dir")
    res = grade(cand)
    print(json.dumps(res, indent=2))
    outp = Path(a.out) if a.out else (
        (REPO / "results-v4.2" / "complexity" / a.slug / "grade.json") if a.slug else None)
    if outp:
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
