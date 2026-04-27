"""Tests for reqwatch.stats module."""

import pytest
from reqwatch.stats import compute_stats, RequestStats
from reqwatch.core import RequestRecord


def _make_record(method="GET", url="http://example.com/api", status=200, body=""):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body="",
        response_status=status,
        response_headers={},
        response_body=body,
    )


class TestComputeStatsEmpty:
    def test_empty_returns_zero_total(self):
        stats = compute_stats([])
        assert stats.total == 0

    def test_empty_returns_empty_dicts(self):
        stats = compute_stats([])
        assert stats.by_method == {}
        assert stats.by_status == {}


class TestComputeStatsCounts:
    def test_total_count(self):
        records = [_make_record() for _ in range(5)]
        stats = compute_stats(records)
        assert stats.total == 5

    def test_method_grouping(self):
        records = [
            _make_record(method="GET"),
            _make_record(method="GET"),
            _make_record(method="POST"),
        ]
        stats = compute_stats(records)
        assert stats.by_method["GET"] == 2
        assert stats.by_method["POST"] == 1

    def test_method_case_normalized(self):
        records = [_make_record(method="get"), _make_record(method="GET")]
        stats = compute_stats(records)
        assert stats.by_method.get("GET") == 2

    def test_status_grouping(self):
        records = [
            _make_record(status=200),
            _make_record(status=200),
            _make_record(status=404),
        ]
        stats = compute_stats(records)
        assert stats.by_status[200] == 2
        assert stats.by_status[404] == 1

    def test_success_count(self):
        records = [_make_record(status=200), _make_record(status=201), _make_record(status=404)]
        stats = compute_stats(records)
        assert stats.success_count == 2

    def test_error_count(self):
        records = [
            _make_record(status=400),
            _make_record(status=500),
            _make_record(status=200),
        ]
        stats = compute_stats(records)
        assert stats.error_count == 2

    def test_urls_collected(self):
        records = [_make_record(url="http://a.com"), _make_record(url="http://b.com")]
        stats = compute_stats(records)
        assert "http://a.com" in stats.urls
        assert "http://b.com" in stats.urls


class TestRequestStatsSummary:
    def test_summary_contains_total(self):
        stats = RequestStats(total=3, success_count=2, error_count=1)
        assert "3" in stats.summary()

    def test_summary_contains_method(self):
        stats = RequestStats(total=1, by_method={"GET": 1})
        assert "GET" in stats.summary()

    def test_summary_contains_status(self):
        stats = RequestStats(total=1, by_status={200: 1})
        assert "200" in stats.summary()
