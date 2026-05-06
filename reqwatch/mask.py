"""Masking utilities for sensitive values in request/response records."""

from __future__ import annotations

import re
from typing import Any

from reqwatch.core import RequestRecord

_DEFAULT_MASK = "***"
_SENSITIVE_KEYS = frozenset(
    {"authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token"}
)


def mask_headers(
    headers: dict[str, str],
    keys: list[str] | None = None,
    mask: str = _DEFAULT_MASK,
) -> dict[str, str]:
    """Return a copy of *headers* with sensitive values replaced by *mask*.

    Args:
        headers: The headers dict to process.
        keys: Additional header names (case-insensitive) to mask beyond the
            built-in sensitive key list.
        mask: The replacement string for masked values.
    """
    target = {k.lower() for k in (keys or [])} | _SENSITIVE_KEYS
    return {
        k: (mask if k.lower() in target else v)
        for k, v in headers.items()
    }


def mask_body(
    body: str | None,
    patterns: list[str],
    mask: str = _DEFAULT_MASK,
) -> str:
    """Replace all regex *patterns* found in *body* with *mask*.

    Args:
        body: The body string to process. Returns an empty string if ``None``.
        patterns: A list of regex patterns whose matches will be replaced.
        mask: The replacement string for matched substrings.

    Raises:
        re.error: If any entry in *patterns* is not a valid regular expression.
    """
    if not body:
        return body or ""
    result = body
    for pattern in patterns:
        result = re.sub(pattern, mask, result)
    return result


def mask_record(
    record: RequestRecord,
    header_keys: list[str] | None = None,
    body_patterns: list[str] | None = None,
    mask: str = _DEFAULT_MASK,
) -> RequestRecord:
    """Return a new :class:`RequestRecord` with sensitive data masked."""
    d: dict[str, Any] = {
        "id": record.id,
        "timestamp": record.timestamp,
        "method": record.method,
        "url": record.url,
        "request_headers": mask_headers(record.request_headers, header_keys, mask),
        "request_body": mask_body(record.request_body, body_patterns or [], mask),
        "status_code": record.status_code,
        "response_headers": mask_headers(record.response_headers, header_keys, mask),
        "response_body": mask_body(record.response_body, body_patterns or [], mask),
        "duration_ms": record.duration_ms,
        "metadata": dict(record.metadata),
    }
    return RequestRecord(**d)


def mask_summary(original: RequestRecord, masked: RequestRecord) -> str:
    """Return a human-readable summary of what was masked."""
    req_h = sum(
        1 for k in original.request_headers
        if masked.request_headers.get(k) != original.request_headers[k]
    )
    res_h = sum(
        1 for k in original.response_headers
        if masked.response_headers.get(k) != original.response_headers[k]
    )
    body_changed = (
        original.request_body != masked.request_body
        or original.response_body != masked.response_body
    )
    parts = []
    if req_h:
        parts.append(f"{req_h} request header(s) masked")
    if res_h:
        parts.append(f"{res_h} response header(s) masked")
    if body_changed:
        parts.append("body pattern(s) masked")
    return ", ".join(parts) if parts else "nothing masked"
