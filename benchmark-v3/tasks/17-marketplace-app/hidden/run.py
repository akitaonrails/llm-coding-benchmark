#!/usr/bin/env python3
"""Aggregate hidden grader for 17-marketplace-app. Continuous score (0-100).

One coherent `marketplace/` app; the score is the weighted fraction of independent
checks across FIVE feature areas, each with DISTINCT failure modes (no near-duplicates):
  commerce  — checkout/pricing/inventory/idempotency/atomicity (cross-file)
  accounts  — user directory production-readiness (validation, no-leak, no-mutation)
  admin     — backup restore hardened against path traversal (latent CVE)
  plugins   — version-range compatibility (edge-case-intensive)
  analytics — SQL correctness+injection, and an efficient (non-N+1) report

Each check re-imports the relevant module(s) fresh (hermetic vs class-level state) and
compares against an independent oracle. Emits ONE json line:
{"score": float, "breakdown": {...}}  (or load_error).
"""
import io
import json
import os
import sqlite3
import sys
import tarfile
import tempfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = str(Path(sys.argv[1]).resolve().parents[2])  # dir containing marketplace/
CATALOG_SPEC = {"A": ("Apple", 100), "B": ("Banana", 250), "C": ("Cherry", 999)}


def _purge():
    for m in list(sys.modules):
        if m == "marketplace" or m.startswith("marketplace."):
            del sys.modules[m]
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)


def imp(dotted):
    _purge()
    import importlib
    return importlib.import_module("marketplace." + dotted)


# ---------------- oracle ----------------
def rc(d):
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def o_line(unit, qty):
    g = Decimal(unit * qty)
    r = Decimal("0.2") if qty >= 50 else (Decimal("0.1") if qty >= 10 else Decimal(0))
    return rc(g * (1 - r))


CHECKS = []


def chk(tag, w, fn):
    CHECKS.append((tag, w, fn))


# =================== COMMERCE ===================
def commerce_build(stock):
    _purge()
    import importlib
    svc = importlib.import_module("marketplace.commerce.service")
    inv = importlib.import_module("marketplace.commerce.inventory")
    store = importlib.import_module("marketplace.commerce.store")
    models = importlib.import_module("marketplace.commerce.models")
    errors = importlib.import_module("marketplace.commerce.errors")
    Product = models.Product
    catalog = {s: Product(s, nm, pr, stock.get(s, 0)) for s, (nm, pr) in CATALOG_SPEC.items()}
    inventory = inv.Inventory(dict(stock))
    st = store.OrderStore()
    return svc.OrderService(catalog, inventory, st), inventory, st, errors


def _pricing():
    return imp("commerce.pricing")


chk("commerce", 2, lambda: _pricing().line_total_cents(100, 3) == 300)
chk("commerce", 2, lambda: _pricing().line_total_cents(100, 10) == 900)
chk("commerce", 2, lambda: _pricing().line_total_cents(100, 9) == 900)
chk("commerce", 2, lambda: _pricing().line_total_cents(100, 50) == 4000)
chk("commerce", 2, lambda: _pricing().line_total_cents(1, 15) == o_line(1, 15))
chk("commerce", 2, lambda: _pricing().coupon_discount_cents(1000, {"type": "pct", "value": 10, "min_spend": 0}) == 100)
chk("commerce", 3, lambda: _pricing().coupon_discount_cents(1000, {"type": "fixed", "value": 500, "min_spend": 2000}) == 0)
chk("commerce", 2, lambda: _pricing().coupon_discount_cents(300, {"type": "fixed", "value": 500, "min_spend": 0}) == 300)
chk("commerce", 2, lambda: _pricing().tax_cents(1005, 0.1) == rc(Decimal(1005) * Decimal("0.1")))


def c_no_oversell():
    _, inv, _, errors = commerce_build({"A": 5})
    try:
        inv.reserve_all({"A": 6}); return False
    except errors.OutOfStockError:
        return inv.available("A") == 5
chk("commerce", 3, c_no_oversell)


