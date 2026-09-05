"""Cart validation. Merges duplicate SKUs, rejects malformed carts.

NOTE: this starter is incomplete and has bugs. Make it correct.
"""
from .models import CartItem


def normalize_cart(cart, catalog):
    """Validate and normalize a cart. See the reference contract in the docstring of
    the correct version: empty cart and unknown sku and non-positive/non-int qty are
    errors; duplicate SKUs are merged."""
    items = []
    for raw in cart:
        sku = raw.sku if isinstance(raw, CartItem) else raw["sku"]
        qty = raw.qty if isinstance(raw, CartItem) else raw["qty"]
        items.append(CartItem(sku, qty))
    return items
