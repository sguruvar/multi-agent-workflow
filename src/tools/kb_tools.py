"""Tools for the Tech Support agent."""

from .fake_data import KNOWLEDGE_BASE


def search_kb(query: str) -> str:
    """Search the knowledge base for troubleshooting steps."""
    query_lower = query.lower()
    for topic, answer in KNOWLEDGE_BASE.items():
        if any(word in query_lower for word in topic.split()):
            return f"Topic: {topic}\n\nSolution: {answer}"
    return "No matching article found in the knowledge base. Please describe your issue in more detail, or I can escalate to a human agent."
