terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to use"
  type        = string
  default     = "default"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "multi-agent"
}

variable "vpc_id" {
  description = "VPC ID for EKS cluster"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for EKS (at least 2 in different AZs)"
  type        = list(string)
}

locals {
  tags = {
    Project     = var.project_name
    Environment = "demo"
    ManagedBy   = "terraform"
  }
  account_id = data.aws_caller_identity.current.account_id
}

data "aws_caller_identity" "current" {}

# --- ECR Repositories ---

module "ecr_app" {
  source          = "../../modules/ecr"
  repository_name = "${var.project_name}-agents"
  tags            = local.tags
}

module "ecr_loadgen" {
  source          = "../../modules/ecr"
  repository_name = "${var.project_name}-loadgen"
  tags            = local.tags
}

# --- EKS Cluster ---

module "eks" {
  source             = "../../modules/eks"
  cluster_name       = var.project_name
  vpc_id             = var.vpc_id
  subnet_ids         = var.subnet_ids
  node_instance_type = "t3.medium"
  desired_capacity   = 2
  tags               = local.tags
}

# --- Amazon Managed Prometheus (AMP) ---

resource "aws_prometheus_workspace" "this" {
  alias = var.project_name
  tags  = local.tags
}

# --- IAM role for ADOT collector + Grafana to read/write AMP ---

resource "aws_iam_role" "adot_collector" {
  name = "${var.project_name}-observability"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = module.eks.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringLike = {
            "${module.eks.oidc_provider}:aud" = "sts.amazonaws.com"
            "${module.eks.oidc_provider}:sub" = "system:serviceaccount:agents:*"
          }
        }
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy" "adot_amp_write" {
  name = "amp-full-access"
  role = aws_iam_role.adot_collector.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aps:RemoteWrite",
          "aps:QueryMetrics",
          "aps:GetSeries",
          "aps:GetLabels",
          "aps:GetMetricMetadata"
        ]
        Resource = "*"
      }
    ]
  })
}

# --- IAM role for app pods to call Bedrock ---

resource "aws_iam_role" "app_bedrock" {
  name = "${var.project_name}-app-bedrock"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = module.eks.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${module.eks.oidc_provider}:aud" = "sts.amazonaws.com"
            "${module.eks.oidc_provider}:sub" = "system:serviceaccount:agents:agents-app"
          }
        }
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy" "app_bedrock_invoke" {
  name = "bedrock-invoke"
  role = aws_iam_role.app_bedrock.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:*:${local.account_id}:inference-profile/*",
          "arn:aws:bedrock:*:*:inference-profile/*"
        ]
      }
    ]
  })
}

# --- Outputs ---

output "ecr_app_url" {
  value = module.ecr_app.repository_url
}

output "ecr_loadgen_url" {
  value = module.ecr_loadgen.repository_url
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "amp_workspace_id" {
  value = aws_prometheus_workspace.this.id
}

output "amp_endpoint" {
  value = aws_prometheus_workspace.this.prometheus_endpoint
}

output "observability_role_arn" {
  value = aws_iam_role.adot_collector.arn
}

output "app_role_arn" {
  value = aws_iam_role.app_bedrock.arn
}
