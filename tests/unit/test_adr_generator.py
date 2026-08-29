"""
Unit tests for MADR ADR Generator tool.
"""

from app.tools.adr_tool import generate_madr_adr


def test_generate_madr_adr_structure():
    adr_output = generate_madr_adr(
        title="Enforce CMEK Encryption on Vertex AI Buckets",
        context="Buckets were created without Cloud KMS CMEK encryption keys.",
        legal_citations=[
            {
                "document": "EU_AI_ACT",
                "article_or_recital": "Article 15",
                "legal_text": "High-risk AI systems shall achieve high levels of cybersecurity.",
            }
        ],
        considered_options=["Status Quo", "Enable Cloud KMS CMEK"],
        chosen_option="Enable Cloud KMS CMEK",
        rationale="Guarantees zero-trust encryption compliant with SecNumCloud requirements.",
        remediation_patch="- kms_key_name = null\n+ kms_key_name = google_kms_crypto_key.cmek.id",
        compliance_tags=["EU-AI-ACT-ART-15", "GDPR-ART-32"],
        adr_number="0001",
    )

    assert "# [ADR-0001] Enforce CMEK Encryption on Vertex AI Buckets" in adr_output
    assert "* **Status:** Accepted" in adr_output
    assert "EU-AI-ACT-ART-15, GDPR-ART-32" in adr_output
    assert "### Citation 1: EU_AI_ACT Article 15" in adr_output
    assert (
        "High-risk AI systems shall achieve high levels of cybersecurity." in adr_output
    )
    assert "```diff" in adr_output
    assert "+ kms_key_name = google_kms_crypto_key.cmek.id" in adr_output
