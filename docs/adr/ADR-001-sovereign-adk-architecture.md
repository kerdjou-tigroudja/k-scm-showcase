# ADR-001: Sovereign Multi-Agent Architecture on Google ADK 2.0 & Cloud Run europe-west9

* **Status:** Accepted
* **Deciders:** Kerdjou Tigroudja (Lead Architect)
* **Date:** 2026-08-20

## Context and Problem Statement
Enterprises deploying generative AI systems in the European Union face stringent regulatory obligations under the EU AI Act (Regulation 2024/1689) and GDPR (Regulation 2016/679). Manual compliance audits of code and cloud infrastructure are slow, costly, and error-prone. We require an automated, sovereign agentic system capable of auditing codebases and IaC manifests while enforcing strict data residency in France (`europe-west9`).

## Decision Drivers
* Strict European data sovereignty (data at rest, data in transit, compute strictly in `europe-west9`).
* High deterministic reproducibility of static code/IaC analysis.
* Interoperable agent communication using standard protocols (A2A, JSON-RPC streaming).
* Telemetry with automatic PII and secret redaction.

## Considered Options
1. Monolithic LLM prompt pipeline.
2. Multi-Agent System on Google Agent Development Kit (ADK 2.0) with specialized roles (Orchestrator, Auditor, RAG, ADR, GitOps).
3. LangChain/CrewAI generic agent graph.

## Decision Outcome
Chosen option: **Multi-Agent System on Google ADK 2.0 deployed on Cloud Run (`europe-west9`)**, because:
* ADK 2.0 provides first-class native integration with Google Cloud IAM, Vertex AI, and OpenTelemetry.
* Decomposing the system into specialized sub-agents (Static Auditor, Sovereign RAG, ADR Generator, GitOps Remediator) ensures isolated failure domains and deterministic evaluation.
* The system publishes an Agent-to-Agent (A2A) Card (`/.well-known/agent-card.json`) enabling seamless orchestration.
