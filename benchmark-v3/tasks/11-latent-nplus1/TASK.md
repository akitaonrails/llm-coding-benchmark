# Task 11 — Order report

**Category:** implementation · **Language:** Python · **Scoring:** continuous (0–100)

`report.py` builds an order report from the data layer in `db.py`. Implement
`order_report(db, order_ids)` so it returns a list of
`(order_id, customer_name, order_total)` tuples — one per id in `order_ids`, in the
**same order** as `order_ids`. `order_total` is the sum of the prices of the order's
items. You may assume every id is valid.

Read `db.py` for the available accessors. Standard library only. Keep the signature.
Edit `report.py` in place.

The report is used on requests ranging from a handful of orders to very large
batches. Your solution is graded on a spectrum by a hidden test suite over a range
of inputs — make it correct and well-suited to that range, not just the happy path.
