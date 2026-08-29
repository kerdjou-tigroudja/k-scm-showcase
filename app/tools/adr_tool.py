"""
ADK Tool for generating MADR v3 Architecture Decision Records (ADRs) in English.
"""

from datetime import UTC, datetime
from typing import Any


def generate_madr_adr(
    title: str,
    context: str,
    legal_citations: list[dict[str, Any]],
    considered_options: list[str],
    chosen_option: str,
    rationale: str,
    remediation_patch: str,
    compliance_tags: list[str] | None = None,
    adr_number: str = "0001",
) -> str:
    """Generates an Architecture Decision Record (ADR) conforming strictly to the English MADR v3 standard.

    Args:
        title: Short title describing the remediation decision (e.g. 'Enforce CMEK Encryption on Vertex AI Buckets').
        context: Detailed explanation of the detected non-compliance or vulnerability in IaC / Python code.
        legal_citations: List of regulatory chunks or dictionary items returned by query_regulatory_rag (containing doc_id, article_num, legal_text).
        considered_options: List of alternative solutions evaluated (e.g. ['Status Quo / Non-compliant', 'Enable Cloud KMS CMEK']).
        chosen_option: The selected remediation solution.
        rationale: Technical and legal justification for choosing the selected option.
        remediation_patch: Terraform HCL or Python unified diff patch fixing the vulnerability.
        compliance_tags: List of compliance tags (e.g. ['EU-AI-ACT-ART-15', 'GDPR-ART-32', 'SecNumCloud']).
        adr_number: Sequential ADR number identifier (default: '0001').

    Returns:
        Complete Markdown string formatted as an English MADR v3 ADR document.
    """
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    tags_str = ", ".join(compliance_tags) if compliance_tags else "EU-AI-ACT, GDPR"

    # Format legal citations
    citations_md = []
    if legal_citations:
        for idx, cite in enumerate(legal_citations, start=1):
            doc = cite.get("document") or cite.get("doc_id", "EU Regulation")
            art = cite.get("article_or_recital") or cite.get("article_num", "")
            text = cite.get("legal_text") or cite.get("content", "")
            citations_md.append(f"### Citation {idx}: {doc} {art}\n> {text.strip()}\n")
        formatted_citations = "\n".join(citations_md)
    else:
        formatted_citations = "_No explicit regulatory citations attached._"

    # Format considered options
    options_md = "\n".join([f"* {opt}" for opt in considered_options])

    # Build MADR v3 document
    madr_content = f"""# [ADR-{adr_number}] {title}

* **Status:** Accepted
* **Deciders:** K-SCM Sovereign Compliance Mesh Agent, SecDevOps Team
* **Date:** {date_str}
* **Compliance Tags:** `{tags_str}`

## Context and Problem Statement
{context}

## Decision Drivers
* EU AI Act & GDPR Regulatory Compliance
* SecNumCloud Sovereign Infrastructure Standards (`europe-west9`)
* Automated Remediation via Human-in-the-Loop GitOps Pull Requests

## Regulatory & Legal Justification (RAG Anchored)
{formatted_citations}

## Considered Options
{options_md}

## Decision Outcome
**Chosen Option:** {chosen_option}

### Technical Rationale
{rationale}

### Remediation Patch
```diff
{remediation_patch.strip()}
```

## Consequences

### Positive Consequences
* Ensures strict compliance with regulatory requirements (`{tags_str}`).
* Protects against major regulatory penalties under EU AI Act and GDPR.
* Provides full auditability and traceable architecture records in `docs/adr/`.

### Negative Consequences / Trade-offs
* Requires manual human engineer review and merge on GitHub (Human-in-the-Loop).
"""
    return madr_content
