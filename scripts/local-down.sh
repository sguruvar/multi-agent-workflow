#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# local-down.sh — Tear down the local Kind cluster
# ============================================================

CLUSTER_NAME="multi-agent"

echo "Deleting Kind cluster '$CLUSTER_NAME'..."
kind delete cluster --name "$CLUSTER_NAME"

echo "Cleaning up Docker images..."
docker rmi agents-app:latest loadgen:latest 2>/dev/null || true

echo ""
echo "Local environment torn down."
