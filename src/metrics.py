"""Custom OTEL metrics for business-level observability.

These go BEYOND what Bedrock/AgentCore auto-vend. They capture
application-specific signals queryable via PromQL in CloudWatch.
"""

import time
from contextlib import contextmanager

from opentelemetry import metrics

meter = metrics.get_meter("customer-support-agent", "0.1.0")

# --- Counters ---

intent_counter = meter.create_counter(
    "agent.intent.classified",
    description="Intent classifications by type",
    unit="1",
)

tool_call_counter = meter.create_counter(
    "agent.tool.calls",
    description="Tool invocations by agent and tool name",
    unit="1",
)

tool_error_counter = meter.create_counter(
    "agent.tool.errors",
    description="Tool errors by agent and error type",
    unit="1",
)

escalation_counter = meter.create_counter(
    "agent.escalation.count",
    description="Queries that could not be resolved by the agent",
    unit="1",
)

http_request_counter = meter.create_counter(
    "http.requests",
    description="HTTP request count by path and status",
    unit="1",
)

# --- Histograms ---

agent_duration_histogram = meter.create_histogram(
    "agent.invocation.duration",
    description="End-to-end agent invocation duration",
    unit="ms",
)

tool_duration_histogram = meter.create_histogram(
    "agent.tool.duration",
    description="Individual tool call duration",
    unit="ms",
)

token_input_counter = meter.create_counter(
    "agent.tokens.input",
    description="Input tokens consumed per invocation",
    unit="1",
)

token_output_counter = meter.create_counter(
    "agent.tokens.output",
    description="Output tokens consumed per invocation",
    unit="1",
)

cost_counter = meter.create_counter(
    "agent.cost.usd",
    description="Estimated cost in USD (millionths) per invocation",
    unit="1",
)

# --- Gauges ---

active_sessions_gauge = meter.create_up_down_counter(
    "agent.sessions.active",
    description="Currently active agent sessions",
    unit="1",
)


# --- Framework-to-agent mapping ---
AGENT_FRAMEWORK = {
    "order_status": "langgraph",
    "billing": "crewai",
    "tech_support": "strands",
    "general": "langgraph",
}


# --- Helpers ---

@contextmanager
def track_agent_duration(agent_name: str, intent: str = "unknown"):
    """Context manager to record agent invocation duration."""
    framework = AGENT_FRAMEWORK.get(agent_name, "unknown")
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        agent_duration_histogram.record(
            duration_ms,
            {"agent_name": agent_name, "intent": intent, "framework": framework},
        )


@contextmanager
def track_tool_duration(agent_name: str, tool_name: str):
    """Context manager to record tool call duration."""
    framework = AGENT_FRAMEWORK.get(agent_name, "unknown")
    start = time.perf_counter()
    try:
        tool_call_counter.add(1, {"agent_name": agent_name, "tool_name": tool_name, "framework": framework})
        yield
    except Exception as e:
        tool_error_counter.add(1, {
            "agent_name": agent_name,
            "tool_name": tool_name,
            "error_type": type(e).__name__,
            "framework": framework,
        })
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        tool_duration_histogram.record(
            duration_ms,
            {"agent_name": agent_name, "tool_name": tool_name, "framework": framework},
        )


def record_intent(intent: str, customer_tier: str = "standard"):
    """Record an intent classification."""
    framework = AGENT_FRAMEWORK.get(intent, "unknown")
    intent_counter.add(1, {"intent": intent, "customer_tier": customer_tier, "framework": framework})


def record_escalation(from_agent: str, reason: str):
    """Record an agent escalation."""
    framework = AGENT_FRAMEWORK.get(from_agent, "unknown")
    escalation_counter.add(1, {"from_agent": from_agent, "reason": reason, "framework": framework})


# Claude Haiku 4.5 pricing (us-east-1)
PRICE_INPUT_PER_TOKEN = 0.001 / 1000    # $0.001 per 1K input tokens
PRICE_OUTPUT_PER_TOKEN = 0.005 / 1000   # $0.005 per 1K output tokens


def record_token_usage(agent_name: str, input_tokens: int, output_tokens: int, intent: str = "unknown"):
    """Record real token usage and compute cost."""
    framework = AGENT_FRAMEWORK.get(agent_name, "unknown")
    labels = {"agent_name": agent_name, "intent": intent, "framework": framework}

    token_input_counter.add(input_tokens, labels)
    token_output_counter.add(output_tokens, labels)

    cost_usd = (input_tokens * PRICE_INPUT_PER_TOKEN) + (output_tokens * PRICE_OUTPUT_PER_TOKEN)
    # Store cost in micro-dollars (multiply by 1_000_000) so counter stays integer-friendly
    cost_counter.add(int(cost_usd * 1_000_000), labels)


def record_http_request(path: str, status: int):
    """Record HTTP request."""
    http_request_counter.add(1, {"path": path, "status": str(status)})
