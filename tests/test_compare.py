"""Tests for reqwatch.compare module."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.compare import (
    CompareResult,
    compare_stores,
    _record_key,
    _records_differ,
)


def _make_record(
    method="GET",
    url="http://example.com/api",
    status_code=200,
    request_body="",
    response_body="ok",
):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=request_body,
        response_status=status_code,
        response_headers={},
        response_body=response_body,
        timestamp="2024-01-01T00:00:00",
        duration_ms=10.0,
    )


class TestRecordKey:
    def test_key_includes_method_and_url(self):
        r = _make_record(method="get", url="http://example.com/path")
        assert _record_key(r) == "GET:http://example.com/path"

    def test_method_uppercased(self):
        r = _make_record(method="post")
        assert _record_key(r).startswith("POST:")


class TestRecordsDiffer:
    def test_identical_records_do_not_differ(self):
        a = _make_record()
        b = _make_record()
        assert not _records_differ(a, b)

    def test_different_status_codes_differ(self):
        a = _make_record(status_code=200)
        b = _make_record(status_code=404)
        assert _records_differ(a, b)

    def test_different_response_body_differs(self):
        a = _make_record(response_body="hello")
        b = _make_record(response_body="world")
        assert _records_differ(a, b)

    def test_different_request_body_differs(self):
        a = _make_record(request_body="{\"x\": 1}")
        b = _make_record(request_body="{\"x\": 2}")
        assert _records_differ(a, b)


class TestCompareStores:
    def test_empty_stores_no_changes(self):
        result = compare_stores([], [])
        assert not result.has_changes
        assert result.added == []
        assert result.removed == []
        assert result.changed == []

    def test_added_record_detected(self):
        new_rec = _make_record(url="http://example.com/new")
        result = compare_stores([], [new_rec])
        assert len(result.added) == 1
        assert result.added[0].url == "http://example.com/new"

    def test_removed_record_detected(self):
        old_rec = _make_record(url="http://example.com/old")
        result = compare_stores([old_rec], [])
        assert len(result.removed) == 1
        assert result.removed[0].url == "http://example.com/old"

    def test_changed_record_detected(self):
        base = _make_record(status_code=200)
        curr = _make_record(status_code=500)
        result = compare_stores([base], [curr])
        assert len(result.changed) == 1
        assert result.changed[0][0].response_status == 200
        assert result.changed[0][1].response_status == 500

    def test_unchanged_record_not_in_changed(self):
        rec = _make_record()
        result = compare_stores([rec], [rec])
        assert result.unchanged
        assert not result.changed

    def test_has_changes_false_when_only_unchanged(self):
        rec = _make_record()
        result = compare_stores([rec], [rec])
        assert not result.has_changes

    def test_summary_format(self):
        result = CompareResult()
        summary = result.summary()
        assert "Added" in summary
        assert "Removed" in summary
        assert "Changed" in summary
        assert "Unchanged" in summary
