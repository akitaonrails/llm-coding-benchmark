#!/usr/bin/env python3
"""Retroactive "intended-idiom recall" dimension for v3 — analog of rails/ai-evals'
API-recall, computed by STATIC ANALYSIS of the solutions models already wrote (no re-run).

For each saved solution we check whether the model used the INTENDED idiom/API (the one
the reference uses) rather than a workaround. Reads results-v3/<slug>/{17,18}/project/.
Signals are deliberately high-precision (a hit strongly implies the intended idiom).
"""
from __future__ import annotations
import ast, glob, json, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results-v3"


def read(p: Path) -> str:
    try:
        return p.read_text()
    except Exception:
        return ""


def recursive_defs(src: str) -> bool:
    """True if any function calls itself (a backtracking/recursive resolver)."""
    try:
        tree = ast.parse(src)
    except Exception:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == name:
                    return True
    return False


def signals(app: Path, resolver: Path) -> dict:
    mk = app / "marketplace"
    pricing = read(mk / "commerce" / "pricing.py")
    queries = read(mk / "analytics" / "queries.py")
    report = read(mk / "analytics" / "report.py")
    restore = read(mk / "admin" / "restore.py")
    directory = read(mk / "accounts" / "directory.py")
    res = read(resolver)

    s = {}
    # money uses Decimal (not float) — intended rounding idiom
    s["money_decimal"] = bool(pricing) and "Decimal" in pricing
    # SQL aggregation uses COUNT(DISTINCT ...) — avoids join fan-out
    s["sql_count_distinct"] = bool(queries) and re.search(r"count\s*\(\s*distinct", queries, re.I) is not None
    # SQL is parameterized (? placeholder), not string-interpolated
    s["sql_parameterized"] = bool(queries) and ("?" in queries) and not re.search(r"execute\(\s*[\"'].*(%s|\+|\{)", queries)
    # report batches DB access (no N+1): uses plural accessors
    s["batched_no_nplus1"] = bool(report) and any(f"get_{x}(" in report for x in ("orders", "customers", "items"))
    # safe tar extraction: path containment check or extractall filter (not bare extractall)
    s["safe_tar_extract"] = bool(restore) and (
        any(k in restore for k in ("realpath", "abspath", "commonpath", "commonprefix"))
        or re.search(r"extractall\([^)]*filter", restore) is not None)
    # directory keeps per-instance state (__init__), not class-level shared list
    s["instance_state"] = bool(directory) and re.search(r"def __init__\s*\(\s*self", directory) is not None
    # email normalized (trim + case-fold)
    s["email_normalized"] = bool(directory) and (".strip()" in directory) and (".lower()" in directory or ".casefold()" in directory)
    # resolver uses backtracking (recursive) rather than one greedy pass
    s["resolver_backtracks"] = bool(res) and recursive_defs(res)
    return s


def main() -> int:
    quality = {}
    for rj in glob.glob(str(RES / "*" / "result.json")):
        r = json.loads(Path(rj).read_text())
        slug = r["slug"]
        ts = [t for t in r["tasks"] if t["task"][:2] in ("17", "18")]
        if ts and all(t.get("correctness") is not None for t in ts):
            quality[slug] = (r.get("label") or slug, round(sum(t["correctness"] for t in ts) / len(ts), 1))

    rows = []
    for d in sorted(glob.glob(str(RES / "*" / "17-marketplace-app" / "project"))):
        slug = Path(d).parents[1].name
        app = Path(d)
        resolver = RES / slug / "18-resolver-backtrack" / "project" / "resolver.py"
        sig = signals(app, resolver)
        got = sum(1 for v in sig.values() if v)
        tot = len(sig)
        label, q = quality.get(slug, (slug, None))
        rows.append({"label": label, "q": q, "recall": round(100 * got / tot, 1),
                     "got": got, "tot": tot, "sig": sig})

    rows.sort(key=lambda x: (-(x["recall"]), -(x["q"] or 0)))
    keys = list(rows[0]["sig"].keys()) if rows else []
    abbr = {"money_decimal": "Dec", "sql_count_distinct": "CntD", "sql_parameterized": "Param",
            "batched_no_nplus1": "Batch", "safe_tar_extract": "SafeTar", "instance_state": "Inst",
            "email_normalized": "Email", "resolver_backtracks": "Backtr"}
    print("v3 INTENDED-IDIOM RECALL (static analysis of saved solutions — no re-run)")
    print(f"{'model':38} {'Qual':>5} {'Recall':>7}  " + " ".join(f"{abbr[k]:>7}" for k in keys))
    print("-" * (38 + 16 + 8 * len(keys)))
    for x in rows:
        cells = " ".join(f"{'yes' if x['sig'][k] else '-':>7}" for k in keys)
        qs = f"{x['q']:.1f}" if x["q"] is not None else "  -"
        print(f"{x['label'][:38]:38} {qs:>5} {x['recall']:>6.1f}%  {cells}")
    print(f"\n{len(rows)} models. Recall = fraction of {len(keys)} intended idioms used "
          f"(Dec=Decimal money, CntD=COUNT(DISTINCT), Param=parameterized SQL, Batch=no N+1, "
          f"SafeTar=path-checked extract, Inst=per-instance state, Email=trim+casefold, "
          f"Backtr=recursive resolver).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
