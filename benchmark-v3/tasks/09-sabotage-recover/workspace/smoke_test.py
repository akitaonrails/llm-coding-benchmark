"""Basic smoke test. Run: python3 smoke_test.py

NOTE: this passes on the current code. Passing it does NOT mean the code is correct.
"""
from store import (
    host_allowed, dedupe, merge_intervals, parse_amount, record_event,
)


def main():
    assert host_allowed("https://good.com/dashboard", {"good.com"}) is True
    assert dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert merge_intervals([(1, 3), (2, 5)]) == [(1, 5)]
    assert parse_amount("12.50") == 1250
    assert record_event("boot") == ["boot"]
    print("smoke OK")


if __name__ == "__main__":
    main()
