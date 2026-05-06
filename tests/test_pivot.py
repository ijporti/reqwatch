"""Tests for reqwatch.pivot."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.pivot import (
    VALID_DIMENSIONS,
    PivotResult,
    pivot,
    pivot_summary,
)


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api",
    status: int = 200,
) -> RequestRecord:
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


class TestPivotResult:
    def test_has_error_false_when_no_error(self):
        r = PivotResult(dimension="method")
        assert r.has_error is False

    def test_has_error_true_when_error_set(self):
        r = PivotResult(dimension="method", error="oops")
        assert r.has_error is True

    def test_summary_no_error(self):
        r = PivotResult(dimension="method", table={"GET": [_make_record()]})
        s = r.summary()
        assert "method" in s
        assert "1 group" in s
        assert "1 record" in s

    def test_summary_with_error(self):
        r = PivotResult(dimension="method", error="bad dim")
        assert "bad dim" in r.summary()


class TestPivotByMethod:
    def test_groups_by_method(self):
        records = [
            _make_record(method="GET"),
            _make_record(method="POST"),
            _make_record(method="get"),
        ]
        result = pivot(records, "method")
        assert not result.has_error
        assert len(result.table["GET"]) == 2
        assert len(result.table["POST"]) == 1

    def test_empty_records(self):
        result = pivot([], "method")
        assert result.table == {}
        assert not result.has_error


class TestPivotByStatus:
    def test_groups_by_status(self):
        records = [
            _make_record(status=200),
            _make_record(status=404),
            _make_record(status=200),
        ]
        result = pivot(records, "status")
        assert len(result.table["200"]) == 2
        assert len(result.table["404"]) == 1


class TestPivotByHost:
    def test_groups_by_host(self):
        records = [
            _make_record(url="http://alpha.com/x"),
            _make_record(url="http://beta.com/y"),
            _make_record(url="http://alpha.com/z"),
        ]
        result = pivot(records, "host")
        assert len(result.table["alpha.com"]) == 2
        assert len(result.table["beta.com"]) == 1


class TestPivotByPath:
    def test_groups_by_path(self):
        records = [
            _make_record(url="http://host.com/api/v1"),
            _make_record(url="http://host.com/api/v2"),
            _make_record(url="http://host.com/api/v1"),
        ]
        result = pivot(records, "path")
        assert len(result.table["/api/v1"]) == 2
        assert len(result.table["/api/v2"]) == 1


class TestPivotInvalidDimension:
    def test_returns_error(self):
        result = pivot([_make_record()], "banana")
        assert result.has_error
        assert "banana" in result.error

    def test_summary_mentions_valid_choices(self):
        result = pivot([], "nope")
        s = result.summary()
        for d in VALID_DIMENSIONS:
            assert d in s


class TestPivotSummary:
    def test_lists_groups(self):
        records = [_make_record(method="GET"), _make_record(method="POST")]
        result = pivot(records, "method")
        s = pivot_summary(result)
        assert "GET" in s
        assert "POST" in s

    def test_error_returns_error_message(self):
        result = pivot([], "bad")
        s = pivot_summary(result)
        assert "error" in s.lower()
