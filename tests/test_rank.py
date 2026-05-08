"""Tests for reqwatch.rank."""
from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.rank import RankResult, rank_records, rank_summary


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/",
    status_code: int = 200,
    response_body: str = "",
    response_time: float = 0.0,
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        status_code=status_code,
        response_headers={},
        response_body=response_body,
        timestamp="2024-01-01T00:00:00",
        metadata={"response_time": response_time},
    )


class TestRankResult:
    def test_succeeded_when_no_error(self):
        r = RankResult(records=[], criterion="status", ascending=True)
        assert r.succeeded() is True

    def test_not_succeeded_when_error(self):
        r = RankResult(records=[], criterion="status", ascending=True, error="oops")
        assert r.succeeded() is False

    def test_summary_success(self):
        r = RankResult(records=[_make_record()], criterion="status", ascending=False)
        s = r.summary()
        assert "1" in s
        assert "status" in s
        assert "desc" in s

    def test_summary_error(self):
        r = RankResult(records=[], criterion="x", ascending=True, error="bad")
        assert "error" in r.summary()


def test_rank_by_status_descending():
    records = [
        _make_record(status_code=200),
        _make_record(status_code=500),
        _make_record(status_code=404),
    ]
    result = rank_records(records, criterion="status", ascending=False)
    assert result.succeeded()
    codes = [r.status_code for r in result.records]
    assert codes == [500, 404, 200]


def test_rank_by_status_ascending():
    records = [
        _make_record(status_code=500),
        _make_record(status_code=200),
        _make_record(status_code=301),
    ]
    result = rank_records(records, criterion="status", ascending=True)
    codes = [r.status_code for r in result.records]
    assert codes == [200, 301, 500]


def test_rank_by_response_time():
    records = [
        _make_record(response_time=0.5),
        _make_record(response_time=2.0),
        _make_record(response_time=0.1),
    ]
    result = rank_records(records, criterion="response_time", ascending=False)
    times = [r.metadata["response_time"] for r in result.records]
    assert times == [2.0, 0.5, 0.1]


def test_rank_by_body_size():
    records = [
        _make_record(response_body="hi"),
        _make_record(response_body="hello world"),
        _make_record(response_body=""),
    ]
    result = rank_records(records, criterion="body_size", ascending=False)
    sizes = [len(r.response_body or "") for r in result.records]
    assert sizes[0] >= sizes[1] >= sizes[2]


def test_top_n_limits_results():
    records = [_make_record(status_code=c) for c in [200, 404, 500, 201]]
    result = rank_records(records, criterion="status", ascending=False, top_n=2)
    assert len(result.records) == 2


def test_unknown_criterion_returns_error():
    result = rank_records([], criterion="magic")
    assert not result.succeeded()
    assert "magic" in result.summary()


def test_empty_list_returns_empty():
    result = rank_records([], criterion="status")
    assert result.succeeded()
    assert result.records == []


def test_rank_summary_delegates():
    result = rank_records([_make_record()], criterion="body_size")
    assert rank_summary(result) == result.summary()
