"""Load generator for the multi-agent system.

Sends realistic customer support queries at configurable rate to populate
dashboards with meaningful data across all agent types and frameworks.
"""

import os
import time
import random
import asyncio
import httpx

TARGET_URL = os.getenv("TARGET_URL", "http://localhost:8080")
RPS = float(os.getenv("LOAD_RPS", "2"))
DURATION_SECONDS = int(os.getenv("LOAD_DURATION", "0"))  # 0 = infinite

QUERIES = [
    # Order status (LangGraph)
    {"prompt": "Where is my order ORD-1001?", "session_id": "load-order-1"},
    {"prompt": "What's the status of order ORD-1002?", "session_id": "load-order-2"},
    {"prompt": "Track my order ORD-1003", "session_id": "load-order-3"},
    {"prompt": "When will ORD-1001 be delivered?", "session_id": "load-order-4"},
    {"prompt": "Is ORD-1004 shipped yet?", "session_id": "load-order-5"},
    # Billing (CrewAI)
    {"prompt": "What's my account balance? I'm CUST-100", "session_id": "load-billing-1"},
    {"prompt": "I want a refund for order ORD-1004", "session_id": "load-billing-2"},
    {"prompt": "Check balance for CUST-101", "session_id": "load-billing-3"},
    {"prompt": "Process refund for ORD-1003", "session_id": "load-billing-4"},
    {"prompt": "How much credit do I have? CUST-102", "session_id": "load-billing-5"},
    # Tech support (Strands)
    {"prompt": "My bluetooth headphones aren't connecting", "session_id": "load-tech-1"},
    {"prompt": "Screen flickering on my device", "session_id": "load-tech-2"},
    {"prompt": "Battery is draining really fast", "session_id": "load-tech-3"},
    {"prompt": "WiFi keeps dropping on my laptop", "session_id": "load-tech-4"},
    {"prompt": "App crashes every time I open it", "session_id": "load-tech-5"},
    # General
    {"prompt": "Hi there, what can you help me with?", "session_id": "load-general-1"},
    {"prompt": "Thanks for the help!", "session_id": "load-general-2"},
    {"prompt": "Hello!", "session_id": "load-general-3"},
]


async def send_request(client: httpx.AsyncClient, query: dict):
    try:
        resp = await client.post(
            f"{TARGET_URL}/invoke",
            json=query,
            timeout=60.0,
        )
        status = resp.status_code
        intent = resp.json().get("intent", "unknown") if status == 200 else "error"
        print(f"[{status}] intent={intent} session={query['session_id']}")
    except Exception as e:
        print(f"[ERR] {type(e).__name__}: {e}")


async def main():
    interval = 1.0 / RPS
    start = time.time()
    print(f"Load generator started: {RPS} RPS → {TARGET_URL}")
    print(f"Duration: {'infinite' if DURATION_SECONDS == 0 else f'{DURATION_SECONDS}s'}")

    async with httpx.AsyncClient() as client:
        while True:
            if DURATION_SECONDS > 0 and (time.time() - start) > DURATION_SECONDS:
                break
            query = random.choice(QUERIES)
            asyncio.create_task(send_request(client, query))
            await asyncio.sleep(interval)

    print("Load generation complete.")


if __name__ == "__main__":
    asyncio.run(main())
