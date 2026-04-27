"""Utilities for truncating and summarising long request/response bodies."""

from __future__ import annotations

from typing import Optional

DEFAULT_MAX_BYTES = 512


def truncate_body(body: Optional[str], max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    """Return *body* truncated to *max_bytes* characters.

    If the body is ``None`` or empty an empty string is returned.
    When truncation occurs a short notice is appended so the reader knows
    the content was cut.
    """
    if not body:
        return ""
    if len(body) <= max_bytes:
        return body
    snippet = body[:max_bytes]
    omitted = len(body) - max_bytes
    return f"{snippet}... [{omitted} chars truncated]"


def is_truncated(body: Optional[str], max_bytes: int = DEFAULT_MAX_BYTES) -> bool:
    """Return ``True`` when *body* would be truncated at *max_bytes*."""
    if not body:
        return False
    return len(body) > max_bytes


def truncate_headers(
    headers: dict[str, str],
    max_value_length: int = 128,
) -> dict[str, str]:
    """Return a copy of *headers* with long values truncated."""
    result: dict[str, str] = {}
    for key, value in headers.items():
        if len(value) > max_value_length:
            omitted = len(value) - max_value_length
            result[key] = f"{value[:max_value_length]}... [{omitted} chars truncated]"
        else:
            result[key] = value
    return result


def truncation_summary(body: Optional[str], max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    """Return a human-readable one-liner about the body size and truncation."""
    if not body:
        return "body: empty"
    size = len(body)
    if size <= max_bytes:
        return f"body: {size} chars (not truncated)"
    return f"body: {size} chars (truncated to {max_bytes})"
