"""Order persistence with idempotency by request_id."""


class OrderStore:
    def __init__(self):
        self._by_request = {}   # request_id -> Receipt
        self._order = []        # request_ids in insertion order

    def get(self, request_id: str):
        return self._by_request.get(request_id)

    def save(self, receipt) -> None:
        if receipt.request_id not in self._by_request:
            self._order.append(receipt.request_id)
        self._by_request[receipt.request_id] = receipt

    def all(self) -> list:
        return [self._by_request[r] for r in self._order]
