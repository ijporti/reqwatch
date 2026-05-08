"""Generate human-readable summary reports from a RequestStore."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.core import RequestStore
from reqwatch.stats import compute_stats
from reqwatch.group import group_by_method, group_by_status


@dataclass
class ReportResult:
    title: str
    total: int
    method_counts: dict
    status_counts: dict
    top_urls: List[str]
    error_rate: float
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"Report failed: {self.error}"
        lines = [
            f"=== {self.title} ===",
            f"Total requests : {self.total}",
            f"Error rate     : {self.error_rate:.1%}",
            "Methods        : "
            + ", ".join(f"{m}={c}" for m, c in sorted(self.method_counts.items())),
            "Status codes   : "
            + ", ".join(f"{s}={c}" for s, c in sorted(self.status_counts.items())),
        ]
        if self.top_urls:
            lines.append("Top URLs:")
            for url in self.top_urls:
                lines.append(f"  {url}")
        return "\n".join(lines)


def _top_urls(store: RequestStore, n: int = 5) -> List[str]:
    from collections import Counter
    counts: Counter = Counter(r.url for r in store.records)
    return [url for url, _ in counts.most_common(n)]


def generate_report(store: RequestStore, title: str = "Request Report", top_n: int = 5) -> ReportResult:
    try:
        stats = compute_stats(store.records)
        error_count = sum(
            1 for r in store.records
            if r.response_status is not None and r.response_status >= 400
        )
        total = stats.total
        error_rate = error_count / total if total > 0 else 0.0
        top_urls = _top_urls(store, top_n)
        return ReportResult(
            title=title,
            total=total,
            method_counts=dict(stats.method_counts),
            status_counts=dict(stats.status_counts),
            top_urls=top_urls,
            error_rate=error_rate,
        )
    except Exception as exc:  # pragma: no cover
        return ReportResult(
            title=title,
            total=0,
            method_counts={},
            status_counts={},
            top_urls=[],
            error_rate=0.0,
            error=str(exc),
        )
