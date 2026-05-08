"""Schedule-based replay: replay stored requests on a cron-like interval."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.core import RequestRecord
from reqwatch.replay import ReplayResult, replay_request


@dataclass
class ScheduleResult:
    runs: int
    results: List[ReplayResult]
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"Schedule failed: {self.error}"
        total = len(self.results)
        ok = sum(1 for r in self.results if r.success())
        return (
            f"Scheduled {self.runs} run(s): {total} request(s) replayed, "
            f"{ok} succeeded, {total - ok} failed."
        )


def run_schedule(
    records: List[RequestRecord],
    runs: int,
    interval_seconds: float = 1.0,
    dry_run: bool = False,
) -> ScheduleResult:
    """Replay *records* *runs* times, pausing *interval_seconds* between runs."""
    if runs < 1:
        return ScheduleResult(runs=0, results=[], error="runs must be >= 1")
    if interval_seconds < 0:
        return ScheduleResult(runs=0, results=[], error="interval_seconds must be >= 0")

    all_results: List[ReplayResult] = []
    for i in range(runs):
        for record in records:
            if dry_run:
                all_results.append(
                    ReplayResult(record=record, status_code=None, error=None, elapsed=0.0)
                )
            else:
                all_results.append(replay_request(record))
        if i < runs - 1 and interval_seconds > 0:
            time.sleep(interval_seconds)

    return ScheduleResult(runs=runs, results=all_results)


def schedule_summary(result: ScheduleResult) -> str:
    return result.summary()
