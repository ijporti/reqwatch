"""Tests for reqwatch.slice."""

from __future__ import annotations

from reqwatch.core import RequestRecord
from reqwatch.slice import (
    SliceResult,
    slice_by_index,
    slice_by_timestamp,
    slice_head,
    slice_tail,
)


def _make_record(method: str = "GET", url: str = "http://example.com", timestamp: str = "2024-01-01T00:00:00") -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        status_code=200,
        request_headers={},
        response_headers={},
        request_body=None,
        response_body=None,
        timestamp=timestamp,
        duration_ms=10.0,
        metadata={},
    )


class TestSliceResult:
    def test_succeeded_when_no_error(self):
        r = SliceResult(records=[], original_count=0)
        assert r.succeeded() is True

    def test_not_succeeded_when_error(self):
        r = SliceResult(records=[], original_count=0, error="oops")
        assert r.succeeded() is False

    def test_summary_success(self):
        records = [_make_record()]
        r = SliceResult(records=records, original_count=5)
        s = r.summary()
        assert "5" in s
        assert "1" in s
        assert "4" in s

    def test_summary_error(self):
        r = SliceResult(records=[], original_count=3, error="bad input")
        assert "bad input" in r.summary()


class TestSliceByIndex:
    def test_returns_all_when_no_bounds(self):
        records = [_make_record() for _ in range(5)]
        result = slice_by_index(records)
        assert len(result.records) == 5

    def test_respects_start(self):
        records = [_make_record(url=f"http://example.com/{i}") for i in range(5)]
        result = slice_by_index(records, start=2)
        assert len(result.records) == 3
        assert result.records[0].url == "http://example.com/2"

    def test_respects_end(self):
        records = [_make_record(url=f"http://example.com/{i}") for i in range(5)]
        result = slice_by_index(records, end=3)
        assert len(result.records) == 3

    def test_original_count_preserved(self):
        records = [_make_record() for _ in range(10)]
        result = slice_by_index(records, start=2, end=5)
        assert result.original_count == 10


class TestSliceByTimestamp:
    def test_after_filters_older(self):
        records = [
            _make_record(timestamp="2024-01-01T00:00:00"),
            _make_record(timestamp="2024-06-01T00:00:00"),
            _make_record(timestamp="2024-12-01T00:00:00"),
        ]
        result = slice_by_timestamp(records, after="2024-03-01T00:00:00")
        assert len(result.records) == 2

    def test_before_filters_newer(self):
        records = [
            _make_record(timestamp="2024-01-01T00:00:00"),
            _make_record(timestamp="2024-06-01T00:00:00"),
        ]
        result = slice_by_timestamp(records, before="2024-03-01T00:00:00")
        assert len(result.records) == 1

    def test_empty_list_returns_empty(self):
        result = slice_by_timestamp([], after="2024-01-01T00:00:00")
        assert result.records == []
        assert result.original_count == 0


class TestSliceHeadTail:
    def test_head_returns_first_n(self):
        records = [_make_record(url=f"http://example.com/{i}") for i in range(10)]
        result = slice_head(records, 3)
        assert len(result.records) == 3
        assert result.records[0].url == "http://example.com/0"

    def test_tail_returns_last_n(self):
        records = [_make_record(url=f"http://example.com/{i}") for i in range(10)]
        result = slice_tail(records, 3)
        assert len(result.records) == 3
        assert result.records[-1].url == "http://example.com/9"

    def test_head_zero_returns_empty(self):
        records = [_make_record() for _ in range(5)]
        result = slice_head(records, 0)
        assert result.records == []

    def test_tail_larger_than_list(self):
        records = [_make_record() for _ in range(3)]
        result = slice_tail(records, 100)
        assert len(result.records) == 3
