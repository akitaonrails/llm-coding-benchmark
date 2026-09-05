#!/usr/bin/env python3
"""Hidden runner for 12-latent-antipatterns. Continuous score (0-100).

The prompt asks only to make the module production-ready and states the functional
contract. It does NOT mention the injected anti-patterns. This suite checks the
contract AND universal good-practice properties: input validation, no mutation of the
caller's arguments, and no leaking of internal mutable state. Each is objectively
observable.

HERMETIC PER CHECK: the candidate module is re-imported fresh for every check, so a
candidate that uses CLASS-LEVEL (shared) state cannot have that state accumulate
across checks and cascade false failures. (Instance-isolation is still tested WITHIN
a single check, where two Directory() built from the same fresh class correctly
reveal whether state is shared.)

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error).
"""
import importlib.util
import itertools
import json
import sys

_CNT = itertools.count()


def fresh_directory(path):
    spec = importlib.util.spec_from_file_location(f"cand_directory_{next(_CNT)}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Directory


def main():
    path = sys.argv[1]
    checks = []  # (tag, weight, fn(D)->bool)

    def chk(tag, weight, fn):
        checks.append((tag, weight, fn))

    # ---------- functional contract ----------
    def func_basic(D):
        d = D()
        d.add_user({"email": "A@X.com", "name": "Ann"})
        u = d.find_by_email("a@x.com")
        return d.count() == 1 and u is not None and u["name"] == "Ann"
    chk("func", 3, func_basic)

    def func_case_insensitive(D):
        d = D()
        d.add_user({"email": "Bob@Site.COM", "name": "Bob"})
        return (d.find_by_email("bob@site.com") is not None
                and d.find_by_email("BOB@SITE.COM") is not None)
    chk("func", 2, func_case_insensitive)

    def func_missing(D):
        return D().find_by_email("nobody@x.com") is None
    chk("func", 1, func_missing)

    # ---------- contract: validation + dedup ----------
    def rejects_invalid(D):
        d = D()
        for bad in ({"email": "noatsign", "name": "x"}, {"email": "a@b.com", "name": ""},
                    {"email": "", "name": "y"}, {"name": "no email"}):
            try:
                d.add_user(bad)
            except Exception:
                pass
        return d.count() == 0 and d.all_users() == []
    chk("validate", 3, rejects_invalid)

    def dedup(D):
        d = D()
        d.add_user({"email": "dup@x.com", "name": "First"})
        try:
            d.add_user({"email": "DUP@X.com", "name": "Second"})
        except Exception:
            pass
        return d.count() == 1
    chk("dedup", 2, dedup)

    # ---------- good practice: don't mutate the caller's argument ----------
    def no_input_mutation(D):
        d = D()
        rec = {"email": "Case@X.com", "name": "Case"}
        d.add_user(rec)
        return rec["email"] == "Case@X.com"
    chk("no_mutation", 3, no_input_mutation)

    # ---------- good practice: don't leak internal mutable state ----------
    def no_leak_all_users(D):
        d = D()
        d.add_user({"email": "leak@x.com", "name": "Leak"})
        lst = d.all_users()
        try:
            lst.clear()
            if lst and isinstance(lst[0], dict):
                lst[0]["name"] = "HACKED"
        except Exception:
            pass
        return d.count() == 1 and d.find_by_email("leak@x.com")["name"] == "Leak"
    chk("no_leak", 3, no_leak_all_users)

    def no_leak_find(D):
        d = D()
        d.add_user({"email": "f@x.com", "name": "Orig"})
        u = d.find_by_email("f@x.com")
        try:
            u["name"] = "HACKED"
        except Exception:
            pass
        return d.find_by_email("f@x.com")["name"] == "Orig"
    chk("no_leak", 2, no_leak_find)

    by = {}
    passW = totW = 0.0
    for tag, w, fn in checks:
        totW += w
        d = by.setdefault(tag, [0, 0])
        d[1] += w
        ok = False
        try:
            ok = bool(fn(fresh_directory(path)))   # fresh module per check == hermetic
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            passW += w
            d[0] += w
    score = round(100.0 * passW / totW, 1) if totW else 0.0
    print(json.dumps({"score": score, "breakdown": {k: f"{v[0]}/{v[1]}" for k, v in by.items()}}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"load_error": f"runner crashed: {e}", "score": None}))
