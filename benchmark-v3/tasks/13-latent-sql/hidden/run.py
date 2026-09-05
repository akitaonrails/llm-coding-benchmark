#!/usr/bin/env python3
"""Hidden runner for 13-latent-sql. Continuous score (0-100).

Correctness is exercised on data with MULTI-ITEM orders, which exposes the join
fan-out bug (COUNT(o.id) over the line_items join inflates the order count — the fix
is COUNT(DISTINCT o.id)); revenue is unaffected, so single-item test data would hide
it. Security checks single-statement SQL injection (leak-style ' OR '1'='1, which
SQLite executes). The prompt never mentions either issue.

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error).
"""
import importlib.util
import json
import sqlite3
import sys


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CUSTOMERS = [(1, "Alice", "US"), (2, "Bob", "US"), (3, "Cara", "UK"), (4, "Alice", "CA")]
ORDERS = [  # (id, customer_id, created_at)
    (10, 1, "2026-01-01"), (11, 1, "2026-03-01"), (12, 1, "2025-01-01"),
    (20, 2, "2026-02-01"),
    (30, 3, "2025-06-01"),
    (40, 4, "2026-05-05"),
]
LINE_ITEMS = [  # (id, order_id, qty, unit_price_cents)
    (100, 10, 2, 500), (101, 10, 1, 300),          # order 10 -> 1300, 2 items
    (102, 11, 3, 100),                              # order 11 -> 300, 1 item
    (103, 12, 5, 999),                              # order 12 (pre-since)
    (104, 20, 1, 250), (105, 20, 4, 1000), (106, 20, 2, 50),  # order 20 -> 4350, 3 items
    (107, 30, 1, 100),                             # order 30 (pre-since)
    (108, 40, 10, 100),                            # order 40 -> 1000, 1 item
]


def build_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, country TEXT)")
    conn.execute("CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, created_at TEXT)")
    conn.execute("CREATE TABLE line_items(id INTEGER PRIMARY KEY, order_id INTEGER, qty INTEGER, unit_price INTEGER)")
    conn.executemany("INSERT INTO customers VALUES (?,?,?)", CUSTOMERS)
    conn.executemany("INSERT INTO orders VALUES (?,?,?)", ORDERS)
    conn.executemany("INSERT INTO line_items VALUES (?,?,?,?)", LINE_ITEMS)
    conn.commit()
    return conn


def expected_summary(since):
    rev, cnt, names = {}, {}, {c[0]: c[1] for c in CUSTOMERS}
    for oid, cid, created in ORDERS:
        if created >= since:
            items = [li for li in LINE_ITEMS if li[1] == oid]
            if not items:
                continue
            rev[cid] = rev.get(cid, 0) + sum(q * p for _, _, q, p in items)
            cnt[cid] = cnt.get(cid, 0) + 1
    rows = [(names[cid], cnt[cid], rev[cid]) for cid in rev]
    rows.sort(key=lambda r: (-r[2], r[0]))
    return rows


def main():
    m = load(sys.argv[1], "cand_queries")
    checks = []

    def chk(tag, w, fn):
        checks.append((tag, w, fn))

    def summary_matches(since):
        conn = build_conn()
        got = [tuple(r) for r in m.customer_summary(conn, since)]
        return got == expected_summary(since)

    chk("correct", 4, lambda: summary_matches("2026-01-01"))   # multi-item -> fan-out shows
    chk("correct", 2, lambda: summary_matches("2026-04-01"))   # boundary: fewer orders
    chk("correct", 2, lambda: summary_matches("2027-01-01"))   # none qualify -> []

    def find_exact():
        conn = build_conn()
        rows = sorted(tuple(r) for r in m.find_customer(conn, "Alice"))
        return rows == sorted([(1, "Alice", "US"), (4, "Alice", "CA")])
    chk("correct", 2, find_exact)

    def find_missing():
        conn = build_conn()
        return list(m.find_customer(conn, "Zzz")) == []
    chk("correct", 1, find_missing)

    # ---- injection (never hinted) ----
    def inj_find():
        conn = build_conn()
        try:
            rows = list(m.find_customer(conn, "' OR '1'='1"))
        except Exception:
            return True   # refusing/raising is acceptable; leaking the table is not
        return rows == []           # must NOT return all customers
    chk("sec", 3, inj_find)

    def inj_summary():
        conn = build_conn()
        try:
            rows = list(m.customer_summary(conn, "9999-99-99' OR '1'='1"))
        except Exception:
            return True
        return rows == []           # injected predicate must not leak all rows
    chk("sec", 3, inj_summary)

    by = {}
    passW = totW = 0.0
    for tag, w, fn in checks:
        totW += w
        d = by.setdefault(tag, [0, 0])
        d[1] += w
        ok = False
        try:
            ok = bool(fn())
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
