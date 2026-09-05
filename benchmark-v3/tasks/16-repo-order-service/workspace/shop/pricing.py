"""Pricing rules: line totals with bulk discounts, coupons, tax.

Rules:
  * line total = unit_price * qty, with a per-line bulk discount: qty >= 50 -> 20% off
    that line; else qty >= 10 -> 10% off that line. Rounded half-up to cents.
  * subtotal = sum of line totals.
  * coupon (optional): {"type":"pct","value":P,"min_spend":M} takes P% off the subtotal;
    {"type":"fixed","value":C,"min_spend":M} takes C cents off. Applied ONLY if
    subtotal >= min_spend; a pct discount never exceeds the subtotal, a fixed discount
    never exceeds the subtotal. Otherwise no discount (coupon_applied False).
  * tax applies to (subtotal - discount), rounded half-up to cents.
  * total = subtotal - discount + tax.

NOTE: this starter is incomplete and has bugs. Make it correct.
"""


def line_total_cents(unit_price_cents, qty):
    total = unit_price_cents * qty
    if qty > 10:
        total = int(total * 0.9)
    return total


def coupon_discount_cents(subtotal_cents, coupon):
    if not coupon:
        return 0
    if coupon["type"] == "pct":
        return int(subtotal_cents * coupon["value"] / 100)
    return coupon["value"]


def tax_cents(taxable_cents, tax_rate):
    return int(taxable_cents * tax_rate)
