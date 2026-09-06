"""Inventory: stock levels with atomic multi-line reservation (no overselling)."""
from .errors import OutOfStockError, UnknownSkuError


class Inventory:
    def __init__(self, stock: dict):
        self._stock = dict(stock)  # sku -> units

    def available(self, sku: str) -> int:
        if sku not in self._stock:
            raise UnknownSkuError(sku)
        return self._stock[sku]

    def reserve_all(self, needs: dict):
        """Atomically reserve {sku: qty}. If ANY sku lacks stock, reserve NOTHING and
        raise OutOfStockError. Returns nothing; on success stock is decremented."""
        for sku, qty in needs.items():
            if sku not in self._stock:
                raise UnknownSkuError(sku)
            if self._stock[sku] < qty:
                raise OutOfStockError(sku)
        for sku, qty in needs.items():
            self._stock[sku] -= qty

    def release(self, needs: dict):
        for sku, qty in needs.items():
            if sku in self._stock:
                self._stock[sku] += qty
