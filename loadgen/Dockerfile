FROM python:3.13-slim

WORKDIR /app
RUN pip install --no-cache-dir httpx
COPY loadgen.py .

ENV PYTHONUNBUFFERED=1
CMD ["python", "loadgen.py"]
