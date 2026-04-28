"""Retry logic for replaying failed requests with configurable backoff."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from reqwatch.core import RequestRecord
from reqwatch.replay import ReplayResult, replay_request


@dataclass
class RetryResult:
    record: RequestRecord
    attempts: List[ReplayResult] = field(default_factory=list)
    final: Optional[ReplayResult] = None

    @property
    def succeeded(self) -> bool:
        return self.final is not None and self.final.success

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)

    def summary(self) -> str:
        status = "OK" if self.succeeded else "FAILED"
        return (
            f"{self.record.method} {self.record.url} "
            f"[{status}] after {self.total_attempts} attempt(s)"
        )


def retry_request(
    record: RequestRecord,
    max_retries: int = 3,
    backoff: float = 0.5,
    retry_on: Optional[Callable[[ReplayResult], bool]] = None,
) -> RetryResult:
    """Replay a request, retrying on failure up to max_retries times."""
    if retry_on is None:
        retry_on = lambda r: not r.success

    result = RetryResult(record=record)
    for attempt in range(1, max_retries + 1):
        res = replay_request(record)
        result.attempts.append(res)
        if not retry_on(res):
            result.final = res
            return result
        if attempt < max_retries:
            time.sleep(backoff * attempt)

    result.final = result.attempts[-1]
    return result


def retry_all(
    records: List[RequestRecord],
    max_retries: int = 3,
    backoff: float = 0.5,
) -> List[RetryResult]:
    """Retry all records and return their retry results."""
    return [retry_request(r, max_retries=max_retries, backoff=backoff) for r in records]


def retry_summary(results: List[RetryResult]) -> str:
    total = len(results)
    succeeded = sum(1 for r in results if r.succeeded)
    failed = total - succeeded
    avg_attempts = (
        sum(r.total_attempts for r in results) / total if total else 0.0
    )
    return (
        f"Retry summary: {total} request(s), "
        f"{succeeded} succeeded, {failed} failed, "
        f"avg {avg_attempts:.1f} attempt(s)"
    )
