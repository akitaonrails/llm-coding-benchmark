"""Event-sourced account-balance projection.

Events arrive via apply() from an at-least-once delivery channel: they may be
duplicated, arrive out of order, and arrive with gaps (a later seq before an
earlier one). See TASK.md for the exact contract.

NAIVE STARTER — it applies every event immediately in arrival order, with no
buffering and no dedup. It is wrong under reordering, gaps, and redelivery.
"""


class Projection:
    def __init__(self):
        self._balance = 0

    def apply(self, event):
        t = event["type"]
        if t == "open":
            self._balance = 0
        elif t == "deposit":
            self._balance += event["amount"]
        elif t == "withdraw":
            if self._balance >= event["amount"]:
                self._balance -= event["amount"]

    def balance(self):
        return self._balance
