"""Filtering utilities for RequestStore records."""

from __future__ import annotations

import re
from typing import Callable, Iterable, List, Optional

from reqwatch.core import RequestRecord


def filter_by_method(records: Iterable[RequestRecord], method: str) -> List[RequestRecord]:
    """Return records matching the given HTTP method (case-insensitive)."""
    method_upper = method.upper()
    return [r for r in records if r.method.upper() == method_upper]


def filter_by_status(records: Iterable[RequestRecord], status: int) -> List[RequestRecord]:
    """Return records whose response status code matches."""
    return [r for r in records if r.status_code == status]


def filter_by_url_pattern(records: Iterable[RequestRecord], pattern: str) -> List[RequestRecord]:
    """Return records whose URL matches the given regex pattern."""
    compiled = re.compile(pattern)
    return [r for r in records if compiled.search(r.url)]


def filter_by_status_range(
    records: Iterable[RequestRecord],
    min_status: int = 100,
    max_status: int = 599,
) -> List[RequestRecord]:
    """Return records whose status code falls within [min_status, max_status]."""
    return [r for r in records if min_status <= r.status_code <= max_status]


def apply_filters(
    records: Iterable[RequestRecord],
    method: Optional[str] = None,
    status: Optional[int] = None,
    url_pattern: Optional[str] = None,
    min_status: Optional[int] = None,
    max_status: Optional[int] = None,
) -> List[RequestRecord]:
    """Apply multiple optional filters in sequence and return matching records."""
    result: List[RequestRecord] = list(records)

    if method is not None:
        result = filter_by_method(result, method)
    if status is not None:
        result = filter_by_status(result, status)
    if url_pattern is not None:
        result = filter_by_url_pattern(result, url_pattern)
    if min_status is not None or max_status is not None:
        lo = min_status if min_status is not None else 100
        hi = max_status if max_status is not None else 599
        result = filter_by_status_range(result, lo, hi)

    return result
