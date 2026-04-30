"""Transform request/response records by modifying headers, body, or URL."""

from typing import Callable, List, Optional
from reqwatch.core import RequestRecord


def transform_url(record: RequestRecord, fn: Callable[[str], str]) -> RequestRecord:
    """Return a new record with the URL transformed by fn."""
    d = record.to_dict()
    d["url"] = fn(d.get("url", ""))
    return RequestRecord.from_dict(d)


def transform_request_headers(
    record: RequestRecord, fn: Callable[[dict], dict]
) -> RequestRecord:
    """Return a new record with request headers transformed by fn."""
    d = record.to_dict()
    d["request_headers"] = fn(dict(d.get("request_headers") or {}))
    return RequestRecord.from_dict(d)


def transform_response_headers(
    record: RequestRecord, fn: Callable[[dict], dict]
) -> RequestRecord:
    """Return a new record with response headers transformed by fn."""
    d = record.to_dict()
    d["response_headers"] = fn(dict(d.get("response_headers") or {}))
    return RequestRecord.from_dict(d)


def transform_body(record: RequestRecord, fn: Callable[[Optional[str]], Optional[str]]) -> RequestRecord:
    """Return a new record with the request body transformed by fn."""
    d = record.to_dict()
    d["body"] = fn(d.get("body"))
    return RequestRecord.from_dict(d)


def apply_transforms(
    records: List[RequestRecord],
    transforms: List[Callable[[RequestRecord], RequestRecord]],
) -> List[RequestRecord]:
    """Apply a sequence of transform functions to every record in the list."""
    result = []
    for record in records:
        current = record
        for transform in transforms:
            current = transform(current)
        result.append(current)
    return result


def replace_host(record: RequestRecord, old_host: str, new_host: str) -> RequestRecord:
    """Replace old_host with new_host in the record URL."""
    return transform_url(record, lambda url: url.replace(old_host, new_host, 1))


def set_request_header(record: RequestRecord, key: str, value: str) -> RequestRecord:
    """Set a specific request header key to value."""
    def _set(headers: dict) -> dict:
        headers[key] = value
        return headers
    return transform_request_headers(record, _set)


def remove_request_header(record: RequestRecord, key: str) -> RequestRecord:
    """Remove a specific request header key if present."""
    def _remove(headers: dict) -> dict:
        headers.pop(key, None)
        return headers
    return transform_request_headers(record, _remove)


def transform_summary(original: List[RequestRecord], transformed: List[RequestRecord]) -> str:
    """Return a short summary of how many records were transformed."""
    changed = sum(
        1 for o, t in zip(original, transformed) if o.to_dict() != t.to_dict()
    )
    return f"Transformed {changed}/{len(original)} records."
