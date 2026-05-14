"""Tools for the Billing agent."""

from .fake_data import CUSTOMERS, ORDERS, REFUND_ELIGIBLE_STATUSES


def check_balance(customer_id: str) -> str:
    """Check the account balance/credit for a customer."""
    customer = CUSTOMERS.get(customer_id.upper())
    if not customer:
        return f"Customer {customer_id} not found."
    return f"Customer: {customer['name']}\nAccount Credit: ${customer['balance']:.2f}"


def process_refund(order_id: str) -> str:
    """Process a refund for a given order ID."""
    order = ORDERS.get(order_id.upper())
    if not order:
        return f"Order {order_id} not found. Cannot process refund."
    if order["status"] not in REFUND_ELIGIBLE_STATUSES:
        return f"Order {order_id} has status '{order['status']}' and is not eligible for refund."
    return f"Refund initiated for order {order_id.upper()} ({order['item']}). Please allow 3-5 business days for the credit to appear."
