#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# aws-deploy.sh — Full deploy: Terraform + ECR + EKS + AMP + Grafana
#
# Usage:
#   ./scripts/aws-deploy.sh                        # uses default profile, aws env
#   AWS_PROFILE=myprofile TF_ENV=genai ./scripts/aws-deploy.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
TF_ENV="${TF_ENV:-aws}"

echo "=========================================="
echo "  Multi-Agent — Full AWS Deployment"
echo "=========================================="
echo "  Profile: $AWS_PROFILE"
echo "  Region:  $AWS_REGION"
echo "  TF Env:  $TF_ENV"
echo ""

# --- 1. Terraform apply ---
echo "[1/7] Provisioning infrastructure (ECR + EKS + AMP + IAM)..."
cd "$ROOT_DIR/infra/terraform/environments/$TF_ENV"
terraform init -upgrade -input=false
terraform apply -auto-approve

export ECR_APP_URL=$(terraform output -raw ecr_app_url)
export ECR_LOADGEN_URL=$(terraform output -raw ecr_loadgen_url)
EKS_CLUSTER=$(terraform output -raw eks_cluster_name)
export AMP_ENDPOINT=$(terraform output -raw amp_endpoint)
export AMP_REMOTE_WRITE_ENDPOINT="${AMP_ENDPOINT}api/v1/remote_write"
export ADOT_ROLE_ARN=$(terraform output -raw observability_role_arn)
export APP_ROLE_ARN=$(terraform output -raw app_role_arn)

ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
cd "$ROOT_DIR"

echo "  Account:     $ACCOUNT_ID"
echo "  EKS:         $EKS_CLUSTER"
echo "  AMP:         $AMP_ENDPOINT"

# --- 2. Build and push images ---
echo ""
echo "[2/7] Building and pushing images to ECR..."
aws ecr get-login-password --region "$AWS_REGION" --profile "$AWS_PROFILE" | \
    docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build --platform linux/amd64 -t "$ECR_APP_URL:latest" "$ROOT_DIR"
docker push "$ECR_APP_URL:latest"

docker build --platform linux/amd64 -t "$ECR_LOADGEN_URL:latest" "$ROOT_DIR/loadgen"
docker push "$ECR_LOADGEN_URL:latest"

# --- 3. Configure kubectl ---
echo ""
echo "[3/7] Configuring kubectl..."
aws eks update-kubeconfig --name "$EKS_CLUSTER" --region "$AWS_REGION" --profile "$AWS_PROFILE"
kubectl get nodes

# --- 4. Deploy K8s manifests ---
echo ""
echo "[4/7] Deploying to EKS..."
kubectl apply -f "$ROOT_DIR/k8s/aws/namespace.yaml"

for f in service-accounts otel-collector tempo agents-app loadgen grafana; do
    envsubst < "$ROOT_DIR/k8s/aws/${f}.yaml" | kubectl apply -f -
done

# --- 5. Wait for rollout ---
echo ""
echo "[5/7] Waiting for pods..."
kubectl rollout status deployment/tempo -n agents --timeout=60s
kubectl rollout status deployment/otel-collector -n agents --timeout=120s
kubectl rollout status deployment/agents-app -n agents --timeout=180s
kubectl rollout status deployment/loadgen -n agents --timeout=60s
kubectl rollout status deployment/grafana -n agents --timeout=60s

# --- 6. Configure Grafana (datasource + dashboards via API) ---
# NOTE: Grafana provisioning does NOT correctly set sigV4AuthType.
# We MUST configure the datasource and import dashboards via API.
echo ""
echo "[6/7] Configuring Grafana..."
kubectl port-forward -n agents svc/grafana 3199:3000 &>/dev/null &
PF_PID=$!
sleep 8

# Configure AMP datasource with correct sigV4AuthType
curl -s -X PUT "http://localhost:3199/api/datasources/uid/prometheus" \
    -u admin:admin -H "Content-Type: application/json" \
    -d "{
        \"name\":\"AMP\",\"type\":\"prometheus\",\"uid\":\"prometheus\",
        \"access\":\"proxy\",\"url\":\"${AMP_ENDPOINT}\",\"isDefault\":true,
        \"jsonData\":{\"httpMethod\":\"POST\",\"sigV4Auth\":true,\"sigV4AuthType\":\"default\",\"sigV4Region\":\"${AWS_REGION}\"}
    }" > /dev/null 2>&1

# Import dashboards (these JSONs have datasource on every target + correct metric names)
for dashboard_file in "$ROOT_DIR/grafana/dashboards/"*.json; do
    curl -s -X POST "http://localhost:3199/api/dashboards/db" \
        -u admin:admin -H "Content-Type: application/json" \
        -d "{\"dashboard\":$(cat "$dashboard_file"),\"overwrite\":true}" > /dev/null 2>&1
done

kill $PF_PID 2>/dev/null
echo "  Datasource + 5 dashboards configured."

# --- 7. Status ---
echo ""
echo "[7/7] Final status..."
kubectl get pods -n agents

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "  Access:"
echo "    kubectl port-forward -n agents svc/grafana 3000:3000"
echo ""
echo "  Grafana: http://localhost:3000"
echo "    • Developer/SRE — latency, request rate, tool calls"
echo "    • FinOps — real cost by framework (\$0.001/1K in, \$0.005/1K out)"
echo "    • Business — intent volume, cost per query, resolution"
echo "    • Operations — cost spikes, timeout rate, heatmap"
echo "    • Observability — session traces → span waterfall → node graph"
echo ""
echo "  Load generator running at 0.5 RPS."
echo "  Dashboards auto-refresh every 10s."
echo ""
echo "  Teardown: AWS_PROFILE=$AWS_PROFILE TF_ENV=$TF_ENV ./scripts/aws-teardown.sh"
echo "=========================================="
