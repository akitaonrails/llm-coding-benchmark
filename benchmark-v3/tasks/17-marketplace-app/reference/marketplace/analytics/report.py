"""Reference: same result, but a CONSTANT number of round-trips (no N+1).

Batch every level: orders in one call, all needed customers in one call, all needed
items in one call. 3 round-trips regardless of how many orders are requested.
"""


def order_report(db, order_ids):
    orders = db.get_orders(order_ids)
    customer_ids = {orders[oid]["customer_id"] for oid in order_ids}
    customers = db.get_customers(list(customer_ids))
    item_ids = {iid for oid in order_ids for iid in orders[oid]["item_ids"]}
    items = db.get_items(list(item_ids))
    out = []
    for oid in order_ids:
        o = orders[oid]
        total = sum(items[iid]["price"] for iid in o["item_ids"])
        out.append((oid, customers[o["customer_id"]]["name"], total))
    return out
