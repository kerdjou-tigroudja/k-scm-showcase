# ADR-003: Human-in-the-Loop GitOps Remediation Protocol

* **Status:** Accepted
* **Deciders:** Kerdjou Tigroudja (Lead Architect)
* **Date:** 2026-08-25

## Context and Problem Statement
Autonomous agents should never push unreviewed modifications directly into production branches. Every compliance fix must be auditable, explained via an Architectural Decision Record (MADR), and proposed via a pull request requiring human review.

## Decision Outcome
Chosen option: **Isolated GitOps Branching with Automated MADR Record Generation & Draft PR Submission**.
The GitOps agent creates an ephemeral branch (e.g. `fix/compliance-madr-0001`), commits the remediated code/IaC alongside a standardized MADR record in `docs/adr/`, and opens a Draft Pull Request for human review.
