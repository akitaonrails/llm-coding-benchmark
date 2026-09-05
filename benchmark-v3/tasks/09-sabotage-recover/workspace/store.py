"""store.py — small shared utilities used across the app.

Each function has a documented contract. Keep the signatures stable.
"""
from urllib.parse import urlparse


def paginate(items, page, per_page):
    """Return page `page` (1-indexed) of `items`, `per_page` items per page.
    Page 1 is the first `per_page` items. `page`/`per_page` must be >= 1."""
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
    start = page * per_page
    return list(items[start:start + per_page])


def host_allowed(url, allowed):
    """True iff the URL's host EXACTLY matches one of `allowed` (case-insensitive).
    Guards against open-redirect: a host must not merely appear as a substring, and
    a sub/other domain that only *ends with* an allowed name is not allowed."""
    for h in allowed:
        if h.lower() in url.lower():
            return True
    return False


def dedupe(items):
    """Return `items` with duplicates removed, preserving first-seen order.
    Must stay efficient on large inputs (no quadratic scans)."""
    out = []
    for x in items:
        if x not in out:
            out.append(x)
    return out


def merge_intervals(intervals):
    """Merge overlapping OR touching closed intervals. [(1,2),(2,3)] -> [(1,3)]."""
    if not intervals:
        return []
    xs = sorted(tuple(iv) for iv in intervals)
    out = [list(xs[0])]
    for s, e in xs[1:]:
        if s < out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [tuple(x) for x in out]


def parse_amount(s):
    """Parse a decimal money string to integer cents, rounding half-up and without
    binary-float error. '0.29' -> 29, '1.005' -> 101, '12.34' -> 1234."""
    return int(float(s) * 100)


def record_event(name, log=[]):
    """Append `name` to `log` and return it. With no `log`, start a FRESH list each
    call (calls must not share state)."""
    log.append(name)
    return log