def c_atomic_reserve():
    _, inv, _, errors = commerce_build({"A": 5, "B": 0})
    try:
        inv.reserve_all({"A": 2, "B": 1}); return False
    except errors.OutOfStockError:
        return inv.available("A") == 5
chk("commerce", 3, c_atomic_reserve)


def c_unknown_available():
    _, inv, _, errors = commerce_build({"A": 1})
    try:
        inv.available("Z"); return False
    except errors.UnknownSkuError:
        return True
    except Exception:
        return False
chk("commerce", 1, c_unknown_available)


def c_no_mutate():
    _purge()
    import importlib
    invmod = importlib.import_module("marketplace.commerce.inventory")
    stock = {"A": 5}
    invmod.Inventory(stock).reserve_all({"A": 2})
    return stock["A"] == 5
chk("commerce", 2, c_no_mutate)


def c_val(cart):
    svc, _, _, errors = commerce_build({"A": 10, "B": 10})
    try:
        svc.checkout({"request_id": "r", "cart": cart}); return None
    except errors.ValidationError:
        return "VE"
    except Exception as e:
        return type(e).__name__
chk("commerce", 2, lambda: c_val([]) == "VE")
chk("commerce", 2, lambda: c_val([{"sku": "Z", "qty": 1}]) == "VE")
chk("commerce", 2, lambda: c_val([{"sku": "A", "qty": 0}]) == "VE")
chk("commerce", 2, lambda: c_val([{"sku": "A", "qty": -1}]) == "VE")
chk("commerce", 1, lambda: c_val([{"sku": "A", "qty": True}]) == "VE")


def c_dup_merge():
    svc, inv, _, _ = commerce_build({"A": 100})
    r = svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 2}, {"sku": "A", "qty": 3}]})
    return len(r.lines) == 1 and r.lines[0].qty == 5 and inv.available("A") == 95
chk("commerce", 3, c_dup_merge)


def c_idem():
    svc, inv, store, _ = commerce_build({"A": 100})
    req = {"request_id": "d", "cart": [{"sku": "A", "qty": 4}], "tax_rate": 0.0}
    a = svc.checkout(req); b = svc.checkout(req)
    return a.total_cents == b.total_cents and inv.available("A") == 96 and len(store.all()) == 1
chk("commerce", 3, c_idem)


def c_atomic_checkout():
    svc, inv, store, errors = commerce_build({"A": 1})
    try:
        svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 5}]}); ok = False
    except errors.OutOfStockError:
        ok = True
    return ok and inv.available("A") == 1 and len(store.all()) == 0
chk("commerce", 3, c_atomic_checkout)


def c_receipt():
    svc, _, _, _ = commerce_build({"A": 100, "B": 100})
    r = svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 12}, {"sku": "B", "qty": 3}],
                      "coupon": {"type": "pct", "value": 10, "min_spend": 0}, "tax_rate": 0.07})
    sub = o_line(100, 12) + o_line(250, 3)
    disc = rc(Decimal(sub) * Decimal("0.1"))
    tax = rc(Decimal(sub - disc) * Decimal("0.07"))
    return (r.subtotal_cents == sub and r.discount_cents == disc and r.tax_cents == tax
            and r.total_cents == sub - disc + tax)
chk("commerce", 3, c_receipt)


def c_missing_rid():
    svc, _, _, errors = commerce_build({"A": 5})
    try:
        svc.checkout({"cart": [{"sku": "A", "qty": 1}]}); return False
    except errors.ValidationError:
        return True
    except Exception:
        return False
chk("commerce", 1, c_missing_rid)


# --- subtle, un-telegraphed edges (differentiators) ---
def c_coupon_fractional():
    svc, _, _, _ = commerce_build({"A": 100})
    r = svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 3}],
                      "coupon": {"type": "pct", "value": 12.5, "min_spend": 0}})
    return r.discount_cents == rc(Decimal(300) * Decimal("12.5") / 100)  # 37.5 -> 38 half-up
chk("commerce", 2, c_coupon_fractional)


