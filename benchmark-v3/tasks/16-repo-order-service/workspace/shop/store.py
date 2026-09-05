"""Order persistence with idempotency by request_id.

NOTE: this starter is incomplete and has bugs. Make it correct.
"""


class OrderStore:
    def __init__(self):
        self._orders = []

    def get(self, request_id):
        return None

    def save(self, receipt):
        self._orders.append(receipt)

    def all(self):
        return self._orders
