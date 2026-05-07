"""Tests for reqwatch.split."""
from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.split import SplitResult, split_by, split_summary


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api",
    response_status: int = 200,
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=response_status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
    )


class TestSplitResult:
    def test_succeeded_when_no_error(self):
        r = SplitResult(buckets={"GET": []})
        assert r.succeeded is True

    def test_not_succeeded_when_error(self):
        r = SplitResult(error="oops")
        assert r.succeeded is False

    def test_summary_shows_bucket_counts(self):
        records = [_make_record()]
        r = SplitResult(buckets={"GET": records})
        s = r.summary()
        assert "GET=1" in s

    def test_summary_error(self):
        r = SplitResult(error="bad criterion")
        assert "failed" in r.summary().lower()


class TestSplitByMethod:
    def test_groups_by_method(self):
        records = [
            _make_record(method="GET"),
            _make_record(method="POST"),
            _make_record(method="GET"),
        ]
        result = split_by(records, "method")
        assert result.succeeded
        assert len(result.buckets["GET"]) == 2
        assert len(result.buckets["POST"]) == 1

    def test_method_normalised_to_upper(self):
        records = [_make_record(method="get")]
        result = split_by(records, "method")
        assert "GET" in result.buckets

    def test_empty_records_returns_empty_buckets(self):
        result = split_by([], "method")
        assert result.buckets == {}


class TestSplitByStatus:
    def test_groups_by_status_code(self):
        records = [
            _make_record(response_status=200),
            _make_record(response_status=404),
            _make_record(response_status=200),
        ]
        result = split_by(records, "status")
        assert len(result.buckets["200"]) == 2
        assert len(result.buckets["404"]) == 1


class TestSplitByHost:
    def test_groups_by_hostname(self):
        records = [
            _make_record(url="http://alpha.com/a"),
            _make_record(url="http://beta.com/b"),
            _make_record(url="http://alpha.com/c"),
        ]
        result = split_by(records, "host")
        assert len(result.buckets["alpha.com"]) == 2
        assert len(result.buckets["beta.com"]) == 1


class TestSplitUnknownCriterion:
    def test_returns_error_for_unknown_criterion(self):
        result = split_by([_make_record()], "foobar")
        assert not result.succeeded
        assert "foobar" in result.error  # type: ignore[operator]


def test_split_summary_delegates_to_result():
    result = split_by([_make_record()], "method")
    assert split_summary(result) == result.summary()
