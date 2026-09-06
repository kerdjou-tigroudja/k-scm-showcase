# K-SCM — Sovereign Compliance Mesh

[![GCP europe-west9](https://img.shields.io/badge/GCP_Region-europe--west9_(Paris)-blue?logo=googlecloud&logoColor=white)](https://cloud.google.com/about/locations/paris)
[![Google ADK 2.0](https://img.shields.io/badge/Google_ADK-2.0-4285F4?logo=google&logoColor=white)](https://cloud.google.com/products/agent-development-kit)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Agent Card A2A](https://img.shields.io/badge/A2A_Protocol-Agent_Card_JSON-cyan)](docs/agent-card.json)
[![RAGAS Precision](https://img.shields.io/badge/RAGAS_Precision-0.9750-brightgreen)](https://github.com/kerdjou-tigroudja/k-scm-showcase)

> **Autonomous multi-agent compliance mesh for automated EU AI Act & GDPR audits, architectural decision generation (MADR), and Human-in-the-Loop GitOps remediation on Google Cloud Platform.**

Developed by **[Kerdjou Tigroudja](https://kerdjou.dev)** (`contact@kerdjou.dev`).

---

## Executive Overview

**K-SCM (Sovereign Compliance Mesh)** is an enterprise-grade agentic system designed to help engineering and compliance teams automatically audit software codebases and Terraform IaC configurations against strict European regulations (**EU AI Act — Regulation 2024/1689** and **GDPR — Regulation 2016/679**).

### Key Differentiators:
1. **Strict European Data Sovereignty :** Compute (Cloud Run), storage (Cloud Storage CMEK), vector embeddings (AlloyDB pgvector), and telemetry (BigQuery) are hosted strictly in the **`europe-west9` (Paris, France)** region.
2. **Multi-Agent Orchestration (Google ADK 2.0) :** Specialized autonomous agents coordinate via standardized protocols (Agent-to-Agent A2A Card, JSON-RPC streaming).
3. **Human-in-the-Loop GitOps Remediation :** Generates non-destructive pull requests containing corrected source files and formal Architectural Decision Records (MADR) for peer review.
4. **Zero-Trust Security & Private IAM :** Cloud Run endpoints enforce authenticated IAM invoker controls (`roles/run.invoker`) and VPC Service Controls, preventing unauthenticated public token leakage.

---

## System Architecture

```mermaid
graph TD
    classDef client fill:#E1F5FE,stroke:#0288D1,stroke-width:2px,color:#000;
    classDef agent fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
    classDef gcp fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000;
    classDef target fill:#EDE7F6,stroke:#512DA8,stroke-width:2px,color:#000;

    Client["A2A Client / Webhook / CI/CD"]:::client

    subgraph CloudRun ["Cloud Run Service (europe-west9)"]
        FastAPIApp["FastAPI Server & A2A Handler<br>/a2a/app/.well-known/agent-card.json"]:::agent
        Orchestrator["Root Orchestrator Agent<br>(Google ADK 2.0)"]:::agent
        
        Auditor["Static Code & IaC Auditor"]:::agent
        RAGAgent["Sovereign Legal RAG Agent"]:::agent
        ADRAgent["MADR Architecture Generator"]:::agent
        GitOpsAgent["GitOps Remediation Agent"]:::agent
        
        Orchestrator --> Auditor
        Orchestrator --> RAGAgent
        Orchestrator --> ADRAgent
        Orchestrator --> GitOpsAgent
    end

    subgraph SovereignStorage ["GCP Sovereign Infrastructure (europe-west9)"]
        AlloyDB[("AlloyDB pgvector<br>EU AI Act & GDPR Embeddings")]:::gcp
        BigQuery[("BigQuery Agent Analytics<br>Redacted Telemetry & FinOps")]:::gcp
        KMS["Cloud KMS (CMEK Keys)"]:::gcp
    end

    subgraph SandboxTarget ["Target Repository (Audited & Remediated)"]
        MockRepo["Target Codebase<br>(e.g. k-scm-mock-target-showcase)"]:::target
        PullRequest["Human-in-the-Loop PR<br>(fix/compliance-madr-0001)"]:::target
    end

    Client --> FastAPIApp
    FastAPIApp --> Orchestrator
    RAGAgent <--> AlloyDB
    GitOpsAgent -->|Scans & Remediates| MockRepo
    GitOpsAgent -->|Opens Draft PR + MADR| PullRequest
    Orchestrator -.->|Sanitized Spans & Metrics| BigQuery
```

---

## Live Production & A2A Endpoints

| Resource | Description | Location / Access |
|---|---|---|
| **A2A Agent Card** | Machine-readable capabilities descriptor | [docs/agent-card.json](docs/agent-card.json) |
| **Cloud Run Production Service** | Authenticated Serverless Node | `europe-west9 (Paris, France)` |
| **Live Remediation Example** | Draft PR #1 with MADR v3 ADR | [k-scm-mock-target-showcase #1](https://github.com/kerdjou-tigroudja/k-scm-mock-target-showcase/pull/1) |
| **A2A JSON-RPC Streaming** | Agent execution endpoint | `/a2a/app` (IAM Authenticated) |

> [!NOTE]
> **Security Notice (Zero-Trust Ingress) :** In alignment with SecNumCloud isolation principles and enterprise Zero-Trust architectures, the live Cloud Run service enforces private IAM authentication (`roles/run.invoker`). Unauthenticated requests are rejected by design (HTTP 403 Forbidden). Authorized clients pass a Google Cloud OAuth2 Bearer token in the `Authorization` header.

---

## Local Quickstart & Test Suite

### 1. Prerequisites
- Python 3.12+
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 2. Setup & Installation
```bash
git clone https://github.com/kerdjou-tigroudja/k-scm-showcase.git
cd k-scm-showcase

# Install dependencies in isolated virtual environment
uv sync
```

### 3. Run Autonomous Unit Test Suite (38 tests, 100% Mocked/Offline)
```bash
uv run pytest tests/unit/ -v
```
*(Note: The full enterprise mesh validates 62/62 integration tests and 99 unit tests in internal qualification environments).*

---

## Architectural Decision Records (MADR)

Key architectural decisions are documented in [`docs/adr/`](docs/adr/):
- **[ADR-001: Sovereign Multi-Agent Architecture on Google ADK 2.0](docs/adr/ADR-001-sovereign-adk-architecture.md)**
- **[ADR-002: Sovereign Regulatory Vector Store using AlloyDB pgvector](docs/adr/ADR-002-alloydb-pgvector-retrieval.md)**
- **[ADR-003: Human-in-the-Loop GitOps Remediation Protocol](docs/adr/ADR-003-human-in-the-loop-gitops-remediation.md)**

---

## Related Repositories & Portfolio

* **Target Sandbox Repository :** [`kerdjou-tigroudja/k-scm-mock-target-showcase`](https://github.com/kerdjou-tigroudja/k-scm-mock-target-showcase)
* **Official Web Hub :** [https://kerdjou.dev](https://kerdjou.dev)
* **Author Contact :** [contact@kerdjou.dev](mailto:contact@kerdjou.dev)
