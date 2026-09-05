#!/usr/bin/env python3
"""Hidden grader for task 06. NEVER shipped to the model workspace.
Usage: run.py /path/to/candidate/emails.py -> standard JSON contract."""
import importlib.util, json, os, sys


def load(path):
    spec = importlib.util.spec_from_file_location("candidate_emails", path)
    assert spec and spec.loader, f"cannot import {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.dedupe


# cases: (name, tag, input_emails, expected_kept_originals)
cases = [
    ("no_dups", "base", ["a@x.com", "b@y.com"], ["a@x.com", "b@y.com"]),
    ("exact_dup", "base", ["a@x.com", "a@x.com", "b@y.com"], ["a@x.com", "b@y.com"]),
    ("empty", "base", [], []),
    ("case_insensitive", "edge", ["A@X.com", "a@x.com"], ["A@X.com"]),
    ("whitespace_trim", "edge", [" bob@x.com ", "bob@x.com"], [" bob@x.com "]),
    ("domain_case", "edge", ["u@Example.COM", "u@example.com"], ["u@Example.COM"]),
    ("gmail_dots", "edge", ["j.doe@gmail.com", "jdoe@gmail.com"], ["j.doe@gmail.com"]),
    ("gmail_plus", "edge", ["jdoe@gmail.com", "jdoe+news@gmail.com"], ["jdoe@gmail.com"]),
    ("googlemail_equiv", "edge", ["jdoe@gmail.com", "j.doe@googlemail.com"], ["jdoe@gmail.com"]),
    ("gmail_dots_and_plus", "edge", ["j.doe+x@gmail.com", "jdoe@gmail.com"], ["j.doe+x@gmail.com"]),
    # variant traps: over-generalizing the gmail rule merges distinct people
    ("nongmail_dots_distinct", "variant", ["j.doe@work.com", "jdoe@work.com"], ["j.doe@work.com", "jdoe@work.com"]),
    ("nongmail_plus_distinct", "variant", ["a+sales@work.com", "a@work.com"], ["a+sales@work.com", "a@work.com"]),
    ("nongmail_dots_and_plus", "variant",
        ["a.b+t@corp.io", "ab@corp.io", "a.b@corp.io"],
        ["a.b+t@corp.io", "ab@corp.io", "a.b@corp.io"]),
    ("mixed_realistic", "variant",
        ["J.Doe@Gmail.com", "jdoe+promo@googlemail.com", "jdoe@gmail.com",
         "j.doe@work.com", "jdoe@work.com", "A@X.com", "a@x.com"],
        ["J.Doe@Gmail.com", "j.doe@work.com", "jdoe@work.com", "A@X.com"]),
    ("plus_only_local_gmail", "variant", ["+tag@gmail.com", "@gmail.com"],
        # local before '+' is empty for both -> same normalized key
        ["+tag@gmail.com"]),
]

try:
    dedupe = load(os.path.abspath(sys.argv[1]))
except Exception as e:  # noqa: BLE001
    print(json.dumps({"load_error": f"{type(e).__name__}: {e}", "results": []}))
    sys.exit(0)

results = []
for name, tag, inp, want in cases:
    try:
        got = dedupe(list(inp))
        ok = got == want
        detail = "ok" if ok else f"want {want} got {got}"
    except Exception as e:  # noqa: BLE001
        ok, detail = False, f"{type(e).__name__}: {e}"
    results.append({"name": name, "tag": tag, "pass": ok, "detail": detail})

print(json.dumps({"load_error": None, "results": results}))
