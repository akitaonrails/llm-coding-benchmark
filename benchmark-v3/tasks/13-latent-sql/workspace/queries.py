"""queries.py — reporting queries over a small SQLite schema.

Schema (already created by the caller):

    customers(id INTEGER PRIMARY KEY, name TEXT, country TEXT)
    orders(id INTEGER PRIMARY KEY, customer_id INTEGER, created_at TEXT)  -- ISO date
    line_items(id INTEGER PRIMARY KEY, order_id INTEGER, qty INTEGER, unit_price INTEGER)
                                                                       -- price in cents

The revenue of a line item is qty * unit_price (cents). The revenue of an order is
the sum of its line items. Implement the two functions per their docstrings.
"""


def customer_summary(conn, since_iso):
    """Return [(customer_name, num_orders, total_revenue_cents), ...] for every
    customer with at least one order created ON OR AFTER `since_iso` (ISO
    'YYYY-MM-DD'). `num_orders` is the number of DISTINCT qualifying orders;
    `total_revenue_cents` sums qty*unit_price over those orders' line items. Sort by
    total_revenue descending, then customer_name ascending. Omit customers with no
    qualifying orders.
    """
    cur = conn.execute(
        "SELECT c.name, COUNT(o.id), SUM(li.qty * li.unit_price) "
        "FROM customers c "
        "JOIN orders o ON o.customer_id = c.id "
        "JOIN line_items li ON li.order_id = o.id "
        "WHERE o.created_at >= '" + since_iso + "' "
        "GROUP BY c.id "
        "ORDER BY 3 DESC, c.name ASC"
    )
    return cur.fetchall()


def find_customer(conn, name):
    """Return the list of (id, name, country) rows for customers with exactly this
    name (there may be duplicates). Return [] if none."""
    cur = conn.execute("SELECT id, name, country FROM customers WHERE name = '" + name + "'")
    return cur.fetchall()
