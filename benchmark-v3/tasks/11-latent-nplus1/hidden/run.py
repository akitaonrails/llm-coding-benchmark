#!/usr/bin/env python3
"""Hidden runner for 11-latent-nplus1. Continuous score (0-100).

The prompt is purely functional; it never says "be efficient". Correctness is a
GATE; the spectrum is ROUND-TRIP COUNT (deterministic, machine-independent). A naive
N+1 implementation is correct but issues O(N) round-trips and scores low; a properly
batched implementation issues O(1) and scores ~100.

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error).
"""
import importlib.util
import json
import random
import sys


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CountingDB:
    def __init__(self, orders, customers, items):
        self._o, self._c, self._i = orders, customers, items
        self.calls = 0

    def get_order(self, oid):
        self.calls += 1
        return dict(self._o[oid])

    def get_orders(self, oids):
        self.calls += 1
        return {oid: dict(self._o[oid]) for oid in oids}

    def get_customer(self, cid):
        self.calls += 1
        return dict(self._c[cid])

    def get_customers(self, cids):
        self.calls += 1
        return {cid: dict(self._c[cid]) for cid in cids}

    def get_item(self, iid):
        self.calls += 1
        return dict(self._i[iid])

    def get_items(self, iids):
        self.calls += 1
        return {iid: dict(self._i[iid]) for iid in iids}


def make_dataset(n_orders, seed):
    rng = random.Random(seed)
    customers = {f"c{i}": {"id": f"c{i}", "name": f"Customer {i}"} for i in range(max(3, n_orders // 4))}
    items = {f"i{i}": {"id": f"i{i}", "price": rng.randint(1, 500)} for i in range(max(5, n_orders))}
    orders = {}
    for i in range(n_orders):
        cid = rng.choice(list(customers))
        iids = rng.sample(list(items), rng.randint(1, 3))
        orders[f"o{i}"] = {"id": f"o{i}", "customer_id": cid, "item_ids": iids}
    return orders, customers, items


def expected(orders, customers, items, order_ids):
    out = []
    for oid in order_ids:
        o = orders[oid]
        total = sum(items[iid]["price"] for iid in o["item_ids"])
        out.append((oid, customers[o["customer_id"]]["name"], total))
    return out


def main():
    m = load(sys.argv[1], "cand_report")

    # ---- correctness gate (several datasets + edges) ----
    corr_total = corr_pass = 0
    for seed in range(6):
        orders, customers, items = make_dataset(10 + seed * 5, seed)
        ids = list(orders)
        random.Random(seed).shuffle(ids)
        corr_total += 1
        try:
            got = list(m.order_report(CountingDB(orders, customers, items), ids))
            if got == expected(orders, customers, items, ids):
                corr_pass += 1
        except Exception:
            pass
    # edges: empty, duplicate id, order preserved
    o, c, i = make_dataset(8, 99)
    for ids in ([], [list(o)[0], list(o)[0]], list(reversed(list(o)))):
        corr_total += 1
        try:
            if list(m.order_report(CountingDB(o, c, i), ids)) == expected(o, c, i, ids):
                corr_pass += 1
        except Exception:
            pass
    correct = corr_pass == corr_total

    # ---- efficiency: round-trip count on a large request ----
    orders, customers, items = make_dataset(120, 4321)
    ids = list(orders)
    db = CountingDB(orders, customers, items)
    cand_q = None
    try:
        m.order_report(db, ids)
        cand_q = db.calls
    except Exception:
        cand_q = None

    ref_q = 3  # orders + customers + items, batched
    if not correct or cand_q is None:
        score = round(25.0 * corr_pass / corr_total, 1)
        eff = 0.0
    else:
        # O(1) round-trips (<= ~3x reference) => full marks; O(N) => low, smoothly.
        eff = round(100.0 * max(0.0, min(1.0, (ref_q * 3) / cand_q)), 1)
        score = eff

    print(json.dumps({
        "score": score,
        "breakdown": {
            "correctness": f"{corr_pass}/{corr_total}",
            "round_trips_for_120_orders": cand_q,
            "reference_round_trips": ref_q,
            "efficiency": eff,
        },
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"load_error": f"runner crashed: {e}", "score": None}))
