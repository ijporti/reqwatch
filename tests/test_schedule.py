"""Tests for reqwatch.schedule."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.replay import ReplayResult
from reqwatch.schedule import ScheduleResult, run_schedule, schedule_summary


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api",
    status_code: int = 200,
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status_code,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00Z",
        metadata={},
    )


def _make_replay_result(error: str | None = None) -> ReplayResult:
    return ReplayResult(
        record=_make_record(),
        status_code=200 if error is None else None,
        error=error,
        elapsed=0.01,
    )


class TestScheduleResult:
    def test_succeeded_when_no_error(self):
        r = ScheduleResult(runs=1, results=[])
        assert r.succeeded() is True

    def test_not_succeeded_when_error(self):
        r = ScheduleResult(runs=0, results=[], error="bad")
        assert r.succeeded() is False

    def test_summary_contains_run_count(self):
        r = ScheduleResult(runs=3, results=[_make_replay_result(), _make_replay_result()])
        assert "3" in r.summary()

    def test_summary_shows_failed_count(self):
        r = ScheduleResult(
            runs=1,
            results=[_make_replay_result(), _make_replay_result(error="timeout")],
        )
        assert "1 failed" in r.summary()

    def test_summary_error_message(self):
        r = ScheduleResult(runs=0, results=[], error="runs must be >= 1")
        assert "runs must be >= 1" in r.summary()


def test_invalid_runs_returns_error():
    result = run_schedule([], runs=0, dry_run=True)
    assert result.succeeded() is False
    assert "runs" in result.error


def test_negative_interval_returns_error():
    result = run_schedule([], runs=1, interval_seconds=-1.0, dry_run=True)
    assert result.succeeded() is False


def test_dry_run_does_not_raise():
    records = [_make_record(), _make_record(method="POST")]
    result = run_schedule(records, runs=2, interval_seconds=0, dry_run=True)
    assert result.succeeded() is True
    assert len(result.results) == 4  # 2 records * 2 runs


def test_dry_run_single_run():
    records = [_make_record()]
    result = run_schedule(records, runs=1, interval_seconds=0, dry_run=True)
    assert result.runs == 1
    assert len(result.results) == 1


def test_empty_records_zero_results():
    result = run_schedule([], runs=3, interval_seconds=0, dry_run=True)
    assert result.runs == 3
    assert result.results == []


def test_schedule_summary_delegates():
    r = ScheduleResult(runs=1, results=[_make_replay_result()])
    assert schedule_summary(r) == r.summary()
