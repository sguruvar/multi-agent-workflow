#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# docker-compose-up.sh — Simplest local option (no Kind needed)
# Uses docker-compose with Bedrock credentials from your AWS profile
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  Multi-Agent — Docker Compose Mode"
echo "=========================================="

# Export AWS creds from your profile (set AWS_PROFILE env var to override)
export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id --profile "${AWS_PROFILE:-default}")
export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key --profile "${AWS_PROFILE:-default}")
export AWS_REGION=${AWS_REGION:-us-east-1}

cd "$ROOT_DIR"

echo ""
echo "Starting services..."
docker compose up -d --build

echo ""
echo "Starting load generator..."
docker compose --profile loadgen up -d --build

echo ""
echo "=========================================="
echo "  Stack is UP!"
echo "=========================================="
echo ""
echo "  Application:  http://localhost:8080/invoke"
echo "  Grafana:      http://localhost:3000  (admin/admin)"
echo "  Jaeger:       http://localhost:16686"
echo "  Prometheus:   http://localhost:9090"
echo ""
echo "  Load gen running at 1 RPS."
echo "  Teardown: docker compose --profile loadgen down -v"
echo "=========================================="
