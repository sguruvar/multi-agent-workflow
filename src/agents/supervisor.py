"""Supervisor Agent - LangGraph router that classifies intent and delegates."""

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import END, START, StateGraph, MessagesState
from pydantic import BaseModel, Field

from ..models import get_chat_model
from .order_agent import order_agent
from .billing_agent import run_billing_agent
from .tech_support_agent import run_tech_support_agent


class SupervisorState(MessagesState):
    intent: str


class IntentClassification(BaseModel):
    """Classification of customer support intent."""
    intent: Literal["order_status", "billing", "tech_support", "general"] = Field(
        description="The classified intent of the customer query"
    )
    reasoning: str = Field(description="Brief reasoning for the classification")


CLASSIFIER_PROMPT = """You are a customer support router for TechMart.
Classify the customer's message into one of these categories:

- order_status: Questions about order tracking, delivery status, shipping updates (mentions order IDs like ORD-XXXX, asks "where is my order", shipping, delivery, tracking)
- billing: Questions about refunds, account balance, credits, payments, charges
- tech_support: Questions about device issues, troubleshooting, things not working, setup help
- general: Greetings, off-topic, or queries that don't fit the above categories

Classify based on the PRIMARY intent of the message."""

classifier = get_chat_model(temperature=0).with_structured_output(IntentClassification)
responder = get_chat_model(temperature=0.3)


def classify_intent(state: SupervisorState):
    last_message = state["messages"][-1]
    messages = [SystemMessage(content=CLASSIFIER_PROMPT), last_message]
    result = classifier.invoke(messages)
    return {"intent": result.intent}


def route_by_intent(state: SupervisorState) -> Literal["order_status", "billing", "tech_support", "general"]:
    return state.get("intent", "general")


def handle_order_status(state: SupervisorState):
    result = order_agent.invoke({"messages": state["messages"]})
    response = result["messages"][-1]
    return {"messages": [response]}


def handle_billing(state: SupervisorState):
    last_message = state["messages"][-1]
    query = last_message.content if hasattr(last_message, "content") else str(last_message)
    result = run_billing_agent(query)
    return {"messages": [AIMessage(content=result)]}


def handle_tech_support(state: SupervisorState):
    last_message = state["messages"][-1]
    query = last_message.content if hasattr(last_message, "content") else str(last_message)
    result = run_tech_support_agent(query)
    return {"messages": [AIMessage(content=result)]}


def handle_general(state: SupervisorState):
    messages = [
        SystemMessage(content="You are a friendly TechMart customer support agent. For general queries, provide a helpful response and let the customer know you can help with order tracking, billing, and technical support."),
    ] + state["messages"]
    response = responder.invoke(messages)
    return {"messages": [response]}


graph = StateGraph(SupervisorState)

graph.add_node("classify", classify_intent)
graph.add_node("order_status", handle_order_status)
graph.add_node("billing", handle_billing)
graph.add_node("tech_support", handle_tech_support)
graph.add_node("general", handle_general)

graph.add_edge(START, "classify")
graph.add_conditional_edges("classify", route_by_intent)
graph.add_edge("order_status", END)
graph.add_edge("billing", END)
graph.add_edge("tech_support", END)
graph.add_edge("general", END)

supervisor_graph = graph.compile()
