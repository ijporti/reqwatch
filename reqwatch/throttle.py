"""Rate-limiting utilities for replay and export operations."""

import time
from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.core import RequestRecord


@dataclass
class ThrottleConfig:
    requests_per_second: float = 10.0
    burst: int = 1
    min_delay: float = 0.0

    def delay_seconds(self) -> float:
        """Return the base inter-request delay in seconds."""
        if self.requests_per_second <= 0:
            return 0.0
        return max(self.min_delay, 1.0 / self.requests_per_second)


@dataclass
class ThrottleResult:
    total: int = 0
    dispatched: int = 0
    dropped: int = 0
    elapsed: float = 0.0
    delays: List[float] = field(default_factory=list)

    @property
    def actual_rps(self) -> float:
        if self.elapsed <= 0:
            return 0.0
        return self.dispatched / self.elapsed

    def summary(self) -> str:
        return (
            f"Throttle: {self.dispatched}/{self.total} dispatched, "
            f"{self.dropped} dropped, "
            f"{self.actual_rps:.2f} req/s over {self.elapsed:.2f}s"
        )


def throttle_records(
    records: List[RequestRecord],
    config: ThrottleConfig,
    max_records: Optional[int] = None,
) -> ThrottleResult:
    """Yield records at a controlled rate, returning a ThrottleResult summary."""
    result = ThrottleResult(total=len(records))
    delay = config.delay_seconds()
    burst_remaining = config.burst
    start = time.monotonic()

    limit = max_records if max_records is not None else len(records)
    for i, _record in enumerate(records):
        if i >= limit:
            result.dropped += len(records) - i
            break
        if burst_remaining > 0:
            burst_remaining -= 1
        elif delay > 0:
            time.sleep(delay)
            result.delays.append(delay)
        result.dispatched += 1

    result.elapsed = time.monotonic() - start
    return result


def throttle_summary(config: ThrottleConfig) -> str:
    return (
        f"ThrottleConfig: {config.requests_per_second} req/s, "
        f"burst={config.burst}, min_delay={config.min_delay}s"
    )
