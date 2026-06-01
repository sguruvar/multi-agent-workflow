"""FastAPI entry point for EKS deployment.

Run with: uvicorn src.app:app --host 0.0.0.0 --port 8080
"""

from dotenv import load_dotenv

load_dotenv()

# MUST initialize telemetry BEFORE importing agents (they register instrumentors)
from .telemetry import setup_telemetry
setup_telemetry()

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from .agents.supervisor import supervisor_graph
from .metrics import active_sessions_gauge, record_http_request
from .telemetry import get_tracer

app = FastAPI(title="TechMart Customer Support", version="0.1.0")
_executor = ThreadPoolExecutor(max_workers=4)


class InvokeRequest(BaseModel):
    prompt: str = "Hi, I need help"
    session_id: str = "default"


class InvokeResponse(BaseModel):
    result: str
    intent: str
    session_id: str


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    record_http_request(request.url.path, response.status_code)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


def _invoke_sync(prompt: str, session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    result = supervisor_graph.invoke(
        {"messages": [HumanMessage(content=prompt)]},
        config=config,
    )
    return result


@app.post("/invoke", response_model=InvokeResponse)
async def invoke(request: InvokeRequest):
    tracer = get_tracer()
    active_sessions_gauge.add(1)

    try:
        with tracer.start_as_current_span("customer_support.invoke") as span:
            span.set_attribute("session.id", request.session_id)
            span.set_attribute("user.message_length", len(request.prompt))

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor, _invoke_sync, request.prompt, request.session_id
            )

            response = result["messages"][-1].content
            intent = result.get("intent", "unknown")

            span.set_attribute("agent.intent", intent)
            span.set_attribute("agent.response_length", len(response))

            return InvokeResponse(
                result=response, intent=intent, session_id=request.session_id
            )
    finally:
        active_sessions_gauge.add(-1)
