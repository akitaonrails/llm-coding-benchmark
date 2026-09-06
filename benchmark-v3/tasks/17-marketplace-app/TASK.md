# Task 17 — Marketplace backend (app simulation)

**Category:** app-simulation · **Language:** Python · **Scoring:** continuous (0–100)

`marketplace/` is a small backend for an online marketplace. It is under active
development: the happy paths roughly work, but the codebase is **incomplete and buggy
across several modules**. You are the engineer picking up the project — make it correct
and **production-ready**, working the backlog below. Read each module's docstring; the
docstring is the contract.

## The app

- `marketplace/commerce/` — core checkout. `service.OrderService.checkout(request)`
  orchestrates cart validation, pricing (bulk discounts, coupons with a minimum-spend
  threshold and caps, tax), atomic stock reservation (**never oversell**, all-or-nothing),
  and persistence with **idempotency** by `request_id`. Money is integer cents and must
  round correctly.
- `marketplace/accounts/directory.py` — the user directory (`Directory`): register and
  look up users; must validate input, dedupe emails case-insensitively, and not leak or
  mutate internal state.
- `marketplace/admin/restore.py` — `restore_backup(archive_path, dest_dir)` restores a
  `.tar.gz` backup into a directory and returns the restored file paths.
- `marketplace/plugins/compat.py` — `satisfies(version, range_spec)` decides whether an
  installed plugin version satisfies a required npm-style version range.
- `marketplace/analytics/` — reporting. `queries.py` runs SQL reports over the orders
  database (`customer_summary`, `find_customer`); `report.py`'s `order_report(db, order_ids)`
  builds an order report from the data layer in `db.py`. Reports run on large inputs.

## The backlog (make all of it production-ready)

1. **Checkout is unreliable** — orders can oversell stock, totals are wrong on bulk and
   coupon edge cases, and repeated requests double-charge. Fix the commerce flow end to end.
2. **The user directory** accepts junk and leaks internal state — harden it.
3. **Admin restore** must safely handle backup archives from untrusted sources.
4. **Plugin compatibility** must correctly resolve the full range syntax, including
   pre-release versions.
5. **Analytics** reports must be correct on real data and must not fall over on large
   inputs or hostile parameters.

Standard library only. Keep all public class/function names and signatures. Edit the files
in place — do not create a second copy of the package. You are graded on a spectrum by a
hidden suite of many independent checks across all modules, covering correctness AND
robustness — make it correct in general, not merely on the obvious happy path.
