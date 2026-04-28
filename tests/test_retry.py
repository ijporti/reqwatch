"""Tests for reqwatch.retry module."""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from reqwatch.core import RequestRecord
from reqwatch.replay import ReplayResult
from reqwatch.retry import (
    RetryResult,
    retry_request,
    retry_all,
    retry_summary,
)


def _make_record(**kwargs) -> RequestRecord:
    defaults = dict(
        id="abc123",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        method="GET",
        url="http://example.com/api",
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body="ok",
        duration_ms=50.0,
        metadata={},
    )
    defaults.update(kwargs)
    return RequestRecord(**defaults)


def _make_replay_result(error=None, status=200):
    record = _make_record(response_status=status)
    return ReplayResult(record=record, status_code=status, body="ok", error=error)


class TestRetryResult:
    def test_succeeded_when_final_success(self):
        rr = RetryResult(record=_make_record())
        rr.final = _make_replay_result()
        assert rr.succeeded is True

    def test_not_succeeded_when_final_error(self):
        rr = RetryResult(record=_make_record())
        rr.final = _make_replay_result(error="timeout")
        assert rr.succeeded is False

    def test_not_succeeded_when_no_final(self):
        rr = RetryResult(record=_make_record())
        assert rr.succeeded is False

    def test_total_attempts_counts_list(self):
        rr = RetryResult(record=_make_record())
        rr.attempts = [_make_replay_result(), _make_replay_result()]
        assert rr.total_attempts == 2

    def test_summary_ok(self):
        rr = RetryResult(record=_make_record())
        rr.attempts = [_make_replay_result()]
        rr.final = _make_replay_result()
        assert "OK" in rr.summary()
        assert "1 attempt" in rr.summary()

    def test_summary_failed(self):
        rr = RetryResult(record=_make_record())
        rr.attempts = [_make_replay_result(error="err")] * 3
        rr.final = _make_replay_result(error="err")
        assert "FAILED" in rr.summary()


class TestRetryRequest:
    @patch("reqwatch.retry.replay_request")
    @patch("reqwatch.retry.time.sleep")
    def test_succeeds_on_first_attempt(self, mock_sleep, mock_replay):
        mock_replay.return_value = _make_replay_result()
        record = _make_record()
        result = retry_request(record, max_retries=3, backoff=0.1)
        assert result.succeeded
        assert result.total_attempts == 1
        mock_sleep.assert_not_called()

    @patch("reqwatch.retry.replay_request")
    @patch("reqwatch.retry.time.sleep")
    def test_retries_on_failure_then_succeeds(self, mock_sleep, mock_replay):
        fail = _make_replay_result(error="err")
        ok = _make_replay_result()
        mock_replay.side_effect = [fail, ok]
        result = retry_request(_make_record(), max_retries=3, backoff=0.0)
        assert result.succeeded
        assert result.total_attempts == 2

    @patch("reqwatch.retry.replay_request")
    @patch("reqwatch.retry.time.sleep")
    def test_exhausts_all_retries(self, mock_sleep, mock_replay):
        mock_replay.return_value = _make_replay_result(error="err")
        result = retry_request(_make_record(), max_retries=3, backoff=0.0)
        assert not result.succeeded
        assert result.total_attempts == 3


def test_retry_all_returns_one_result_per_record():
    records = [_make_record(id=str(i)) for i in range(4)]
    with patch("reqwatch.retry.replay_request") as mock_replay:
        mock_replay.return_value = _make_replay_result()
        results = retry_all(records, max_retries=1, backoff=0.0)
    assert len(results) == 4


def test_retry_summary_all_success():
    rr = RetryResult(record=_make_record())
    rr.attempts = [_make_replay_result()]
    rr.final = _make_replay_result()
    summary = retry_summary([rr, rr])
    assert "2 request" in summary
    assert "2 succeeded" in summary
    assert "0 failed" in summary


def test_retry_summary_empty():
    summary = retry_summary([])
    assert "0 request" in summary