def c_idem_diff_cart():
    # a replayed request_id must return the ORIGINAL receipt even if the cart differs
    svc, inv, store, _ = commerce_build({"A": 100})
    a = svc.checkout({"request_id": "x", "cart": [{"sku": "A", "qty": 2}], "tax_rate": 0})
    b = svc.checkout({"request_id": "x", "cart": [{"sku": "A", "qty": 9}], "tax_rate": 0})
    return a.total_cents == b.total_cents and inv.available("A") == 98 and len(store.all()) == 1
chk("commerce", 3, c_idem_diff_cart)


def c_qty_float_rejected():
    svc, _, _, errors = commerce_build({"A": 100})
    try:
        svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 2.0}]}); return False
    except errors.ValidationError:
        return True
    except Exception:
        return False
chk("commerce", 2, c_qty_float_rejected)


# =================== ACCOUNTS ===================
def _Dir():
    return imp("accounts.directory").Directory


def a_basic():
    D = _Dir(); d = D(); d.add_user({"email": "A@X.com", "name": "Ann"})
    u = d.find_by_email("a@x.com")
    return d.count() == 1 and u is not None and u["name"] == "Ann"


def a_reject_invalid():
    D = _Dir(); d = D()
    for bad in ({"email": "noat", "name": "x"}, {"email": "a@b.com", "name": ""}, {"name": "z"}):
        try:
            d.add_user(bad)
        except Exception:
            pass
    return d.count() == 0


def a_dedup():
    D = _Dir(); d = D(); d.add_user({"email": "d@x.com", "name": "F"})
    try:
        d.add_user({"email": "D@X.com", "name": "S"})
    except Exception:
        pass
    return d.count() == 1


def a_no_mutation():
    D = _Dir(); d = D(); rec = {"email": "Case@X.com", "name": "C"}; d.add_user(rec)
    return rec["email"] == "Case@X.com"


def a_no_leak():
    D = _Dir(); d = D(); d.add_user({"email": "l@x.com", "name": "Leak"})
    lst = d.all_users()
    try:
        lst.clear()
    except Exception:
        pass
    return d.count() == 1 and d.find_by_email("l@x.com")["name"] == "Leak"


def a_trim_email():
    D = _Dir(); d = D(); d.add_user({"email": "  Trim@X.com  ", "name": "T"})
    return d.find_by_email("trim@x.com") is not None and d.count() == 1
chk("accounts", 2, a_trim_email)

chk("accounts", 3, a_basic)
chk("accounts", 3, a_reject_invalid)
chk("accounts", 2, a_dedup)
chk("accounts", 3, a_no_mutation)
chk("accounts", 3, a_no_leak)


# =================== ADMIN (restore, path-traversal) ===================
def _restore():
    return imp("admin.restore").restore_backup


def _mk_targz(path, members):
    with tarfile.open(path, "w:gz") as t:
        for name, payload in members:
            if isinstance(payload, tuple) and payload[0] == "SYM":
                ti = tarfile.TarInfo(name); ti.type = tarfile.SYMTYPE; ti.linkname = payload[1]
                t.addfile(ti)
            else:
                ti = tarfile.TarInfo(name); ti.size = len(payload)
                t.addfile(ti, io.BytesIO(payload))


def ad_legit():
    rb = _restore()
    with tempfile.TemporaryDirectory() as w:
        arc = os.path.join(w, "a.tar.gz")
        _mk_targz(arc, [("a.txt", b"alpha"), ("sub/b.txt", b"bravo")])
        dest = os.path.join(w, "d")
        rb(arc, dest)
        return (open(os.path.join(dest, "a.txt"), "rb").read() == b"alpha"
                and open(os.path.join(dest, "sub", "b.txt"), "rb").read() == b"bravo")


def ad_no_escape(members, canary):
    rb = _restore()
    with tempfile.TemporaryDirectory() as w:
        dest = os.path.join(w, "l1", "l2", "dest"); os.makedirs(dest)
        arc = os.path.join(w, "m.tar.gz"); _mk_targz(arc, members)
        try:
            rb(arc, dest)
        except Exception:
            pass
        return not os.path.exists(os.path.realpath(os.path.join(dest, canary)))


