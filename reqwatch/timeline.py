"""Timeline view: sort and display requests in chronological order."""

from typing import List, Optional
from datetime import datetime
from reqwatch.core import RequestRecord


def sort_by_time(records: List[RequestRecord], reverse: bool = False) -> List[RequestRecord]:
    """Sort records by timestamp, ascending by default."""
    return sorted(records, key=lambda r: r.timestamp, reverse=reverse)


def bucket_by_second(records: List[RequestRecord]) -> dict:
    """Group records into buckets keyed by truncated second (ISO string)."""
    buckets: dict = {}
    for record in records:
        try:
            dt = datetime.fromisoformat(record.timestamp)
            key = dt.strftime("%Y-%m-%dT%H:%M:%S")
        except (ValueError, TypeError):
            key = "unknown"
        buckets.setdefault(key, []).append(record)
    return buckets


def timeline_summary(records: List[RequestRecord], limit: Optional[int] = None) -> List[str]:
    """Return a list of formatted lines representing the request timeline."""
    sorted_records = sort_by_time(records)
    if limit is not None:
        sorted_records = sorted_records[:limit]

    lines = []
    for record in sorted_records:
        status = record.response_status or "---"
        method = (record.method or "???").upper()
        url = record.url or ""
        ts = record.timestamp or "unknown"
        lines.append(f"[{ts}] {method} {url} -> {status}")
    return lines


def time_range(records: List[RequestRecord]):
    """Return (earliest_timestamp, latest_timestamp) strings, or (None, None)."""
    if not records:
        return None, None
    sorted_records = sort_by_time(records)
    return sorted_records[0].timestamp, sorted_records[-1].timestamp
