"""Pivot request records by a chosen dimension for tabular analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from reqwatch.core import RequestRecord

VALID_DIMENSIONS = ("method", "status", "host", "path")


@dataclass
class PivotResult:
    dimension: str
    table: Dict[str, List[RequestRecord]] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def has_error(self) -> bool:
        return self.error is not None

    def summary(self) -> str:
        if self.has_error:
            return f"Pivot error: {self.error}"
        total = sum(len(v) for v in self.table.values())
        rows = len(self.table)
        return (
            f"Pivot by '{self.dimension}': {rows} group(s), {total} record(s) total"
        )


def _key_for(record: RequestRecord, dimension: str) -> str:
    if dimension == "method":
        return (record.method or "UNKNOWN").upper()
    if dimension == "status":
        return str(record.response_status or "none")
    if dimension == "host":
        url = record.url or ""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc or "unknown"
        except Exception:
            return "unknown"
    if dimension == "path":
        url = record.url or ""
        try:
            from urllib.parse import urlparse
            return urlparse(url).path or "/"
        except Exception:
            return "/"
    return "unknown"


def pivot(records: List[RequestRecord], dimension: str) -> PivotResult:
    """Group *records* into a pivot table keyed by *dimension*."""
    if dimension not in VALID_DIMENSIONS:
        return PivotResult(
            dimension=dimension,
            error=f"Unknown dimension '{dimension}'. Choose from: {', '.join(VALID_DIMENSIONS)}",
        )
    table: Dict[str, List[RequestRecord]] = {}
    for rec in records:
        key = _key_for(rec, dimension)
        table.setdefault(key, []).append(rec)
    return PivotResult(dimension=dimension, table=table)


def pivot_summary(result: PivotResult) -> str:
    """Return a human-readable breakdown of each pivot group."""
    if result.has_error:
        return result.summary()
    lines = [result.summary()]
    for key in sorted(result.table):
        count = len(result.table[key])
        lines.append(f"  {key}: {count}")
    return "\n".join(lines)
