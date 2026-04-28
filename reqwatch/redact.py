"""redact.py — Utilities for redacting sensitive data from request records.

Provides helpers to mask headers (e.g. Authorization, Cookie) and body
fields so that logs can be shared safely without leaking credentials.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

from reqwatch.core import RequestRecord

# Headers that are redacted by default
DEFAULT_SENSITIVE_HEADERS: List[str] = [
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "proxy-authorization",
]

REDACT_PLACEHOLDER = "[REDACTED]"


def redact_headers(
    headers: Dict[str, str],
    sensitive: Optional[Iterable[str]] = None,
) -> Dict[str, str]:
    """Return a copy of *headers* with sensitive values replaced.

    Header name matching is case-insensitive.

    Args:
        headers: Original header mapping.
        sensitive: Iterable of header names to redact.  Defaults to
            :data:`DEFAULT_SENSITIVE_HEADERS`.

    Returns:
        New dict with sensitive header values replaced by
        :data:`REDACT_PLACEHOLDER`.
    """
    if sensitive is None:
        sensitive = DEFAULT_SENSITIVE_HEADERS
    sensitive_lower = {h.lower() for h in sensitive}
    return {
        k: (REDACT_PLACEHOLDER if k.lower() in sensitive_lower else v)
        for k, v in headers.items()
    }


def redact_body(
    body: Optional[str],
    patterns: Iterable[str],
) -> Optional[str]:
    """Replace occurrences of regex *patterns* in *body* with the placeholder.

    Useful for scrubbing tokens or passwords embedded in request/response
    bodies without fully removing the body content.

    Args:
        body: Raw body string (may be ``None``).
        patterns: Regular expression patterns whose matches will be replaced.

    Returns:
        Redacted body string, or ``None`` if *body* was ``None``.
    """
    if body is None:
        return None
    result = body
    for pattern in patterns:
        result = re.sub(pattern, REDACT_PLACEHOLDER, result)
    return result


def redact_record(
    record: RequestRecord,
    sensitive_headers: Optional[Iterable[str]] = None,
    body_patterns: Optional[Iterable[str]] = None,
) -> RequestRecord:
    """Return a *new* :class:`~reqwatch.core.RequestRecord` with sensitive
    data redacted.

    The original record is **not** mutated.

    Args:
        record: The request record to sanitise.
        sensitive_headers: Header names to redact.  Defaults to
            :data:`DEFAULT_SENSITIVE_HEADERS`.
        body_patterns: Optional regex patterns applied to the request body.

    Returns:
        A shallow-copied record with redacted headers and body.
    """
    new_req_headers = redact_headers(record.request_headers, sensitive_headers)
    new_resp_headers = redact_headers(record.response_headers, sensitive_headers)

    patterns = list(body_patterns) if body_patterns else []
    new_body = redact_body(record.body, patterns)

    return RequestRecord(
        id=record.id,
        timestamp=record.timestamp,
        method=record.method,
        url=record.url,
        request_headers=new_req_headers,
        body=new_body,
        status_code=record.status_code,
        response_headers=new_resp_headers,
        response_body=redact_body(record.response_body, patterns),
        duration_ms=record.duration_ms,
        metadata=dict(record.metadata),
    )


def redaction_summary(original: RequestRecord, redacted: RequestRecord) -> str:
    """Produce a human-readable summary of what was redacted.

    Args:
        original: The unmodified record.
        redacted: The record after redaction.

    Returns:
        A short multi-line string describing redacted headers and body changes.
    """
    lines: List[str] = [f"Redaction summary for record {original.id}:"]

    changed_req = [
        k for k in original.request_headers
        if original.request_headers[k] != redacted.request_headers.get(k)
    ]
    changed_resp = [
        k for k in original.response_headers
        if original.response_headers[k] != redacted.response_headers.get(k)
    ]

    if changed_req:
        lines.append(f"  Request headers redacted : {', '.join(changed_req)}")
    if changed_resp:
        lines.append(f"  Response headers redacted: {', '.join(changed_resp)}")
    if original.body != redacted.body:
        lines.append("  Request body was modified by pattern redaction.")
    if original.response_body != redacted.response_body:
        lines.append("  Response body was modified by pattern redaction.")
    if len(lines) == 1:
        lines.append("  Nothing redacted.")
    return "\n".join(lines)
