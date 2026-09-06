"""Cart validation. Merges duplicate SKUs, rejects malformed carts."""
from .errors import ValidationError, UnknownSkuError
from .models import CartItem


def normalize_cart(cart, catalog: dict) -> list:
    """Validate and normalize a cart (list of CartItem or {sku,qty} dicts).

    - empty cart -> ValidationError
    - unknown sku -> UnknownSkuError
    - qty not a positive int -> ValidationError
    - duplicate SKUs are MERGED (quantities summed), order of first appearance kept.
    Returns a list of CartItem with unique SKUs.
    """
    if not cart:
        raise ValidationError("empty cart")
    merged = {}
    order = []
    for raw in cart:
        sku = raw.sku if isinstance(raw, CartItem) else raw.get("sku")
        qty = raw.qty if isinstance(raw, CartItem) else raw.get("qty")
        if sku not in catalog:
            raise UnknownSkuError(str(sku))
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
            raise ValidationError(f"bad qty for {sku}: {qty!r}")
        if sku not in merged:
            order.append(sku)
            merged[sku] = 0
        merged[sku] += qty
    return [CartItem(sku, merged[sku]) for sku in order]
