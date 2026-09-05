"""Reference: O(n log n) via the +1/-1 transform observation.

Map a_i -> +1 if a_i >= k else -1, and let P be the prefix sums (P[0]=0). For a
subarray (i, j] of length L with transformed sum S = P[j]-P[i], the lower median is
>= k iff S >= 1 (equivalently P[i] < P[j]) — because S and L share parity, so the odd
case needs S>=1 and the even case needs S>=2, which unify to S>=1. So the answer is
the number of pairs i<j with P[i] < P[j]: a classic "count smaller before" done with
a Fenwick tree in O(n log n).
"""


def count_subarrays_median_at_least(a, k):
    n = len(a)
    # prefix values range in [-n, n]; shift to [1, 2n+1] for the Fenwick tree.
    size = 2 * n + 2
    tree = [0] * (size + 1)

    def add(idx):
        while idx <= size:
            tree[idx] += 1
            idx += idx & (-idx)

    def query(idx):  # count of inserted values with position <= idx
        s = 0
        while idx > 0:
            s += tree[idx]
            idx -= idx & (-idx)
        return s

    def pos(p):
        return p + n + 1  # map prefix value p in [-n, n] to [1, 2n+1]

    total = 0
    p = 0
    add(pos(0))          # P[0] = 0 inserted
    for x in a:
        p += 1 if x >= k else -1
        # number of earlier prefixes strictly less than current p
        total += query(pos(p) - 1)
        add(pos(p))
    return total