def ad_symlink():
    rb = _restore()
    with tempfile.TemporaryDirectory() as w:
        outside = os.path.join(w, "outside"); os.makedirs(outside)
        dest = os.path.join(w, "dest"); os.makedirs(dest)
        arc = os.path.join(w, "s.tar.gz")
        _mk_targz(arc, [("sneak", ("SYM", outside)), ("sneak/leak.txt", b"pwned")])
        try:
            rb(arc, dest)
        except Exception:
            pass
        return not os.path.exists(os.path.join(outside, "leak.txt"))


def ad_abspath():
    rb = _restore()
    with tempfile.TemporaryDirectory() as w:
        canary = os.path.join(w, "abs_canary.txt")
        arc = os.path.join(w, "a.tar.gz"); _mk_targz(arc, [(canary.lstrip("/"), b"pwn")])
        # craft a truly-absolute member name
        arc2 = os.path.join(w, "b.tar.gz"); _mk_targz(arc2, [("/" + os.path.relpath(canary, "/"), b"pwn")])
        dest = os.path.join(w, "d"); os.makedirs(dest)
        try:
            rb(arc2, dest)
        except Exception:
            pass
        return not os.path.exists(canary)


def ad_empty():
    rb = _restore()
    with tempfile.TemporaryDirectory() as w:
        arc = os.path.join(w, "e.tar.gz"); _mk_targz(arc, [])
        try:
            return rb(arc, os.path.join(w, "d")) == []
        except Exception:
            return False


chk("admin", 3, ad_legit)
chk("admin", 3, lambda: ad_no_escape([("../esc.txt", b"pwn")], "../esc.txt"))
chk("admin", 3, lambda: ad_no_escape([("../../esc2.txt", b"pwn")], "../../esc2.txt"))
chk("admin", 4, ad_symlink)
chk("admin", 3, ad_abspath)
chk("admin", 1, ad_empty)


# =================== PLUGINS (semver) ===================
def _sat():
    return imp("plugins.compat").satisfies


PLUGIN_CASES = [
    ("1.2.3", "1.2.3", True, 1), ("1.5.0", "^1.2.3", True, 1), ("2.0.0", "^1.2.3", False, 1),
    ("0.2.5", "^0.2.3", True, 1), ("0.3.0", "^0.2.3", False, 1), ("1.2.9", "~1.2.3", True, 1),
    ("1.3.0", "~1.2.3", False, 1), ("1.2.9", "1.2.x", True, 1), ("1.3.0", "1.2.x", False, 1),
    ("1.5.0", "1.2.3 - 2.3.4", True, 1), ("2.3.5", "1.2.3 - 2.3.4", False, 1),
    ("2.5.0", "^1.0.0 || ^2.0.0", True, 1),
    ("1.0.0-alpha.1", ">1.0.0-alpha", True, 2), ("1.0.0-rc.1", ">1.0.0-beta.11", True, 2),
    ("1.2.4-alpha", "^1.2.3", False, 3), ("1.0.0-alpha", "<1.0.0", False, 3),
    ("1.2.3-beta.2", ">=1.2.3-beta.1 <1.2.4", True, 3),
    # subtle, un-telegraphed edges (differentiators):
    ("1.2.3+build", "1.2.3", True, 2),                 # build metadata ignored
    ("1.2.3", "^1.2.3-0", True, 2),                     # release satisfies a pre-release floor
    ("2.0.0-alpha", "1.x", False, 3),                   # x-range excludes a prerelease of a diff core
    ("0.0.4", "^0.0.3", False, 2),                      # caret on 0.0.x pins the patch
    ("1.2.3-alpha.2", ">=1.2.3-alpha.1 <1.2.4", True, 3),
]
for _v, _r, _e, _w in PLUGIN_CASES:
    chk("plugins", _w, (lambda v, r, e: (lambda: bool(_sat()(v, r)) == e))(_v, _r, _e))


# =================== ANALYTICS (SQL + report) ===================
def _queries():
    return imp("analytics.queries")


