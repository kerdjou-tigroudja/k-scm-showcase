# ADR-002: Sovereign Regulatory Vector Store using AlloyDB for PostgreSQL & pgvector

* **Status:** Accepted
* **Deciders:** Kerdjou Tigroudja (Lead Architect)
* **Date:** 2026-08-22

## Context and Problem Statement
The Sovereign Compliance Mesh requires instant, highly accurate retrieval of EU AI Act articles, recitals, and GDPR requirements to ground audit findings in official legal texts without hallucinations.

## Decision Outcome
Chosen option: **AlloyDB for PostgreSQL with pgvector extension in `europe-west9`**, using `text-embedding-004` (768 dimensions) with Customer-Managed Encryption Keys (CMEK) and Private Service Connect (PSC).
