# Task 04 — Performance: active sessions at each query time

**Category:** performance under a hard gate · **Language:** Rust

## Problem

`main.rs` reads a problem from **stdin** and writes answers to **stdout**.

- A session is a closed interval `[start, end]` (`start <= end`). It is **active** at
  time `t` iff `start <= t <= end`.
- Given `N` sessions and `Q` query times, output, for each query in order, the number
  of sessions active at that time.

### Input (all integers, whitespace-separated)

```
N
s_1 e_1
...
s_N e_N
Q
t_1
...
t_Q
```

### Output

`Q` lines: the active-session count for each query, in order.

Ranges: `0 <= N, Q <= 200000`; times/endpoints fit in `i64` (may be negative, may be
large, may repeat). Counts fit in `u64`.

### Example

```
3
1 5
2 8
10 12
4
0
2
8
11
```
→ `0`, `2`, `1`, `1` (at t=2 sessions [1,5] and [2,8] are active; at t=8 only [2,8]).

## The gate

The starter is O(N·Q) and is correct but **too slow**: the hidden suite includes a
large case (`N = Q = 200000`) run with a **hard wall-time limit**. An O(N·Q) solution
will time out and fail the performance gate; you need roughly O((N+Q) log N) (sort +
binary search, or a coordinate sweep). Small correctness cases are graded too —
boundaries (`t` exactly at a `start` or `end`), empty inputs, duplicates, negatives.

Keep the stdin/stdout format exactly. Rust standard library only (no external crates);
it is compiled with optimizations.
