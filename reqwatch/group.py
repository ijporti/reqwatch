"""Group and aggregate RequestRecords by various dimensions."""

from collections import defaultdict
from typing import Dict, List, Callable
from reqwatch.core import RequestRecord


def group_by_method(records: List[RequestRecord]) -> Dict[str, List[RequestRecord]]:
    """Group records by HTTP method."""
    groups: Dict[str, List[RequestRecord]] = defaultdict(list)
    for record in records:
        groups[record.method.upper()].append(record)
    return dict(groups)


def group_by_status(records: List[RequestRecord]) -> Dict[int, List[RequestRecord]]:
    """Group records by HTTP status code."""
    groups: Dict[int, List[RequestRecord]] = defaultdict(list)
    for record in records:
        groups[record.status_code].append(record)
    return dict(groups)


def group_by_host(records: List[RequestRecord]) -> Dict[str, List[RequestRecord]]:
    """Group records by host extracted from URL."""
    from urllib.parse import urlparse
    groups: Dict[str, List[RequestRecord]] = defaultdict(list)
    for record in records:
        parsed = urlparse(record.url)
        host = parsed.netloc or parsed.path
        groups[host].append(record)
    return dict(groups)


def group_by(records: List[RequestRecord],
             key_fn: Callable[[RequestRecord], str]) -> Dict[str, List[RequestRecord]]:
    """Group records by an arbitrary key function."""
    groups: Dict[str, List[RequestRecord]] = defaultdict(list)
    for record in records:
        groups[key_fn(record)].append(record)
    return dict(groups)


def group_summary(groups: Dict) -> Dict[str, int]:
    """Return a dict mapping each group key to its record count."""
    return {str(k): len(v) for k, v in groups.items()}
