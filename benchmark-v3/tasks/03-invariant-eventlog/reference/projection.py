"""Reference solution: buffer by seq, dedup, apply the contiguous prefix in order."""


class Projection:
    def __init__(self):
        self._buf = {}          # seq -> event (dedup: first/any occurrence)
        self._next = 0          # next contiguous seq not yet applied
        self._balance = 0

    def apply(self, event):
        seq = event["seq"]
        if seq in self._buf or seq < self._next:
            return  # idempotent: already seen (buffered or already applied)
        self._buf[seq] = event
        # Advance the contiguous frontier, applying in seq order.
        while self._next in self._buf:
            self._apply_one(self._buf.pop(self._next))
            self._next += 1

    def _apply_one(self, event):
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
