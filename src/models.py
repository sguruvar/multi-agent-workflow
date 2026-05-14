"""Model configuration — switch between providers via LLM_PROVIDER env var.

Bedrock auth: set AWS_PROFILE=genai (or your profile) in .env or shell.
"""

import os

import boto3


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "bedrock")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "us.anthropic.claude-sonnet-4-20250514-v1:0")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


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