CUSTOMERS = [(1, "Alice", "US"), (2, "Bob", "US"), (3, "Cara", "UK"), (4, "Alice", "CA")]
ORDERS = [(10, 1, "2026-01-01"), (11, 1, "2026-03-01"), (12, 1, "2025-01-01"),
          (20, 2, "2026-02-01"), (30, 3, "2025-06-01"), (40, 4, "2026-05-05")]
LINE_ITEMS = [(100, 10, 2, 500), (101, 10, 1, 300), (102, 11, 3, 100), (103, 12, 5, 999),
              (104, 20, 1, 250), (105, 20, 4, 1000), (106, 20, 2, 50), (107, 30, 1, 100),
              (108, 40, 10, 100)]


def _conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, country TEXT)")
    c.execute("CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, created_at TEXT)")
    c.execute("CREATE TABLE line_items(id INTEGER PRIMARY KEY, order_id INTEGER, qty INTEGER, unit_price INTEGER)")
    c.executemany("INSERT INTO customers VALUES (?,?,?)", CUSTOMERS)
    c.executemany("INSERT INTO orders VALUES (?,?,?)", ORDERS)
    c.executemany("INSERT INTO line_items VALUES (?,?,?,?)", LINE_ITEMS)
    c.commit()
    return c


def _exp_summary(since):
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


chk("analytics", 4, lambda: [tuple(r) for r in _queries().customer_summary(_conn(), "2026-01-01")] == _exp_summary("2026-01-01"))
chk("analytics", 2, lambda: [tuple(r) for r in _queries().customer_summary(_conn(), "2027-01-01")] == [])
chk("analytics", 3, lambda: (lambda q: (lambda rows: rows == [] )(list(q.find_customer(_conn(), "' OR '1'='1"))) if True else False)(_queries()))
chk("analytics", 3, lambda: _sql_injection_summary())


def _sql_injection_summary():
    q = _queries()
    try:
        rows = list(q.customer_summary(_conn(), "9999' OR '1'='1"))
    except Exception:
        return True
    return rows == []


def _report():
    return imp("analytics.report")


class _CountingDB:
    def __init__(self, orders, customers, items):
        self._o, self._c, self._i = orders, customers, items
        self.calls = 0

    def get_order(self, oid):
        self.calls += 1; return dict(self._o[oid])

    def get_orders(self, oids):
        self.calls += 1; return {o: dict(self._o[o]) for o in oids}

    def get_customer(self, cid):
        self.calls += 1; return dict(self._c[cid])

    def get_customers(self, cids):
        self.calls += 1; return {c: dict(self._c[c]) for c in cids}

    def get_item(self, iid):
        self.calls += 1; return dict(self._i[iid])

    def get_items(self, iids):
        self.calls += 1; return {i: dict(self._i[i]) for i in iids}


def _report_dataset(n):
    import random
    rng = random.Random(7)
    customers = {f"c{i}": {"id": f"c{i}", "name": f"Cust {i}"} for i in range(max(3, n // 4))}
    items = {f"i{i}": {"id": f"i{i}", "price": rng.randint(1, 500)} for i in range(max(5, n))}
    orders = {}
    for i in range(n):
        orders[f"o{i}"] = {"id": f"o{i}", "customer_id": rng.choice(list(customers)),
                           "item_ids": rng.sample(list(items), rng.randint(1, 3))}
    return orders, customers, items


def r_correct():
    o, c, i = _report_dataset(15)
    ids = list(o)
    got = list(_report().order_report(_CountingDB(o, c, i), ids))
    exp = [(oid, c[o[oid]["customer_id"]]["name"], sum(i[x]["price"] for x in o[oid]["item_ids"])) for oid in ids]
    return got == exp


def r_efficient():
    o, c, i = _report_dataset(120)
    db = _CountingDB(o, c, i)
    _report().order_report(db, list(o))
    return db.calls <= 9   # O(1) batched (ref uses 3); N+1 would be ~360+
chk("analytics", 2, r_correct)
chk("analytics", 4, r_efficient)


def main():
    by = {}
    passW = totW = 0.0
    for tag, w, fn in CHECKS:
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
