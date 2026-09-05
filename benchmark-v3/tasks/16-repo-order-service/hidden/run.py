#!/usr/bin/env python3
"""Hidden runner for 16-repo-order-service. Continuous score (0-100).

Repository-scale task: a 6-module `shop` package. The score is the weighted fraction
of ~30 INDEPENDENT checks spanning pricing, inventory, validation, idempotency,
atomicity, and receipt consistency — many requiring correct behaviour ACROSS files.
Expected values come from an independent oracle here (never the candidate's code).
Each check re-imports the package fresh (hermetic vs class-level state).

Emits ONE json line: {"score": float, "breakdown": {...}}  (or load_error).
"""
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = str(Path(sys.argv[1]).resolve().parent.parent)  # dir containing shop/
CATALOG_SPEC = {"A": ("Apple", 100), "B": ("Banana", 250), "C": ("Cherry", 999)}


def fresh():
    for m in list(sys.modules):
        if m == "shop" or m.startswith("shop."):
            del sys.modules[m]
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import shop.errors, shop.inventory, shop.models, shop.service, shop.store, shop.validation  # noqa
    return shop


def build(shop, stock):
    Product = shop.models.Product
    catalog = {sku: Product(sku, nm, pr, stock.get(sku, 0)) for sku, (nm, pr) in CATALOG_SPEC.items()}
    inv = shop.inventory.Inventory(dict(stock))
    store = shop.store.OrderStore()
    svc = shop.service.OrderService(catalog, inv, store)
    return svc, inv, store


# ---- independent oracle ----
def rc(d):
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def o_line(unit, qty):
    g = Decimal(unit * qty)
    r = Decimal("0.2") if qty >= 50 else (Decimal("0.1") if qty >= 10 else Decimal(0))
    return rc(g * (1 - r))


