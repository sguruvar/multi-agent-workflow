"""Standalone runner — demonstrates the multi-agent system with session memory.

Usage:
    python -m src.main
"""

from dotenv import load_dotenv

load_dotenv()

from .telemetry import get_tracer
get_tracer()

from langchain_core.messages import HumanMessage
from .agents.supervisor import supervisor_graph


SESSIONS = [
    {
        "thread_id": "session-alice-001",
        "customer": "Alice",
        "messages": [
            "Hi there! I need some help today.",
            "Where is my order ORD-1001?",
            "Thanks! Also, my bluetooth headphones aren't connecting.",
        ],
    },
    {
        "thread_id": "session-bob-002",
        "customer": "Bob",
        "messages": [
            "What's the status of order ORD-1002?",
            "OK, and what's my account balance? I'm CUST-101.",
        ],
    },
    {
        "thread_id": "session-carol-003",
        "customer": "Carol",
        "messages": [
            "I want a refund for order ORD-1004",
            "My screen is flickering on the new device",
            "The battery is also draining really fast",
        ],
    },
]


def main():
    print("=" * 60)
    print("TechMart Customer Support - Multi-Agent Demo")
    print("Frameworks: LangGraph (supervisor) + CrewAI + Strands SDK")
    print("=" * 60)

    for session in SESSIONS:
        thread_id = session["thread_id"]
        customer = session["customer"]
        config = {"configurable": {"thread_id": thread_id}}

        print(f"\n{'━' * 60}")
        print(f"SESSION: {thread_id} (Customer: {customer})")
        print(f"{'━' * 60}")

        for msg in session["messages"]:
            print(f"\n  Customer: {msg}")

            result = supervisor_graph.invoke(
                {"messages": [HumanMessage(content=msg)]},
                config=config,
            )
            response = result["messages"][-1].content
            intent = result.get("intent", "unknown")

            print(f"  [Route: {intent}]")
            print(f"  Agent: {response[:200]}{'...' if len(response) > 200 else ''}")

    print(f"\n{'━' * 60}")
    print("All sessions complete.")
    print("Traces + metrics exported to configured OTEL endpoint.")
    print("Check: CloudWatch > GenAI Dashboard | PromQL Query Studio")


if __name__ == "__main__":
    main()
