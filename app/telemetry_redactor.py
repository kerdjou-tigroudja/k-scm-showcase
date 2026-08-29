"""Telemetry Data Sanitization and Secret Redaction for K-SCM (F08-KSCM-TELEMETRY-003)."""

import re
from typing import Any

# Compiled regex patterns for detecting and redacting sensitive data & secrets
_PATTERNS = [
    # GCP / Google API Keys (e.g. AIzaSy followed by 20-50 alphanumeric/dash/underscore chars)
    (re.compile(r"AIzaSy[A-Za-z0-9_\-]{20,50}"), "[REDACTED_GCP_KEY]"),
    # Bearer Tokens
    (re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # Generic API Keys / Passwords / Secrets in key=val or key:val format (e.g. db_password, api_secret, auth_token)
    (
        re.compile(
            r"(?i)\b([A-Za-z0-9_]*(?:key|secret|token|password|passwd|pwd))\s*[:=]\s*['\"]?([A-Za-z0-9_\-.~]{6,})['\"]?"
        ),
        r"\1=[REDACTED_SECRET]",
    ),
    # Email addresses (PII)
    (
        re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "[REDACTED_EMAIL]",
    ),
    # IPv4 addresses (PII / Infra internal IPs)
    (
        re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
        "[REDACTED_IP]",
    ),
]


def redact_text(text: str | None) -> str:
    """Sanitizes text by replacing sensitive secrets, API keys, tokens, and PII with redaction placeholders."""
    if not text:
        return ""
    sanitized = str(text)
    for pattern, replacement in _PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def redact_attributes(attributes: dict[str, Any] | None) -> dict[str, str]:
    """Sanitizes OpenTelemetry span attributes or logging metadata dictionaries."""
    if not attributes:
        return {}

    sanitized_attrs: dict[str, str] = {}
    for key, value in attributes.items():
        clean_key = redact_text(str(key))
        clean_val = redact_text(str(value))
        sanitized_attrs[clean_key] = clean_val

    return sanitized_attrs
