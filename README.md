# Multi-Agent AI Observability on Kubernetes

End-to-end OTel tracing, Bedrock cost attribution, and Grafana Tempo
visualization for LangGraph, CrewAI, and AWS Strands agents on EKS.

## What problem this solves
Multi-agent AI systems are black boxes — no visibility into which agent
drove cost, which tool call added latency, or which LLM invocation failed.
This platform instruments all three frameworks without modifying agent code.

## Architecture
```
┌─────────────────────────────────────────────────────────────────────────┐
│  EKS Cluster                                                             │
│                                                                          │
│  ┌─────────────────────────────────┐     ┌────────────────────────────┐ │
│  │  FastAPI App                     │     │  ADOT Collector             │ │
│  │                                  │────▶│  (receives OTLP)            │ │
│  │  Supervisor (LangGraph)          │     │                             │ │
│  │    ├── Order Agent (LangGraph)   │     │  Exports:                   │ │
│  │    ├── Billing Agent (CrewAI)    │     │    traces → Tempo           │ │
│  │    └── Tech Support (Strands)    │     │    metrics → AMP            │ │
│  │                                  │     └──────┬─────────┬────────────┘ │
│  └─────────────────────────────────┘            │         │              │
│                                                  ▼         │              │
│  ┌──────────────┐                    ┌──────────────┐     │              │
│  │  Load Gen     │                    │  Tempo        │     │              │
│  │  (0.5 RPS)   │                    │  (traces)     │     │              │
│  └──────────────┘                    └──────────────┘     │              │
│                                                            │              │
│  ┌──────────────────────────────────────────────────────┐ │              │
│  │  Grafana 12.4                                         │ │              │
│  │  ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────────┐  │ │              │
│  │  │Developer │ │FinOps  │ │Business│ │Observability│  │ │              │
│  │  │  /SRE    │ │        │ │        │ │  Traces     │  │ │              │
│  │  └──────────┘ └────────┘ └────────┘ └────────────┘  │ │              │
│  └──────────────────────────────────────────────────────┘ │              │
└───────────────────────────────────────────────────────────┼──────────────┘
                                                             │
                                                             ▼
                                              ┌──────────────────────────┐
                                              │  Amazon Managed           │
                                              │  Prometheus (AMP)         │
                                              │                           │
                                              │  SigV4 remote_write       │
                                              └──────────────────────────┘
```

## Key components
- boto3 interceptor for Bedrock token attribution (framework-agnostic)
- OTel auto-instrumentation across LangGraph/CrewAI/Strands
- Grafana dashboards: per-agent cost, latency, token usage
- EKS + Terraform deployment (Karpenter auto-provisioning)

## Article
[Medium deep dive](https://medium.com/@sivagurunath/end-to-end-observability-for-multi-agent-ai-systems-on-kubernetes-e4133dd111d6)
