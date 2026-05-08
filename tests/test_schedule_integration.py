"""Integration tests for the schedule feature."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.schedule import run_schedule


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api",
    status_code: int = 200,
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={"Accept": "application/json"},
        request_body=None,
        response_status=status_code,
        response_headers={"Content-Type": "application/json"},
        response_body='{"ok": true}',
        timestamp="2024-06-01T12:00:00Z",
        metadata={},
    )


class TestScheduleIntegration:
    def test_dry_run_multiple_methods(self):
        records = [
            _make_record(method="GET"),
            _make_record(method="POST"),
            _make_record(method="DELETE", status_code=204),
        ]
        result = run_schedule(records, runs=2, interval_seconds=0, dry_run=True)
        assert result.succeeded()
        assert len(result.results) == 6

    def test_single_record_single_run(self):
        result = run_schedule(
            [_make_record()], runs=1, interval_seconds=0, dry_run=True
        )
        assert result.runs == 1
        assert len(result.results) == 1

    def test_summary_shows_all_succeeded_on_dry_run(self):
        records = [_make_record() for _ in range(4)]
        result = run_schedule(records, runs=1, interval_seconds=0, dry_run=True)
        assert "4" in result.summary()
        assert "failed" in result.summary()

    def test_zero_runs_error_propagates(self):
        result = run_schedule([_make_record()], runs=0, dry_run=True)
        assert not result.succeeded()
        assert result.error is not None
