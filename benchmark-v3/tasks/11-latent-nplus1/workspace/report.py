"""report.py — build an order report from the data layer in db.py."""


def order_report(db, order_ids):
    """Return a list of (order_id, customer_name, order_total) tuples, one per id in
    `order_ids`, in the SAME order as `order_ids`. `order_total` is the sum of the
    prices of the order's items. Assume every id is valid.
    """
    result = []
    for oid in order_ids:
        order = db.get_order(oid)
        customer = db.get_customer(order["customer_id"])
        total = 0
        for item_id in order["item_ids"]:
            total += db.get_item(item_id)["price"]
        result.append((oid, customer["name"], total))
    return result
