"""Fake in-memory databases for the customer support demo."""

ORDERS = {
    "ORD-1001": {
        "customer_id": "CUST-100",
        "item": "Wireless Headphones",
        "status": "shipped",
        "tracking": "1Z999AA10123456784",
        "estimated_delivery": "2026-05-18",
    },
    "ORD-1002": {
        "customer_id": "CUST-101",
        "item": "Smart Watch Pro",
        "status": "processing",
        "tracking": None,
        "estimated_delivery": "2026-05-22",
    },
    "ORD-1003": {
        "customer_id": "CUST-100",
        "item": "USB-C Hub",
        "status": "delivered",
        "tracking": "1Z999AA10123456799",
        "estimated_delivery": "2026-05-10",
    },
    "ORD-1004": {
        "customer_id": "CUST-102",
        "item": "Mechanical Keyboard",
        "status": "cancelled",
        "tracking": None,
        "estimated_delivery": None,
    },
}

CUSTOMERS = {
    "CUST-100": {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "balance": 24.99,
    },
    "CUST-101": {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "balance": 0.00,
    },
    "CUST-102": {
        "name": "Carol Davis",
        "email": "carol@example.com",
        "balance": 149.99,
    },
}

KNOWLEDGE_BASE = {
    "device won't turn on": "Try holding the power button for 10 seconds to force restart. If that doesn't work, connect the charging cable and wait 5 minutes before trying again.",
    "bluetooth not connecting": "Go to Settings > Bluetooth, forget the device, then re-pair. Make sure you're within 30 feet and no other device is connected.",
    "screen flickering": "Update your device firmware via Settings > System > Updates. If the issue persists, reduce screen brightness to 50% and contact us for a hardware diagnostic.",
    "battery draining fast": "Check Settings > Battery > Usage to identify power-hungry apps. Disable background refresh for apps you don't need. A factory reset may help if the issue persists.",
    "wifi keeps dropping": "Restart your router, then forget the network on your device and reconnect. If using 5GHz, try switching to 2.4GHz for better range.",
    "app crashes on launch": "Clear the app cache in Settings > Apps > [App Name] > Clear Cache. If it still crashes, uninstall and reinstall the app.",
}

REFUND_ELIGIBLE_STATUSES = {"delivered", "shipped", "cancelled"}
