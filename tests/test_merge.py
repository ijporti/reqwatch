"""Tests for reqwatch.merge."""

import pytest
from reqwatch.core import RequestRecord, RequestStore
from reqwatch.merge import MergeResult, merge_stores, merge_summary


def _make_record(method="GET", url="http://example.com/", status=200, body="hello"):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=body,
        timestamp="2024-01-01T00:00:00",
    )


def _make_store(*records):
    store = RequestStore()
    for r in records:
        store.add(r)
    return store


class TestMergeResult:
    def test_succeeded_when_no_error(self):
        r = MergeResult(records=[], total_before=0, total_after=0, duplicates_removed=0)
        assert r.succeeded() is True

    def test_not_succeeded_when_error(self):
        r = MergeResult(records=[], total_before=0, total_after=0, duplicates_removed=0, error="oops")
        assert r.succeeded() is False

    def test_summary_success(self):
        r = MergeResult(records=[], total_before=4, total_after=3, duplicates_removed=1)
        s = r.summary()
        assert "4" in s
        assert "3" in s
        assert "1" in s

    def test_summary_error(self):
        r = MergeResult(records=[], total_before=0, total_after=0, duplicates_removed=0, error="bad")
        assert "failed" in r.summary().lower()
        assert "bad" in r.summary()


class TestMergeStores:
    def test_combines_records(self):
        a = _make_store(_make_record(url="http://a.com/"))
        b = _make_store(_make_record(url="http://b.com/"))
        result = merge_stores(a, b)
        assert result.total_after == 2
        assert result.succeeded()

    def test_empty_stores(self):
        result = merge_stores(_make_store(), _make_store())
        assert result.total_after == 0
        assert result.duplicates_removed == 0

    def test_no_dedupe_keeps_duplicates(self):
        rec = _make_record()
        a = _make_store(rec)
        b = _make_store(rec)
        result = merge_stores(a, b, dedupe=False)
        assert result.total_after == 2
        assert result.duplicates_removed == 0

    def test_dedupe_removes_duplicates(self):
        rec = _make_record()
        a = _make_store(rec)
        b = _make_store(rec)
        result = merge_stores(a, b, dedupe=True)
        assert result.duplicates_removed >= 1
        assert result.total_after < result.total_before

    def test_base_records_appear_first(self):
        r1 = _make_record(url="http://first.com/")
        r2 = _make_record(url="http://second.com/")
        result = merge_stores(_make_store(r1), _make_store(r2))
        assert result.records[0].url == "http://first.com/"
        assert result.records[1].url == "http://second.com/"


def test_merge_summary_delegates_to_result():
    r = MergeResult(records=[], total_before=2, total_after=2, duplicates_removed=0)
    assert merge_summary(r) == r.summary()
