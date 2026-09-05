"""median.py — count subarrays by their median.

Implement `count_subarrays_median_at_least(a, k)`: given a list of integers `a` and
an integer `k`, return how many contiguous non-empty subarrays have a MEDIAN that is
>= k. The median of a subarray of length L is the element at index (L-1)//2 of the
sorted subarray (the lower median for even lengths).

The starter below is CORRECT but O(n^2) and will not finish on the large inputs the
hidden suite uses.
"""


def count_subarrays_median_at_least(a, k):
    n = len(a)
    cnt = 0
    for i in range(n):
        ge = lt = 0
        for j in range(i, n):
            if a[j] >= k:
                ge += 1
            else:
                lt += 1
            L = ge + lt
            if lt <= (L - 1) // 2:      # lower-median element is >= k
                cnt += 1
    return cnt
