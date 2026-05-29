"""Custom OTEL metrics for business-level observability.

These go BEYOND what Bedrock/AgentCore auto-vend. They capture
application-specific signals queryable via PromQL in CloudWatch.
"""

import time
from contextlib import contextmanager

from opentelemetry import metrics

meter = metrics.get_meter("nysummit-agents", "0.1.0")

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

token_usage_histogram = meter.create_histogram(
    "agent.token.usage",
    description="Token usage per invocation",
    unit="1",
)

# --- Gauges ---

active_sessions_gauge = meter.create_up_down_counter(
    "agent.sessions.active",
    description="Currently active agent sessions",
    unit="1",
)


# --- Helpers ---

@contextmanager
def track_agent_duration(agent_name: str, intent: str = "unknown"):
    """Context manager to record agent invocation duration."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        agent_duration_histogram.record(
            duration_ms,
            {"agent_name": agent_name, "intent": intent},
        )


@contextmanager
def track_tool_duration(agent_name: str, tool_name: str):
    """Context manager to record tool call duration."""
    start = time.perf_counter()
    try:
        tool_call_counter.add(1, {"agent_name": agent_name, "tool_name": tool_name})
        yield
    except Exception as e:
        tool_error_counter.add(1, {
            "agent_name": agent_name,
            "tool_name": tool_name,
            "error_type": type(e).__name__,
        })
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        tool_duration_histogram.record(
            duration_ms,
            {"agent_name": agent_name, "tool_name": tool_name},
        )


def record_intent(intent: str, customer_tier: str = "standard"):
    """Record an intent classification."""
    intent_counter.add(1, {"intent": intent, "customer_tier": customer_tier})


def record_escalation(from_agent: str, reason: str):
    """Record an agent escalation."""
    escalation_counter.add(1, {"from_agent": from_agent, "reason": reason})
