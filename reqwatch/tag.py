"""Tag-based labeling and filtering for RequestRecord collections."""

from typing import List, Dict
from reqwatch.core import RequestRecord


def add_tag(record: RequestRecord, tag: str) -> RequestRecord:
    """Return a new RequestRecord with the given tag added to metadata."""
    tags = list(record.metadata.get("tags", []))
    if tag not in tags:
        tags.append(tag)
    new_meta = {**record.metadata, "tags": tags}
    return RequestRecord(
        id=record.id,
        timestamp=record.timestamp,
        method=record.method,
        url=record.url,
        request_headers=record.request_headers,
        request_body=record.request_body,
        response_status=record.response_status,
        response_headers=record.response_headers,
        response_body=record.response_body,
        duration_ms=record.duration_ms,
        metadata=new_meta,
    )


def remove_tag(record: RequestRecord, tag: str) -> RequestRecord:
    """Return a new RequestRecord with the given tag removed from metadata."""
    tags = [t for t in record.metadata.get("tags", []) if t != tag]
    new_meta = {**record.metadata, "tags": tags}
    return RequestRecord(
        id=record.id,
        timestamp=record.timestamp,
        method=record.method,
        url=record.url,
        request_headers=record.request_headers,
        request_body=record.request_body,
        response_status=record.response_status,
        response_headers=record.response_headers,
        response_body=record.response_body,
        duration_ms=record.duration_ms,
        metadata=new_meta,
    )


def get_tags(record: RequestRecord) -> List[str]:
    """Return the list of tags on a record."""
    return list(record.metadata.get("tags", []))


def filter_by_tag(records: List[RequestRecord], tag: str) -> List[RequestRecord]:
    """Return only records that have the specified tag."""
    return [r for r in records if tag in r.metadata.get("tags", [])]


def tag_summary(records: List[RequestRecord]) -> Dict[str, int]:
    """Return a dict mapping each tag to the number of records carrying it."""
    counts: Dict[str, int] = {}
    for record in records:
        for tag in record.metadata.get("tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return counts
