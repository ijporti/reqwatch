"""Slice a request store to a sub-range by index or timestamp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from reqwatch.core import RequestRecord


@dataclass
class SliceResult:
    records: List[RequestRecord]
    original_count: int
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"Slice failed: {self.error}"
        kept = len(self.records)
        dropped = self.original_count - kept
        return f"Sliced {self.original_count} records → kept {kept}, dropped {dropped}"


def slice_by_index(
    records: List[RequestRecord],
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> SliceResult:
    """Return records[start:end] using standard Python slice semantics."""
    original_count = len(records)
    try:
        sliced = records[start:end]
    except Exception as exc:  # pragma: no cover
        return SliceResult(records=[], original_count=original_count, error=str(exc))
    return SliceResult(records=list(sliced), original_count=original_count)


def slice_by_timestamp(
    records: List[RequestRecord],
    after: Optional[str] = None,
    before: Optional[str] = None,
) -> SliceResult:
    """Return records whose timestamp falls within [after, before] (ISO strings)."""
    original_count = len(records)
    result = []
    for rec in records:
        ts = rec.timestamp or ""
        if after and ts < after:
            continue
        if before and ts > before:
            continue
        result.append(rec)
    return SliceResult(records=result, original_count=original_count)


def slice_head(records: List[RequestRecord], n: int) -> SliceResult:
    """Return the first *n* records."""
    return slice_by_index(records, start=None, end=max(0, n))


def slice_tail(records: List[RequestRecord], n: int) -> SliceResult:
    """Return the last *n* records."""
    n = max(0, n)
    start = len(records) - n if n < len(records) else 0
    return slice_by_index(records, start=start, end=None)
