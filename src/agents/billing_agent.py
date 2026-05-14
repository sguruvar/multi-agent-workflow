"""Billing Agent - CrewAI implementation."""

import os

from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool as crewai_tool

from ..models import get_crewai_model_name
from ..tools.billing_tools import check_balance, process_refund


@crewai_tool
def check_customer_balance(customer_id: str) -> str:
    """Check the account balance/credit for a customer by their ID (e.g. CUST-100)."""
    return check_balance(customer_id)


@crewai_tool
def process_customer_refund(order_id: str) -> str:
    """Process a refund for a given order ID (e.g. ORD-1001)."""
    return process_refund(order_id)


llm = LLM(
    model=get_crewai_model_name(),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)

billing_specialist = Agent(
    role="Billing Specialist",
    goal="Help customers with billing inquiries, balance checks, and refund processing",
    backstory=(
        "You are a billing specialist at TechMart. You handle account balance inquiries "
        "and process refunds. You are friendly, efficient, and always confirm actions "
        "before processing. Keep responses concise."
    ),
    tools=[check_customer_balance, process_customer_refund],
    llm=llm,
    verbose=False,
)


def run_billing_agent(query: str) -> str:
    """Execute the billing agent with a customer query."""
    task = Task(
        description=f"Handle this customer billing request: {query}",
        expected_output="A clear, helpful response addressing the customer's billing concern.",
        agent=billing_specialist,
    )
    crew = Crew(agents=[billing_specialist], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)
