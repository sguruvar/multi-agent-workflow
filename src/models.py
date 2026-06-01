"""Model configuration — switch between providers via LLM_PROVIDER env var.

Includes a boto3 event hook that captures token usage from every Bedrock call,
regardless of which framework (LangGraph, CrewAI, Strands) initiated it.
"""

import os
import boto3
from botocore.config import Config

from .metrics import record_token_usage, AGENT_FRAMEWORK

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "bedrock")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Global agent context for token attribution
_current_agent = "unknown"


def set_current_agent(agent_name: str):
    """Set the agent name for token attribution."""
    global _current_agent
    _current_agent = agent_name


def _get_current_agent() -> str:
    return _current_agent


def _bedrock_response_hook(parsed, **kwargs):
    """Boto3 event hook — fires after every Bedrock converse/invoke response."""
    usage = parsed.get("usage", {})
    input_tokens = usage.get("inputTokens", 0)
    output_tokens = usage.get("outputTokens", 0)
    if input_tokens or output_tokens:
        agent = _get_current_agent()
        record_token_usage(agent, input_tokens, output_tokens, agent)


def install_token_tracking():
    """Monkey-patch boto3.Session to register token tracking on every new client."""
    _original_client = boto3.Session.client

    def _patched_client(self, service_name, *args, **kwargs):
        client = _original_client(self, service_name, *args, **kwargs)
        if service_name == "bedrock-runtime":
            client.meta.events.register("after-call.bedrock-runtime.Converse", _bedrock_response_hook)
            client.meta.events.register("after-call.bedrock-runtime.InvokeModel", _bedrock_response_hook)
        return client

    boto3.Session.client = _patched_client


# Install globally at import time
install_token_tracking()


def get_chat_model(temperature: float = 0, **kwargs):
    """Get a chat model based on LLM_PROVIDER env var."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=OPENAI_MODEL, temperature=temperature, **kwargs)
    else:
        from langchain_aws import ChatBedrockConverse
        return ChatBedrockConverse(
            model=BEDROCK_MODEL,
            region_name=AWS_REGION,
            temperature=temperature,
            **kwargs,
        )


def get_strands_model():
    """Get a Strands model based on LLM_PROVIDER env var."""
    if LLM_PROVIDER == "openai":
        from strands.models.openai import OpenAIModel
        return OpenAIModel(model_id=OPENAI_MODEL)
    else:
        from strands.models import BedrockModel
        session = boto3.Session(region_name=AWS_REGION)
        return BedrockModel(
            model_id=BEDROCK_MODEL,
            boto_session=session,
        )


def get_crewai_model_name():
    """Get model string for CrewAI's LLM class."""
    if LLM_PROVIDER == "openai":
        return f"openai/{OPENAI_MODEL}"
    else:
        return f"bedrock/{BEDROCK_MODEL}"
