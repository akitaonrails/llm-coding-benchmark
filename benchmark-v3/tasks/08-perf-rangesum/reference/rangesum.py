"""Reference: sort by timestamp, prefix-sum, binary-search each query bound.

O((N + Q) log N) instead of O(N*Q). Handles negatives, duplicate timestamps, and
empty ranges correctly.
"""
from bisect import bisect_left, bisect_right
from itertools import accumulate
from typing import List, Tuple


def solve(events: List[Tuple[int, int]], queries: List[Tuple[int, int]]) -> List[int]:
    if not events:
        return [0] * len(queries)
    ev = sorted(events, key=lambda e: e[0])
    ts = [e[0] for e in ev]
    prefix = [0]
    prefix.extend(accumulate(e[1] for e in ev))  # prefix[i] = sum of first i values
    out = []
    for lo, hi in queries:
        if hi < lo:
            out.append(0)
            continue
        i = bisect_left(ts, lo)
        j = bisect_right(ts, hi)
        out.append(prefix[j] - prefix[i])
    return out
