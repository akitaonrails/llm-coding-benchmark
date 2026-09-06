"""OrderService.checkout — orchestrates validation, pricing, inventory, persistence.

This is the cross-file hub. checkout(request) must be ATOMIC and IDEMPOTENT:
  * request = {"request_id": str, "cart": [...], "coupon": {..}|None, "tax_rate": float}
  * idempotent: a repeated request_id returns the SAME receipt and does not decrement
    stock again.
  * atomic: if validation fails, or any line is out of stock, NO stock is decremented
    and NO order is persisted (all-or-nothing).
  * returns a Receipt; raises ValidationError / UnknownSkuError / OutOfStockError.
"""
from . import pricing
from .models import Receipt, ReceiptLine
from .validation import normalize_cart


class OrderService:
    def __init__(self, catalog: dict, inventory, store):
        self.catalog = catalog          # sku -> Product
        self.inventory = inventory
        self.store = store

    def checkout(self, request: dict) -> Receipt:
        request_id = request.get("request_id")
        if not request_id:
            from .errors import ValidationError
            raise ValidationError("missing request_id")

        prior = self.store.get(request_id)
        if prior is not None:
            return prior  # idempotent replay — no re-charge, no re-decrement

        # validate + normalize FIRST (no side effects yet)
        items = normalize_cart(request.get("cart"), self.catalog)
        needs = {it.sku: it.qty for it in items}

        # reserve stock atomically (raises before any persistence)
        self.inventory.reserve_all(needs)
        try:
            lines = []
            subtotal = 0
            for it in items:
                p = self.catalog[it.sku]
                lt = pricing.line_total_cents(p.unit_price_cents, it.qty)
                lines.append(ReceiptLine(it.sku, it.qty, p.unit_price_cents, lt))
                subtotal += lt
            coupon = request.get("coupon")
            discount = pricing.coupon_discount_cents(subtotal, coupon)
            taxable = subtotal - discount
            tax = pricing.tax_cents(taxable, request.get("tax_rate", 0.0))
            receipt = Receipt(
                request_id=request_id, lines=lines, subtotal_cents=subtotal,
                discount_cents=discount, tax_cents=tax, total_cents=taxable + tax,
                coupon_applied=discount > 0,
            )
        except Exception:
            self.inventory.release(needs)  # roll back the reservation on any failure
            raise
        self.store.save(receipt)
        return receipt
