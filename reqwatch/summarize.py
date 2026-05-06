"""Summarize a collection of RequestRecords into a human-readable report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from reqwatch.core import RequestRecord


@dataclass
class SummarizeResult:
    total: int
    method_counts: Dict[str, int]
    status_counts: Dict[int, int]
    error_count: int
    unique_hosts: List[str]
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Total requests : {self.total}",
            f"Unique hosts   : {len(self.unique_hosts)}",
            f"Errors (5xx)   : {self.error_count}",
        ]
        if self.method_counts:
            method_line = ", ".join(
                f"{m}={c}" for m, c in sorted(self.method_counts.items())
            )
            lines.append(f"Methods        : {method_line}")
        if self.status_counts:
            status_line = ", ".join(
                f"{s}={c}" for s, c in sorted(self.status_counts.items())
            )
            lines.append(f"Status codes   : {status_line}")
        if self.notes:
            for note in self.notes:
                lines.append(f"Note           : {note}")
        return "\n".join(lines)


def summarize_records(records: List[RequestRecord]) -> SummarizeResult:
    """Compute a SummarizeResult from a list of RequestRecords."""
    method_counts: Dict[str, int] = {}
    status_counts: Dict[int, int] = {}
    hosts: set = set()
    error_count = 0
    notes: List[str] = []

    for rec in records:
        method = (rec.method or "UNKNOWN").upper()
        method_counts[method] = method_counts.get(method, 0) + 1

        status = rec.response_status
        if status is not None:
            status_counts[status] = status_counts.get(status, 0) + 1
            if status >= 500:
                error_count += 1

        try:
            from urllib.parse import urlparse
            host = urlparse(rec.url).netloc
            if host:
                hosts.add(host)
        except Exception:
            pass

    if not records:
        notes.append("No records to summarize.")
    elif error_count > 0:
        pct = round(100 * error_count / len(records), 1)
        notes.append(f"{pct}% of requests returned a server error.")

    return SummarizeResult(
        total=len(records),
        method_counts=method_counts,
        status_counts=status_counts,
        error_count=error_count,
        unique_hosts=sorted(hosts),
        notes=notes,
    )
