"""Tests for reqwatch.diff module."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.diff import diff_records, DiffResult


def _make_record(
    status=200,
    body="hello",
    headers=None,
    url="http://example.com/api",
    method="GET",
) -> RequestRecord:
    return RequestRecord(
        id="abc123",
        method=method,
        url=url,
        request_headers={"content-type": "application/json"},
        request_body=None,
        response_status=status,
        response_headers=headers or {"content-type": "application/json"},
        response_body=body,
        timestamp="2024-01-01T00:00:00",
        duration_ms=42.0,
    )


class TestDiffRecordsNoChanges:
    def test_has_diff_false_when_identical(self):
        r = _make_record()
        result = diff_records(r, r)
        assert result.has_diff is False

    def test_summary_no_diff(self):
        r = _make_record()
        result = diff_records(r, r)
        assert result.summary() == "No differences detected."


class TestDiffRecordsStatusChange:
    def test_status_changed_detected(self):
        orig = _make_record(status=200)
        rep = _make_record(status=500)
        result = diff_records(orig, rep)
        assert result.status_changed is True

    def test_status_diff_tuple(self):
        orig = _make_record(status=200)
        rep = _make_record(status=404)
        result = diff_records(orig, rep)
        assert result.status_diff == (200, 404)

    def test_status_diff_none_when_same(self):
        orig = _make_record(status=200)
        rep = _make_record(status=200)
        result = diff_records(orig, rep)
        assert result.status_diff is None

    def test_summary_includes_status(self):
        orig = _make_record(status=200)
        rep = _make_record(status=503)
        result = diff_records(orig, rep)
        assert "200" in result.summary()
        assert "503" in result.summary()


class TestDiffRecordsBodyChange:
    def test_body_changed_detected(self):
        orig = _make_record(body="hello")
        rep = _make_record(body="world")
        result = diff_records(orig, rep)
        assert result.body_changed is True

    def test_body_whitespace_normalized(self):
        orig = _make_record(body="hello")
        rep = _make_record(body="  hello  ")
        result = diff_records(orig, rep)
        assert result.body_changed is False

    def test_none_body_treated_as_empty(self):
        orig = _make_record(body=None)
        rep = _make_record(body="")
        result = diff_records(orig, rep)
        assert result.body_changed is False

    def test_summary_includes_body(self):
        orig = _make_record(body="a")
        rep = _make_record(body="b")
        result = diff_records(orig, rep)
        assert "Body" in result.summary()


class TestDiffRecordsHeaderChange:
    def test_missing_header_detected(self):
        orig = _make_record(headers={"x-trace": "1", "content-type": "json"})
        rep = _make_record(headers={"content-type": "json"})
        result = diff_records(orig, rep)
        assert "x-trace" in result.missing_headers

    def test_added_header_detected(self):
        orig = _make_record(headers={"content-type": "json"})
        rep = _make_record(headers={"content-type": "json", "x-new": "val"})
        result = diff_records(orig, rep)
        assert "x-new" in result.added_headers

    def test_no_header_diff_when_same(self):
        h = {"content-type": "application/json"}
        orig = _make_record(headers=h)
        rep = _make_record(headers=h)
        result = diff_records(orig, rep)
        assert result.headers_changed is False
        assert result.missing_headers == []
        assert result.added_headers == []
