#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# aws-teardown.sh — Destroy all AWS resources
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
TF_ENV="${TF_ENV:-aws}"

echo "=========================================="
echo "  AWS Teardown (profile: $AWS_PROFILE)"
echo "=========================================="
echo ""
read -p "  Destroy ALL resources? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "  Aborted."
    exit 0
fi

# Get EKS cluster name
cd "$ROOT_DIR/infra/terraform/environments/$TF_ENV"
EKS_CLUSTER=$(terraform output -raw eks_cluster_name 2>/dev/null || echo "")

if [ -n "$EKS_CLUSTER" ]; then
    echo ""
    echo "[1/2] Deleting Kubernetes namespace..."
    aws eks update-kubeconfig --name "$EKS_CLUSTER" --region "$AWS_REGION" --profile "$AWS_PROFILE" 2>/dev/null || true
    kubectl delete namespace agents --ignore-not-found=true 2>/dev/null || true
fi

echo ""
echo "[2/2] Destroying Terraform resources..."
terraform destroy -auto-approve

echo ""
echo "  Done. All resources destroyed."
