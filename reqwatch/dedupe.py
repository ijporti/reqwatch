"""Deduplication utilities for identifying and removing duplicate requests."""

from typing import List, Dict, Tuple
from reqwatch.core import RequestRecord


def _request_fingerprint(record: RequestRecord) -> Tuple:
    """Return a tuple that uniquely identifies a request by method, URL, and body."""
    body = (record.request_body or "").strip()
    return (record.method.upper(), record.url, body)


def _response_fingerprint(record: RequestRecord) -> Tuple:
    """Return a tuple that identifies a request+response pair."""
    body = (record.request_body or "").strip()
    return (record.method.upper(), record.url, body, record.status_code)


def find_duplicates(records: List[RequestRecord], match_response: bool = False) -> Dict[Tuple, List[RequestRecord]]:
    """Group records by fingerprint; returns only groups with more than one record."""
    groups: Dict[Tuple, List[RequestRecord]] = {}
    fingerprint_fn = _response_fingerprint if match_response else _request_fingerprint
    for record in records:
        key = fingerprint_fn(record)
        groups.setdefault(key, []).append(record)
    return {k: v for k, v in groups.items() if len(v) > 1}


def deduplicate(records: List[RequestRecord], match_response: bool = False, keep: str = "first") -> List[RequestRecord]:
    """Return a deduplicated list of records.

    Args:
        records: List of RequestRecord objects.
        match_response: If True, also consider status_code when deduplicating.
        keep: 'first' keeps the earliest record; 'last' keeps the most recent.
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")

    fingerprint_fn = _response_fingerprint if match_response else _request_fingerprint
    seen: Dict[Tuple, RequestRecord] = {}

    for record in records:
        key = fingerprint_fn(record)
        if key not in seen:
            seen[key] = record
        elif keep == "last":
            seen[key] = record

    # Preserve original ordering for kept records
    kept_ids = {id(r) for r in seen.values()}
    return [r for r in records if id(r) in kept_ids]


def dedupe_summary(records: List[RequestRecord], match_response: bool = False) -> str:
    """Return a human-readable summary of duplicate statistics."""
    duplicates = find_duplicates(records, match_response=match_response)
    total_dupes = sum(len(v) - 1 for v in duplicates.values())
    unique_count = len(records) - total_dupes
    return (
        f"Total records: {len(records)} | "
        f"Unique: {unique_count} | "
        f"Duplicate groups: {len(duplicates)} | "
        f"Redundant records: {total_dupes}"
    )
