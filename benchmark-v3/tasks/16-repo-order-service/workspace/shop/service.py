"""OrderService.checkout — orchestrates validation, pricing, inventory, persistence.

checkout(request) must be ATOMIC and IDEMPOTENT (see the correct contract):
  * request = {"request_id": str, "cart": [...], "coupon": {..}|None, "tax_rate": float}
  * idempotent: a repeated request_id returns the SAME receipt without re-decrementing.
  * atomic: on any failure, NO stock is decremented and NO order is persisted.
  * returns a Receipt; raises on validation / stock errors.

NOTE: this starter is incomplete and has bugs. Make it correct.
"""
from . import pricing
from .models import Receipt, ReceiptLine
from .validation import normalize_cart


class OrderService:
    def __init__(self, catalog, inventory, store):
        self.catalog = catalog
        self.inventory = inventory
        self.store = store

    def checkout(self, request):
        items = normalize_cart(request["cart"], self.catalog)
        needs = {it.sku: it.qty for it in items}
        # decrement stock
        self.inventory.reserve_all(needs)
        lines = []
        subtotal = 0
        for it in items:
            p = self.catalog[it.sku]
            lt = pricing.line_total_cents(p.unit_price_cents, it.qty)
            lines.append(ReceiptLine(it.sku, it.qty, p.unit_price_cents, lt))
            subtotal += lt
        discount = pricing.coupon_discount_cents(subtotal, request.get("coupon"))
        tax = pricing.tax_cents(subtotal - discount, request.get("tax_rate", 0.0))
        receipt = Receipt(
            request_id=request.get("request_id"), lines=lines, subtotal_cents=subtotal,
            discount_cents=discount, tax_cents=tax, total_cents=subtotal - discount + tax,
            coupon_applied=discount > 0,
        )
        self.store.save(receipt)
        return receipt
