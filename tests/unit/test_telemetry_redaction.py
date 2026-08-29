"""Synthetic unit tests for telemetry secret redaction and sanitization (KER-82 / F08-KSCM-TELEMETRY-003)."""

from app.telemetry_redactor import redact_attributes, redact_text


def test_redact_gcp_api_key():
    """Verify that Google/GCP API key patterns are redacted."""
    raw = "Failed request using key AIzaSyDummyTestKey123456789012345678"
    clean = redact_text(raw)
    assert "AIzaSy" not in clean
    assert "[REDACTED_GCP_KEY]" in clean


def test_redact_bearer_token():
    """Verify that Authorization Bearer headers are redacted."""
    raw = "Header Authorization: Bearer eyJhbGciOiJIUzI1NiR1c2VyIjoic3ludGhldGljIn0.test"
    clean = redact_text(raw)
    assert "eyJhbGci" not in clean
    assert "Bearer [REDACTED_TOKEN]" in clean


def test_redact_email_pii():
    """Verify that email addresses (PII) are redacted."""
    raw = "Audit assigned to engineer jane.doe@sovereign-compliance.eu for review"
    clean = redact_text(raw)
    assert "jane.doe@sovereign-compliance.eu" not in clean
    assert "[REDACTED_EMAIL]" in clean


def test_redact_ip_address():
    """Verify that IPv4 addresses are redacted."""
    raw = "Connected to internal node 192.168.1.105 on port 8080"
    clean = redact_text(raw)
    assert "192.168.1.105" not in clean
    assert "[REDACTED_IP]" in clean


def test_redact_generic_secrets():
    """Verify that generic secret=value parameters are redacted."""
    raw = "db_password='supersecretpass123' and api_secret='mysecrettokenvalue'"
    clean = redact_text(raw)
    assert "supersecretpass123" not in clean
    assert "mysecrettokenvalue" not in clean
    assert "[REDACTED_SECRET]" in clean


def test_redact_attributes_dictionary():
    """Verify that dictionary attributes are completely sanitized in keys and values."""
    attributes = {
        "user_email": "john.smith@synthetic.test",
        "api_key": "AIzaSyDummyTestKey123456789012345678",
        "normal_key": "safe_value_123",
        "auth": "Bearer eyJdummytokenvalue",
    }
    sanitized = redact_attributes(attributes)

    assert sanitized["user_email"] == "[REDACTED_EMAIL]"
    assert sanitized["api_key"] == "[REDACTED_GCP_KEY]"
    assert sanitized["normal_key"] == "safe_value_123"
    assert sanitized["auth"] == "Bearer [REDACTED_TOKEN]"
