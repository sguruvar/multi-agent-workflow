"""FastAPI entry point for EKS deployment.

Run with: uvicorn src.agentcore_app:app --host 0.0.0.0 --port 8080
Or via OTEL: opentelemetry-instrument uvicorn src.agentcore_app:app --host 0.0.0.0 --port 8080
"""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from .telemetry import get_tracer
from .agents.supervisor import supervisor_graph
from .metrics import active_sessions_gauge

get_tracer()

app = FastAPI(title="TechMart Customer Support", version="0.1.0")


class InvokeRequest(BaseModel):
    prompt: str = "Hi, I need help"
    session_id: str = "default"


class InvokeResponse(BaseModel):
    result: str
    intent: str
    session_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/invoke", response_model=InvokeResponse)
async def invoke(request: InvokeRequest):
    tracer = get_tracer()
    active_sessions_gauge.add(1)

    try:
        with tracer.start_as_current_span("customer_support.invoke") as span:
            span.set_attribute("session.id", request.session_id)
            span.set_attribute("user.message_length", len(request.prompt))

            config = {"configurable": {"thread_id": request.session_id}}

            result = supervisor_graph.invoke(
                {"messages": [HumanMessage(content=request.prompt)]},
                config=config,
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
