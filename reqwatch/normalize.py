"""Normalize request records for consistent comparison and storage."""

from typing import List, Optional
from reqwatch.core import RequestRecord


def normalize_method(record: RequestRecord) -> RequestRecord:
    """Return a copy of the record with the HTTP method uppercased."""
    updated = record.to_dict()
    updated["method"] = updated.get("method", "GET").upper()
    return RequestRecord.from_dict(updated)


def normalize_url(record: RequestRecord, strip_trailing_slash: bool = True) -> RequestRecord:
    """Return a copy of the record with the URL normalized.

    Strips trailing slashes and lowercases the scheme and host.
    """
    updated = record.to_dict()
    url: str = updated.get("url", "")

    # Lowercase scheme and host portion
    if "://" in url:
        scheme, rest = url.split("://", 1)
        scheme = scheme.lower()
        if "/" in rest:
            host, path = rest.split("/", 1)
            host = host.lower()
            url = f"{scheme}://{host}/{path}"
        else:
            url = f"{scheme}://{rest.lower()}"

    if strip_trailing_slash and url.endswith("/") and url.count("/") > 2:
        url = url.rstrip("/")

    updated["url"] = url
    return RequestRecord.from_dict(updated)


def normalize_headers(
    record: RequestRecord,
    lowercase_names: bool = True,
    remove_keys: Optional[List[str]] = None,
) -> RequestRecord:
    """Return a copy of the record with headers normalized.

    Optionally lowercases header names and removes specified keys.
    """
    updated = record.to_dict()
    remove_keys_lower = {k.lower() for k in (remove_keys or [])}

    def _clean(headers: dict) -> dict:
        result = {}
        for k, v in headers.items():
            key = k.lower() if lowercase_names else k
            if key not in remove_keys_lower:
                result[key] = v
        return result

    updated["request_headers"] = _clean(updated.get("request_headers") or {})
    updated["response_headers"] = _clean(updated.get("response_headers") or {})
    return RequestRecord.from_dict(updated)


def apply_normalizations(
    record: RequestRecord,
    strip_trailing_slash: bool = True,
    lowercase_headers: bool = True,
    remove_header_keys: Optional[List[str]] = None,
) -> RequestRecord:
    """Apply all normalizations to a record in sequence."""
    record = normalize_method(record)
    record = normalize_url(record, strip_trailing_slash=strip_trailing_slash)
    record = normalize_headers(
        record,
        lowercase_names=lowercase_headers,
        remove_keys=remove_header_keys,
    )
    return record


def normalization_summary(original: RequestRecord, normalized: RequestRecord) -> str:
    """Return a human-readable summary of changes made during normalization."""
    changes = []
    if original.method != normalized.method:
        changes.append(f"method: {original.method!r} -> {normalized.method!r}")
    if original.url != normalized.url:
        changes.append(f"url: {original.url!r} -> {normalized.url!r}")
    if (original.request_headers or {}) != (normalized.request_headers or {}):
        changes.append("request_headers normalized")
    if (original.response_headers or {}) != (normalized.response_headers or {}):
        changes.append("response_headers normalized")
    if not changes:
        return "No changes during normalization."
    return "Normalized: " + "; ".join(changes) + "."
