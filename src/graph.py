"""Main graph entry point — exposes the supervisor for LangGraph dev server."""

from dotenv import load_dotenv

load_dotenv()

from .telemetry import get_tracer as _init_telemetry
_init_telemetry()

from .agents.supervisor import supervisor_graph

graph = supervisor_graph
