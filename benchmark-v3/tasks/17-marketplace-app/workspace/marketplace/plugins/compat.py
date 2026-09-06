"""semver.py — semantic-version range satisfaction (npm-style).

Implement `satisfies(version, range_spec)` (see TASK.md). The starter below handles
the common cases but is INCOMPLETE.
"""
import re

_RE = re.compile(r"^[v=]?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


def _parse(v):
    m = _RE.match(v.strip())
    if not m:
        raise ValueError(f"bad version {v!r}")
    maj, mn, pa, pre = m.group(1), m.group(2), m.group(3), m.group(4)
    pre_t = tuple(pre.split(".")) if pre else ()
    return (int(maj), int(mn), int(pa), pre_t)


def _cmp(a, b):
    if a[:3] != b[:3]:
        return -1 if a[:3] < b[:3] else 1
    # prerelease compared as plain strings
    if a[3] == b[3]:
        return 0
    return -1 if a[3] < b[3] else 1


def _test(op, v, ref):
    c = _cmp(v, ref)
    return {"<": c < 0, "<=": c <= 0, ">": c > 0, ">=": c >= 0, "=": c == 0}[op]


def _comparators(token):
    token = token.strip()
    m = re.match(r"^(\^|~|>=|<=|>|<|=)?\s*(.+)$", token)
    op, rest = m.group(1), m.group(2).strip()
    ref = _parse(rest)
    if op in (None, "="):
        return [("=", ref)]
    if op in (">", ">=", "<", "<="):
        return [(op, ref)]
    if op == "~":
        return [(">=", ref), ("<", (ref[0], ref[1] + 1, 0, ()))]
    if op == "^":
        return [(">=", ref), ("<", (ref[0] + 1, 0, 0, ()))]
    raise ValueError(op)


def satisfies(version, range_spec):
    v = _parse(version)
    for group in range_spec.split("||"):
        comps = []
        for tok in group.split():
            comps.extend(_comparators(tok))
        if comps and all(_test(op, v, ref) for op, ref in comps):
            return True
    return False
