FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

EXPOSE 8080

ENV OTEL_PYTHON_DISTRO=opentelemetry_distro
ENV OTEL_PYTHON_CONFIGURATOR=opentelemetry_configurator
ENV OTEL_METRICS_EXPORTER=otlp
ENV OTEL_TRACES_EXPORTER=otlp
ENV OTEL_EXPORTER_OTLP_PROTOCOL=grpc
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ENV OTEL_SERVICE_NAME=nysummit-agents

CMD ["opentelemetry-instrument", "uvicorn", "src.agentcore_app:app", "--host", "0.0.0.0", "--port", "8080"]
