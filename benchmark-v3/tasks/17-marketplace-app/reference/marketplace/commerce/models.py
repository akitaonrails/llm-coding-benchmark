"""Domain models for the order service."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    unit_price_cents: int
    stock: int


@dataclass(frozen=True)
class CartItem:
    sku: str
    qty: int


@dataclass
class ReceiptLine:
    sku: str
    qty: int
    unit_price_cents: int
    line_total_cents: int


@dataclass
class Receipt:
    request_id: str
    lines: list = field(default_factory=list)
    subtotal_cents: int = 0
    discount_cents: int = 0
    tax_cents: int = 0
    total_cents: int = 0
    coupon_applied: bool = False
