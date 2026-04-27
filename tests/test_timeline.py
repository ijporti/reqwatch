"""Tests for reqwatch.timeline module."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.timeline import (
    sort_by_time,
    bucket_by_second,
    timeline_summary,
    time_range,
)


def _make_record(ts: str, method: str = "GET", url: str = "http://example.com",
                 status: int = 200) -> RequestRecord:
    return RequestRecord(
        timestamp=ts,
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
    )


class TestSortByTime:
    def test_ascending_order(self):
        r1 = _make_record("2024-01-01T10:00:02")
        r2 = _make_record("2024-01-01T10:00:00")
        r3 = _make_record("2024-01-01T10:00:01")
        result = sort_by_time([r1, r2, r3])
        assert [r.timestamp for r in result] == [
            "2024-01-01T10:00:00",
            "2024-01-01T10:00:01",
            "2024-01-01T10:00:02",
        ]

    def test_descending_order(self):
        r1 = _make_record("2024-01-01T10:00:00")
        r2 = _make_record("2024-01-01T10:00:02")
        result = sort_by_time([r1, r2], reverse=True)
        assert result[0].timestamp == "2024-01-01T10:00:02"

    def test_empty_list(self):
        assert sort_by_time([]) == []


class TestBucketBySecond:
    def test_groups_same_second(self):
        r1 = _make_record("2024-01-01T10:00:01.000")
        r2 = _make_record("2024-01-01T10:00:01.500")
        buckets = bucket_by_second([r1, r2])
        assert len(buckets["2024-01-01T10:00:01"]) == 2

    def test_different_seconds(self):
        r1 = _make_record("2024-01-01T10:00:01")
        r2 = _make_record("2024-01-01T10:00:02")
        buckets = bucket_by_second([r1, r2])
        assert len(buckets) == 2

    def test_empty(self):
        assert bucket_by_second([]) == {}


class TestTimelineSummary:
    def test_returns_lines(self):
        r1 = _make_record("2024-01-01T10:00:00", method="GET", status=200)
        lines = timeline_summary([r1])
        assert len(lines) == 1
        assert "GET" in lines[0]
        assert "200" in lines[0]

    def test_sorted_output(self):
        r1 = _make_record("2024-01-01T10:00:02")
        r2 = _make_record("2024-01-01T10:00:00")
        lines = timeline_summary([r1, r2])
        assert "10:00:00" in lines[0]

    def test_limit_respected(self):
        records = [_make_record(f"2024-01-01T10:00:0{i}") for i in range(5)]
        lines = timeline_summary(records, limit=3)
        assert len(lines) == 3


class TestTimeRange:
    def test_returns_earliest_and_latest(self):
        r1 = _make_record("2024-01-01T10:00:00")
        r2 = _make_record("2024-01-01T10:00:05")
        r3 = _make_record("2024-01-01T10:00:03")
        earliest, latest = time_range([r1, r2, r3])
        assert earliest == "2024-01-01T10:00:00"
        assert latest == "2024-01-01T10:00:05"

    def test_empty_returns_none(self):
        assert time_range([]) == (None, None)
