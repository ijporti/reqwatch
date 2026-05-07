"""Split a RequestStore into multiple stores by a given criterion."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from reqwatch.core import RequestRecord, RequestStore


@dataclass
class SplitResult:
    buckets: Dict[str, List[RequestRecord]] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"Split failed: {self.error}"
        total = sum(len(v) for v in self.buckets.values())
        parts = len(self.buckets)
        return f"Split {total} record(s) into {parts} bucket(s): " + ", ".join(
            f"{k}={len(v)}" for k, v in sorted(self.buckets.items())
        )


def split_by(records: List[RequestRecord], criterion: str) -> SplitResult:
    """Split records into buckets keyed by *criterion*.

    Supported criteria: ``method``, ``status``, ``host``.
    """
    buckets: Dict[str, List[RequestRecord]] = {}

    if criterion == "method":
        key_fn = lambda r: (r.method or "UNKNOWN").upper()
    elif criterion == "status":
        key_fn = lambda r: str(r.response_status) if r.response_status else "none"
    elif criterion == "host":
        def key_fn(r: RequestRecord) -> str:  # type: ignore[misc]
            try:
                from urllib.parse import urlparse
                return urlparse(r.url).hostname or "unknown"
            except Exception:
                return "unknown"
    else:
        return SplitResult(error=f"Unknown criterion: {criterion!r}")

    for record in records:
        key = key_fn(record)
        buckets.setdefault(key, []).append(record)

    return SplitResult(buckets=buckets)


def split_summary(result: SplitResult) -> str:
    return result.summary()
