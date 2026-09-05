"""rangesum: answer many range-sum queries over timestamped values.

You are given N events, each (timestamp, value), and Q queries, each an inclusive
range (lo, hi). For every query return the SUM of the values of all events whose
timestamp is within [lo, hi].

The starter below is CORRECT but SLOW (it rescans every event for every query, so
it is O(N*Q)). Your score is graded on a SPECTRUM by how fast your solution runs on
a large hidden input relative to an efficient reference — a correct-but-slow answer
scores poorly, an answer that matches the reference's efficiency scores full marks.
Timestamps, values, and ranges can be any integers (values may be negative). There
may be many events sharing a timestamp. Standard library only. Keep the signature.
"""
from typing import List, Tuple


def solve(events: List[Tuple[int, int]], queries: List[Tuple[int, int]]) -> List[int]:
    """Return, for each (lo, hi) query, the sum of values with lo <= ts <= hi."""
    # SLOW: linear scan per query -> O(N*Q).
    out = []
    for lo, hi in queries:
        s = 0
        for ts, val in events:
            if lo <= ts <= hi:
                s += val
        out.append(s)
    return out
