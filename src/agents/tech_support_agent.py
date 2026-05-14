"""Tech Support Agent - Strands Agents SDK implementation."""

from strands import Agent, tool

from ..models import get_strands_model
from ..tools.kb_tools import search_kb


@tool
def search_knowledge_base(query: str) -> str:
    """Search the TechMart knowledge base for troubleshooting steps related to a customer's technical issue."""
    return search_kb(query)


SYSTEM_PROMPT = """You are a technical support specialist at TechMart.
Your job is to help customers resolve technical issues with their devices.

When a customer describes a problem:
1. Search the knowledge base for relevant solutions
2. Provide clear, step-by-step troubleshooting instructions
3. If the knowledge base doesn't have a match, suggest they contact a human agent

Keep responses concise and empathetic."""

model = get_strands_model()

tech_support = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[search_knowledge_base],
)


def run_tech_support_agent(query: str) -> str:
    """Execute the tech support agent with a customer query."""
    result = tech_support(query)
    return str(result)
