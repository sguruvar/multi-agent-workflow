#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# local-up.sh — Spin up the full stack locally with Kind
# Equivalents: ECR→local docker | EKS→Kind | Bedrock→Bedrock(or Ollama)
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CLUSTER_NAME="multi-agent"

echo "=========================================="
echo "  Multi-Agent Observability — Local Setup"
echo "=========================================="

# --- 1. Create Kind cluster ---
echo ""
echo "[1/5] Creating Kind cluster..."
if kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
    echo "  Cluster '$CLUSTER_NAME' already exists, skipping."
else
    kind create cluster --config "$ROOT_DIR/k8s/kind-cluster.yaml"
fi
kubectl cluster-info --context "kind-$CLUSTER_NAME"

# --- 2. Build Docker images ---
echo ""
echo "[2/5] Building Docker images..."
docker build -t agents-app:latest "$ROOT_DIR"
docker build -t loadgen:latest "$ROOT_DIR/loadgen"

# --- 3. Load images into Kind ---
echo ""
echo "[3/5] Loading images into Kind..."
kind load docker-image agents-app:latest --name "$CLUSTER_NAME"
kind load docker-image loadgen:latest --name "$CLUSTER_NAME"

# --- 4. Deploy to Kind ---
echo ""
echo "[4/5] Deploying to Kubernetes..."
kubectl apply -f "$ROOT_DIR/k8s/base/namespace.yaml"

# Create AWS secret from your profile (set AWS_PROFILE env var to override)
AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id --profile "${AWS_PROFILE:-default}")
AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key --profile "${AWS_PROFILE:-default}")

kubectl create secret generic aws-credentials \
    --namespace agents \
    --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create grafana dashboards configmap from JSON files
kubectl create configmap grafana-dashboards \
    --namespace agents \
    --from-file="$ROOT_DIR/grafana/dashboards/" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f "$ROOT_DIR/k8s/base/otel-collector.yaml"
kubectl apply -f "$ROOT_DIR/k8s/base/jaeger.yaml"
kubectl apply -f "$ROOT_DIR/k8s/base/prometheus.yaml"
kubectl apply -f "$ROOT_DIR/k8s/base/grafana.yaml"
kubectl apply -f "$ROOT_DIR/k8s/base/agents-app.yaml"
kubectl apply -f "$ROOT_DIR/k8s/base/loadgen.yaml"

# --- 5. Wait and report ---
echo ""
echo "[5/5] Waiting for pods to be ready..."
kubectl wait --namespace agents --for=condition=ready pod --selector=app=agents-app --timeout=120s 2>/dev/null || true
kubectl wait --namespace agents --for=condition=ready pod --selector=app=grafana --timeout=60s 2>/dev/null || true

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
echo "  Load gen is running at 1 RPS."
echo "  Give it 2-3 minutes for dashboards to populate."
echo ""
echo "  Teardown: ./scripts/local-down.sh"
echo "=========================================="
