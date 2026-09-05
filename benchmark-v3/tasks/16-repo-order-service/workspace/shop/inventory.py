"""Inventory: stock levels with atomic multi-line reservation (no overselling).

NOTE: this starter is incomplete and has bugs. Make it correct.
"""
from .errors import OutOfStockError


class Inventory:
    def __init__(self, stock):
        self._stock = stock

    def available(self, sku):
        return self._stock[sku]

    def reserve_all(self, needs):
        # reserve each sku
        for sku, qty in needs.items():
            self._stock[sku] -= qty

    def release(self, needs):
        for sku, qty in needs.items():
            self._stock[sku] += qty
