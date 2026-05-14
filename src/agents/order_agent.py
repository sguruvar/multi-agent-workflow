"""Order Status Agent - LangGraph implementation."""

from typing import Literal

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

from ..models import get_chat_model
from ..tools.order_tools import lookup_order

SYSTEM_PROMPT = """You are the Order Status specialist at TechMart customer support.
Your ONLY job is to look up order statuses using the lookup_order tool.

IMPORTANT: If the customer provides an order ID (format: ORD-XXXX), you MUST immediately call the lookup_order tool with that ID. Do NOT ask for additional information.

If no order ID is provided, ask for it. Otherwise, call the tool and relay the results concisely."""

tools = [lookup_order]
model = get_chat_model(temperature=0).bind_tools(tools)


def call_model(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


graph = StateGraph(MessagesState)
graph.add_node("agent", call_model)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")

order_agent = graph.compile()
