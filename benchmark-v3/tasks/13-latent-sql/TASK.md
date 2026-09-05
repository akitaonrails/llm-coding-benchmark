# Task 13 — Reporting queries (SQLite)

**Category:** database · **Language:** Python (sqlite3) · **Scoring:** continuous (0–100)

`queries.py` runs two reporting queries over a small SQLite schema (see the module
docstring for the tables). Implement both functions per their docstrings:

- `customer_summary(conn, since_iso)` → `[(customer_name, num_orders, total_revenue_cents), ...]`
  for customers with orders on or after `since_iso`. `num_orders` is the number of
  distinct qualifying orders; `total_revenue_cents` sums `qty*unit_price` over those
  orders' line items. Sort by revenue desc, then name asc. Omit customers with none.
- `find_customer(conn, name)` → the `(id, name, country)` rows whose name matches
  exactly (duplicates possible), or `[]`.

Standard library only (`sqlite3`). Keep the signatures. Edit `queries.py` in place.
The functions run against real production data and untrusted inputs; your solution is
graded on a spectrum by a hidden suite over a range of inputs — make the queries
correct and robust in general, not just on the simplest data.
