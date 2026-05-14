"""AgentCore Runtime wrapper for deploying to Bedrock AgentCore."""

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .agents.supervisor import supervisor_graph
from .telemetry import get_tracer

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload):
    tracer = get_tracer()
    with tracer.start_as_current_span("customer_support_invoke") as span:
        user_message = payload.get("prompt", "Hi, I need help")
        span.set_attribute("user.message", user_message)

        result = supervisor_graph.invoke(
            {"messages": [HumanMessage(content=user_message)]}
        )

        response = result["messages"][-1].content
        span.set_attribute("agent.response_length", len(response))
        span.set_attribute("agent.intent", result.get("intent", "unknown"))

        return {"result": response}


if __name__ == "__main__":
    app.run()
