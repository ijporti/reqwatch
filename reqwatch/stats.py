"""Statistics and summary reporting for captured request records."""

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict

from reqwatch.core import RequestRecord


@dataclass
class RequestStats:
    total: int = 0
    by_method: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[int, int] = field(default_factory=dict)
    error_count: int = 0
    success_count: int = 0
    urls: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Total requests : {self.total}",
            f"Successes (2xx): {self.success_count}",
            f"Errors (4xx/5xx): {self.error_count}",
            "By method:",
        ]
        for method, count in sorted(self.by_method.items()):
            lines.append(f"  {method}: {count}")
        lines.append("By status:")
        for status, count in sorted(self.by_status.items()):
            lines.append(f"  {status}: {count}")
        return "\n".join(lines)


def compute_stats(records: List[RequestRecord]) -> RequestStats:
    """Compute aggregate statistics from a list of RequestRecord objects."""
    if not records:
        return RequestStats()

    method_counter: Counter = Counter()
    status_counter: Counter = Counter()
    error_count = 0
    success_count = 0

    for rec in records:
        method_counter[rec.method.upper()] += 1
        if rec.response_status is not None:
            status_counter[rec.response_status] += 1
            if 200 <= rec.response_status < 300:
                success_count += 1
            elif rec.response_status >= 400:
                error_count += 1

    return RequestStats(
        total=len(records),
        by_method=dict(method_counter),
        by_status=dict(status_counter),
        error_count=error_count,
        success_count=success_count,
        urls=[rec.url for rec in records],
    )
