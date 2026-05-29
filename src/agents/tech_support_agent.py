"""Tech Support Agent - Strands Agents SDK implementation."""

from opentelemetry import trace
from strands import Agent, tool

from ..models import get_strands_model
from ..metrics import track_tool_duration, record_escalation
from ..tools.kb_tools import search_kb

tracer = trace.get_tracer("nysummit-agents.tech_support")


@tool
def search_knowledge_base(query: str) -> str:
    """Search the TechMart knowledge base for troubleshooting steps related to a customer's technical issue."""
    with track_tool_duration("tech_support", "search_knowledge_base"):
        result = search_kb(query)
        if "No matching article" in result:
            record_escalation("tech_support", "no_kb_match")
        return result


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
    with tracer.start_as_current_span("strands.tech_support_agent") as span:
        span.set_attribute("agent.name", "tech_support")
        span.set_attribute("agent.framework", "strands")
        result = tech_support(query)
        output = str(result)
        return output
