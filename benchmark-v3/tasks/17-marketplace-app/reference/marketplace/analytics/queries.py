"""Reference: correct aggregation (no join fan-out) and parameterized queries."""


def customer_summary(conn, since_iso):
    cur = conn.execute(
        "SELECT c.name, COUNT(DISTINCT o.id), "
        "       COALESCE(SUM(li.qty * li.unit_price), 0) "
        "FROM customers c "
        "JOIN orders o ON o.customer_id = c.id "
        "JOIN line_items li ON li.order_id = o.id "
        "WHERE o.created_at >= ? "
        "GROUP BY c.id "
        "ORDER BY 3 DESC, c.name ASC",
        (since_iso,),
    )
    return cur.fetchall()


def find_customer(conn, name):
    cur = conn.execute(
        "SELECT id, name, country FROM customers WHERE name = ?", (name,)
    )
    return cur.fetchall()
