"""Trim records from a store by count or date range."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from reqwatch.core import RequestRecord


@dataclass
class TrimResult:
    original_count: int
    trimmed_count: int
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"Trim failed: {self.error}"
        removed = self.original_count - self.trimmed_count
        return (
            f"Trimmed {removed} record(s): "
            f"{self.original_count} -> {self.trimmed_count}"
        )


def trim_to_last_n(
    records: List[RequestRecord], n: int
) -> TrimResult:
    """Keep only the most recent *n* records (by timestamp)."""
    if n < 0:
        return TrimResult(
            original_count=len(records),
            trimmed_count=len(records),
            error="n must be >= 0",
        )
    original = len(records)
    sorted_records = sorted(records, key=lambda r: r.timestamp)
    kept = sorted_records[-n:] if n > 0 else []
    records[:] = kept
    return TrimResult(original_count=original, trimmed_count=len(kept))


def trim_before(
    records: List[RequestRecord], cutoff: datetime
) -> TrimResult:
    """Remove all records whose timestamp is before *cutoff*."""
    original = len(records)
    kept = [r for r in records if r.timestamp >= cutoff.isoformat()]
    records[:] = kept
    return TrimResult(original_count=original, trimmed_count=len(kept))


def trim_after(
    records: List[RequestRecord], cutoff: datetime
) -> TrimResult:
    """Remove all records whose timestamp is after *cutoff*."""
    original = len(records)
    kept = [r for r in records if r.timestamp <= cutoff.isoformat()]
    records[:] = kept
    return TrimResult(original_count=original, trimmed_count=len(kept))
