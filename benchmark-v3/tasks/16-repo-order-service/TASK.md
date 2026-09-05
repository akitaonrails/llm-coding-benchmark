# Task 16 — Order service (repository-scale)

**Category:** repository-scale · **Language:** Python · **Scoring:** continuous (0–100)

`shop/` is a small order-service package spread across several modules. The happy path
roughly works, but the implementation is **incomplete and buggy across files**. Make the
whole package correct and **production-ready**.

Modules and their contracts (read each module's docstring — it is the spec):

- `shop/models.py` — data classes (`Product`, `CartItem`, `ReceiptLine`, `Receipt`).
- `shop/errors.py` — the exception types you should raise.
- `shop/pricing.py` — line totals with **bulk discounts**, **coupons** (percent / fixed,
  with a minimum-spend threshold and caps), and **tax**. Monetary math is in integer
  **cents** and must round correctly (no binary-float drift).
- `shop/inventory.py` — stock with **atomic, all-or-nothing** multi-line reservation
  (**never oversell**).
- `shop/validation.py` — validate and normalize a cart.
- `shop/store.py` — persist orders with **idempotency** by `request_id`.
- `shop/service.py` — `OrderService.checkout(request)` orchestrates the above. It must be
  **atomic** (on any failure, no stock is decremented and no order is stored) and
  **idempotent** (a repeated `request_id` returns the same receipt without charging or
  decrementing again).

`request = {"request_id": str, "cart": [ {"sku","qty"} | CartItem ], "coupon": {...}|None,
"tax_rate": float}`. `checkout` returns a `Receipt` or raises the appropriate error.

Standard library only. Keep the public class/function names and signatures. Edit the files
in place (do not create a second copy of the package). Your solution is graded on a
spectrum by a hidden suite of many independent checks covering correctness AND robustness
across all the modules — make it correct in general, not just on the happy path.
