"""Tools for the Order Status agent."""

import time

from langchain_core.tools import tool

from .fake_data import ORDERS


@tool
def lookup_order(order_id: str) -> str:
    """Look up order status by order ID (e.g. ORD-1001)."""
    from ..metrics import track_tool_duration

    with track_tool_duration("order_status", "lookup_order"):
        order = ORDERS.get(order_id.upper())
        if not order:
            return f"Order {order_id} not found. Please check the order ID and try again."
        parts = [
            f"Order: {order_id.upper()}",
            f"Item: {order['item']}",
            f"Status: {order['status']}",
        ]
        if order["tracking"]:
            parts.append(f"Tracking: {order['tracking']}")
        if order["estimated_delivery"]:
            parts.append(f"Estimated Delivery: {order['estimated_delivery']}")
        return "\n".join(parts)