def main():
    checks = []

    def chk(tag, w, fn):
        checks.append((tag, w, fn))

    # ---------------- pricing ----------------
    chk("pricing", 2, lambda: fresh().pricing.line_total_cents(100, 3) == 300)
    chk("pricing", 2, lambda: fresh().pricing.line_total_cents(100, 10) == 900)   # >=10 -> 10%
    chk("pricing", 2, lambda: fresh().pricing.line_total_cents(100, 9) == 900)    # 9 -> no disc (900)
    chk("pricing", 2, lambda: fresh().pricing.line_total_cents(100, 50) == 4000)  # >=50 -> 20%
    chk("pricing", 2, lambda: fresh().pricing.line_total_cents(1, 15) == o_line(1, 15))  # 13.5->14 half-up
    chk("pricing", 2, lambda: fresh().pricing.coupon_discount_cents(1000, {"type": "pct", "value": 10, "min_spend": 0}) == 100)
    chk("pricing", 3, lambda: fresh().pricing.coupon_discount_cents(1000, {"type": "fixed", "value": 500, "min_spend": 2000}) == 0)  # min not met
    chk("pricing", 2, lambda: fresh().pricing.coupon_discount_cents(300, {"type": "fixed", "value": 500, "min_spend": 0}) == 300)  # capped
    chk("pricing", 1, lambda: fresh().pricing.coupon_discount_cents(5000, {"type": "fixed", "value": 500, "min_spend": 3000}) == 500)
    chk("pricing", 2, lambda: fresh().pricing.tax_cents(1005, 0.1) == rc(Decimal(1005) * Decimal("0.1")))  # 100.5->101 half-up

    # ---------------- inventory ----------------
    def no_oversell():
        shop = fresh(); _, inv, _ = build(shop, {"A": 5})
        try:
            inv.reserve_all({"A": 6})
            return False
        except shop.errors.OutOfStockError:
            return inv.available("A") == 5
    chk("inventory", 3, no_oversell)

    def exact_then_over():
        shop = fresh(); _, inv, _ = build(shop, {"A": 5})
        inv.reserve_all({"A": 5})
        try:
            inv.reserve_all({"A": 1}); return False
        except shop.errors.OutOfStockError:
            return inv.available("A") == 0
    chk("inventory", 2, exact_then_over)

    def atomic_reserve():
        shop = fresh(); _, inv, _ = build(shop, {"A": 5, "B": 0})
        try:
            inv.reserve_all({"A": 2, "B": 1}); return False
        except shop.errors.OutOfStockError:
            return inv.available("A") == 5  # A NOT decremented (all-or-nothing)
    chk("inventory", 3, atomic_reserve)

    def unknown_available():
        shop = fresh(); _, inv, _ = build(shop, {"A": 1})
        try:
            inv.available("Z"); return False
        except shop.errors.UnknownSkuError:
            return True
        except Exception:
            return False
    chk("inventory", 1, unknown_available)

    def no_mutate_caller():
        shop = fresh()
        stock = {"A": 5}
        inv = shop.inventory.Inventory(stock)
        inv.reserve_all({"A": 2})
        return stock["A"] == 5  # caller's dict untouched
    chk("inventory", 2, no_mutate_caller)

    # ---------------- validation ----------------
    def val_err(cart):
        shop = fresh(); svc, _, _ = build(shop, {"A": 10, "B": 10})
        try:
            svc.checkout({"request_id": "r", "cart": cart}); return None
        except shop.errors.ValidationError:
            return "VE"
        except Exception as e:
            return type(e).__name__
    chk("validation", 2, lambda: val_err([]) == "VE")                                  # empty
    chk("validation", 2, lambda: val_err([{"sku": "Z", "qty": 1}]) == "VE")            # unknown (UnknownSku<:VE)
    chk("validation", 2, lambda: val_err([{"sku": "A", "qty": 0}]) == "VE")            # zero
    chk("validation", 2, lambda: val_err([{"sku": "A", "qty": -1}]) == "VE")           # negative
    chk("validation", 1, lambda: val_err([{"sku": "A", "qty": True}]) == "VE")         # bool qty

    def dup_merge():
        shop = fresh(); svc, inv, _ = build(shop, {"A": 100})
        r = svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 2}, {"sku": "A", "qty": 3}]})
        return len(r.lines) == 1 and r.lines[0].qty == 5 and inv.available("A") == 95
    chk("validation", 3, dup_merge)

    # ---------------- idempotency ----------------
    def replay_same():
        shop = fresh(); svc, _, _ = build(shop, {"A": 100})
        req = {"request_id": "dup1", "cart": [{"sku": "A", "qty": 2}], "tax_rate": 0.0}
        a = svc.checkout(req); b = svc.checkout(req)
        return a.total_cents == b.total_cents and a.request_id == b.request_id
    chk("idempotency", 3, replay_same)

    def replay_no_double_decrement():
        shop = fresh(); svc, inv, store = build(shop, {"A": 100})
        req = {"request_id": "dup2", "cart": [{"sku": "A", "qty": 4}], "tax_rate": 0.0}
        svc.checkout(req); svc.checkout(req)
        return inv.available("A") == 96 and len(store.all()) == 1
    chk("idempotency", 3, replay_no_double_decrement)

    # ---------------- atomicity ----------------
    def atomic_checkout_oos():
        shop = fresh(); svc, inv, store = build(shop, {"A": 1})
        try:
            svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 5}]}); ok = False
        except shop.errors.OutOfStockError:
            ok = True
        return ok and inv.available("A") == 1 and len(store.all()) == 0  # nothing changed
    chk("atomicity", 3, atomic_checkout_oos)

    def atomic_checkout_unknown():
        shop = fresh(); svc, inv, store = build(shop, {"A": 5})
        try:
            svc.checkout({"request_id": "r", "cart": [{"sku": "Z", "qty": 1}]})
        except shop.errors.ValidationError:
            pass
        except Exception:
            return False
        return inv.available("A") == 5 and len(store.all()) == 0
    chk("atomicity", 2, atomic_checkout_unknown)

    # ---------------- receipt consistency ----------------
    def receipt_totals():
        shop = fresh(); svc, _, _ = build(shop, {"A": 100, "B": 100})
        r = svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 12}, {"sku": "B", "qty": 3}],
                          "coupon": {"type": "pct", "value": 10, "min_spend": 0}, "tax_rate": 0.07})
        exp_sub = o_line(100, 12) + o_line(250, 3)
        exp_disc = rc(Decimal(exp_sub) * Decimal("0.1"))
        exp_tax = rc(Decimal(exp_sub - exp_disc) * Decimal("0.07"))
        return (r.subtotal_cents == exp_sub and r.discount_cents == exp_disc
                and r.tax_cents == exp_tax and r.total_cents == exp_sub - exp_disc + exp_tax
                and sum(l.line_total_cents for l in r.lines) == exp_sub)
    chk("receipt", 3, receipt_totals)

    def coupon_flag():
        shop = fresh(); svc, _, _ = build(shop, {"A": 100})
        r = svc.checkout({"request_id": "r", "cart": [{"sku": "A", "qty": 1}],
                          "coupon": {"type": "fixed", "value": 500, "min_spend": 999999}})
        return r.coupon_applied is False and r.discount_cents == 0
    chk("receipt", 1, coupon_flag)

    def missing_request_id():
        shop = fresh(); svc, _, _ = build(shop, {"A": 5})
        try:
            svc.checkout({"cart": [{"sku": "A", "qty": 1}]}); return False
        except shop.errors.ValidationError:
            return True
        except Exception:
            return False
    chk("receipt", 1, missing_request_id)

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
