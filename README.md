# 🏛️ K-SCM — Sovereign Compliance Mesh

[![GCP europe-west9](https://img.shields.io/badge/GCP_Region-europe--west9_(Paris)-blue?logo=googlecloud&logoColor=white)](https://cloud.google.com/about/locations/paris)
[![Google ADK 2.0](https://img.shields.io/badge/Google_ADK-2.0-4285F4?logo=google&logoColor=white)](https://cloud.google.com/products/agent-development-kit)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Live Cloud Run](https://img.shields.io/badge/Live_Service-Cloud_Run_Live-brightgreen)](https://k-scm-gjaydimv2q-od.a.run.app/.well-known/agent-card.json)

> **Autonomous multi-agent compliance mesh for automated EU AI Act & GDPR audits, architectural decision generation (MADR), and Human-in-the-Loop GitOps remediation on Google Cloud Platform.**

Developed by **[Kerdjou Tigroudja](https://kerdjou.dev)** (`contact@kerdjou.dev`).

---

## 📌 Executive Overview

**K-SCM (Sovereign Compliance Mesh)** is an enterprise-grade agentic system designed to help engineering and compliance teams automatically audit software codebases and Terraform IaC configurations against strict European regulations (**EU AI Act — Regulation 2024/1689** and **GDPR — Regulation 2016/679**).

### Key Differentiators:
1. **Strict European Data Sovereignty :** Compute (Cloud Run), storage (Cloud Storage CMEK), vector embeddings (AlloyDB pgvector), and telemetry (BigQuery) are hosted strictly in the **`europe-west9` (Paris, France)** region.
2. **Multi-Agent Orchestration (Google ADK 2.0) :** Specialized autonomous agents coordinate via standardized protocols (Agent-to-Agent A2A Card, JSON-RPC streaming).
3. **Human-in-the-Loop GitOps Remediation :** Generates non-destructive pull requests containing corrected source files and formal Architectural Decision Records (MADR) for peer review.
4. **Privacy-Preserving Telemetry :** Custom OpenTelemetry & BigQuery redacting pipeline ensuring 0% token leakage of secrets, API keys, or personal data.

---

## 🏗️ System Architecture

```mermaid
graph TD
    classDef client fill:#E1F5FE,stroke:#0288D1,stroke-width:2px,color:#000;
    classDef agent fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
    classDef gcp fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000;
    classDef target fill:#EDE7F6,stroke:#512DA8,stroke-width:2px,color:#000;

    Client["A2A Client / Webhook / CI/CD"]:::client

    subgraph CloudRun ["⚡ Cloud Run Service (europe-west9)"]
        FastAPIApp["FastAPI Server & A2A Handler<br>/.well-known/agent-card.json"]:::agent
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

    subgraph SovereignStorage ["🔒 GCP Sovereign Infrastructure (europe-west9)"]
        AlloyDB[("AlloyDB pgvector<br>EU AI Act & GDPR Embeddings")]:::gcp
        BigQuery[("BigQuery Agent Analytics<br>Redacted Telemetry & FinOps")]:::gcp
        KMS["Cloud KMS (CMEK Keys)"]:::gcp
    end

    subgraph SandboxTarget ["🎯 Target Repository (Audited & Remediated)"]
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

## 🚀 Live Production Endpoints

K-SCM is live and deployed in production on Google Cloud Run:

| Endpoint | Description | URL |
|---|---|---|
| **Agent-to-Agent (A2A) Card** | Machine-readable capabilities descriptor | [`https://k-scm-gjaydimv2q-od.a.run.app/.well-known/agent-card.json`](https://k-scm-gjaydimv2q-od.a.run.app/.well-known/agent-card.json) |
| **A2A Streaming Protocol** | JSON-RPC 2.0 streaming agent execution | `https://k-scm-gjaydimv2q-od.a.run.app/a2a/app/` |
| **Health Probe** | Service readiness & location verification | `https://k-scm-gjaydimv2q-od.a.run.app/health` |

---

## 💻 Local Quickstart & Test Suite

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

---

## 📄 Architectural Decision Records (MADR)

Key architectural decisions are documented in [`docs/adr/`](docs/adr/):
- **[ADR-001: Sovereign Multi-Agent Architecture on Google ADK 2.0](docs/adr/ADR-001-sovereign-adk-architecture.md)**
- **[ADR-002: Sovereign Regulatory Vector Store using AlloyDB pgvector](docs/adr/ADR-002-alloydb-pgvector-retrieval.md)**
- **[ADR-003: Human-in-the-Loop GitOps Remediation Protocol](docs/adr/ADR-003-human-in-the-loop-gitops-remediation.md)**

---

## 🔗 Related Repositories & Portfolio

* **Target Sandbox Repository :** [`kerdjou-tigroudja/k-scm-mock-target-showcase`](https://github.com/kerdjou-tigroudja/k-scm-mock-target-showcase)
* **Official Web Hub :** [https://kerdjou.dev](https://kerdjou.dev)
* **Author Contact :** [contact@kerdjou.dev](mailto:contact@kerdjou.dev)
