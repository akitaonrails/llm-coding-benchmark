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
"""
from decimal import Decimal, ROUND_HALF_UP


def _round_cents(d: Decimal) -> int:
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def line_total_cents(unit_price_cents: int, qty: int) -> int:
    gross = Decimal(unit_price_cents) * qty
    if qty >= 50:
        rate = Decimal("0.20")
    elif qty >= 10:
        rate = Decimal("0.10")
    else:
        rate = Decimal("0")
    return _round_cents(gross * (1 - rate))


def coupon_discount_cents(subtotal_cents: int, coupon: dict | None) -> int:
    if not coupon:
        return 0
    if subtotal_cents < coupon.get("min_spend", 0):
        return 0
    ctype = coupon.get("type")
    if ctype == "pct":
        disc = _round_cents(Decimal(subtotal_cents) * Decimal(str(coupon["value"])) / 100)
    elif ctype == "fixed":
        disc = int(coupon["value"])
    else:
        return 0
    return max(0, min(disc, subtotal_cents))


def tax_cents(taxable_cents: int, tax_rate: float) -> int:
    return _round_cents(Decimal(taxable_cents) * Decimal(str(tax_rate)))
