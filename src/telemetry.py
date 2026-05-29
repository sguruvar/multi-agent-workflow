"""OpenTelemetry setup for traces + metrics.

On EKS: set OTEL_EXPORTER_OTLP_ENDPOINT to the otel-collector service.
The opentelemetry-instrument wrapper handles provider setup when using
the distro. This module adds framework instrumentors and can also
configure providers manually for local dev (no distro).
"""

import os

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "nysummit-agents")


def setup_telemetry(service_name: str = SERVICE_NAME):
    """Initialize OTEL tracing + metrics.

    When launched via `opentelemetry-instrument`, the distro sets up
    providers automatically — we just add framework instrumentors.
    For local dev without the distro wrapper, we wire up providers manually.
    """
    using_distro = os.getenv("OTEL_PYTHON_DISTRO") is not None

    if not using_distro:
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: "0.1.0",
        })

        protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

        if protocol == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            trace_exporter = OTLPSpanExporter(endpoint=endpoint or "http://localhost:4317")
            metric_exporter = OTLPMetricExporter(endpoint=endpoint or "http://localhost:4317")
        else:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            base = endpoint or "http://localhost:4318"
            trace_exporter = OTLPSpanExporter(endpoint=f"{base}/v1/traces")
            metric_exporter = OTLPMetricExporter(endpoint=f"{base}/v1/metrics")

        trace_provider = TracerProvider(resource=resource)
        trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(trace_provider)

        reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(meter_provider)

    # Framework instrumentors — add GenAI spans to LangChain/CrewAI calls
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        LangChainInstrumentor().instrument()
    except Exception:
        pass

    try:
        from openinference.instrumentation.crewai import CrewAIInstrumentor
        CrewAIInstrumentor().instrument()
    except Exception:
        pass

    return trace.get_tracer(service_name)


_tracer = None


def get_tracer() -> trace.Tracer:
    global _tracer
    if _tracer is None:
        _tracer = setup_telemetry()
    return _tracer
