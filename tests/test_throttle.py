"""Tests for reqwatch.throttle."""

import time
from unittest.mock import patch

import pytest

from reqwatch.throttle import (
    ThrottleConfig,
    ThrottleResult,
    throttle_records,
    throttle_summary,
)
from reqwatch.core import RequestRecord


def _make_record(method="GET", url="http://example.com", status=200):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
    )


class TestThrottleConfig:
    def test_delay_for_10_rps(self):
        cfg = ThrottleConfig(requests_per_second=10.0)
        assert abs(cfg.delay_seconds() - 0.1) < 1e-9

    def test_delay_for_1_rps(self):
        cfg = ThrottleConfig(requests_per_second=1.0)
        assert abs(cfg.delay_seconds() - 1.0) < 1e-9

    def test_zero_rps_returns_zero_delay(self):
        cfg = ThrottleConfig(requests_per_second=0)
        assert cfg.delay_seconds() == 0.0

    def test_min_delay_respected(self):
        cfg = ThrottleConfig(requests_per_second=100.0, min_delay=0.05)
        assert cfg.delay_seconds() == 0.05


class TestThrottleResult:
    def test_actual_rps_zero_when_no_elapsed(self):
        r = ThrottleResult(dispatched=5, elapsed=0.0)
        assert r.actual_rps == 0.0

    def test_actual_rps_calculated(self):
        r = ThrottleResult(dispatched=10, elapsed=2.0)
        assert abs(r.actual_rps - 5.0) < 1e-9

    def test_summary_contains_dispatched(self):
        r = ThrottleResult(total=5, dispatched=5, dropped=0, elapsed=1.0)
        assert "5/5" in r.summary()

    def test_summary_contains_rps(self):
        r = ThrottleResult(total=4, dispatched=4, dropped=0, elapsed=2.0)
        assert "2.00 req/s" in r.summary()


class TestThrottleRecords:
    def test_all_dispatched_no_limit(self):
        records = [_make_record() for _ in range(5)]
        cfg = ThrottleConfig(requests_per_second=0, burst=10)
        result = throttle_records(records, cfg)
        assert result.dispatched == 5
        assert result.dropped == 0

    def test_max_records_limits_dispatch(self):
        records = [_make_record() for _ in range(10)]
        cfg = ThrottleConfig(requests_per_second=0, burst=10)
        result = throttle_records(records, cfg, max_records=4)
        assert result.dispatched == 4
        assert result.dropped == 6

    def test_burst_skips_initial_delays(self):
        records = [_make_record() for _ in range(3)]
        cfg = ThrottleConfig(requests_per_second=1.0, burst=3)
        with patch("reqwatch.throttle.time.sleep") as mock_sleep:
            throttle_records(records, cfg)
            mock_sleep.assert_not_called()

    def test_sleep_called_after_burst(self):
        records = [_make_record() for _ in range(4)]
        cfg = ThrottleConfig(requests_per_second=10.0, burst=2)
        with patch("reqwatch.throttle.time.sleep") as mock_sleep:
            throttle_records(records, cfg)
            assert mock_sleep.call_count == 2

    def test_empty_records(self):
        result = throttle_records([], ThrottleConfig())
        assert result.total == 0
        assert result.dispatched == 0


def test_throttle_summary_contains_rps():
    cfg = ThrottleConfig(requests_per_second=5.0, burst=2, min_delay=0.0)
    s = throttle_summary(cfg)
    assert "5.0 req/s" in s
    assert "burst=2" in s
