# Multi-Agent AI Observability on Kubernetes

End-to-end OTel tracing, Bedrock cost attribution, and Grafana Tempo
visualization for LangGraph, CrewAI, and AWS Strands agents on EKS.

## What problem this solves
Multi-agent AI systems are black boxes — no visibility into which agent
drove cost, which tool call added latency, or which LLM invocation failed.
This platform instruments all three frameworks without modifying agent code.

## Architecture
[ASCII diagram or link to diagram image]
DCGM + OTel Collector → AMP → Grafana Tempo → per-agent cost dashboard

## Key components
- boto3 interceptor for Bedrock token attribution (framework-agnostic)
- OTel auto-instrumentation across LangGraph/CrewAI/Strands
- Grafana dashboards: per-agent cost, latency, token usage
- EKS + Terraform deployment (Karpenter auto-provisioning)

## Article
[Medium deep dive] (https://medium.com/@sivagurunath/end-to-end-observability-for-multi-agent-ai-systems-on-kubernetes-e4133dd111d6)
