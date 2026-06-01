terraform {
  required_version = ">= 1.5.0"
}

# Local environment uses Kind + Ollama instead of EKS + Bedrock.
# This is a placeholder that documents the local equivalents.
# No real Terraform resources needed for local — scripts handle it.

output "note" {
  value = "Local mode uses Kind (not EKS), local Docker (not ECR), and Ollama (not Bedrock). Run scripts/local-up.sh to start."
}
