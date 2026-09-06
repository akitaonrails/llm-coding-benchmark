"""Exception types for the order service."""


class ShopError(Exception):
    """Base class for all order-service errors."""


class ValidationError(ShopError):
    pass


class OutOfStockError(ShopError):
    pass


class UnknownSkuError(ValidationError):
    pass
