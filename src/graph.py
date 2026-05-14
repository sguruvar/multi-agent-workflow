"""Main graph entry point — exposes the supervisor for LangGraph dev server."""

from dotenv import load_dotenv

load_dotenv()

from . import tracing  # noqa: F401 — must initialize before framework imports

from .agents.supervisor import supervisor_graph

graph = supervisor_graph
