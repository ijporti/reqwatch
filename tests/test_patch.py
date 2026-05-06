"""Tests for reqwatch.patch."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.patch import (
    PatchResult,
    patch_all,
    patch_record,
    patch_summary,
)


def _make_record(
    rid: str = "abc123",
    method: str = "GET",
    url: str = "http://example.com/api",
    status: int = 200,
) -> RequestRecord:
    return RequestRecord(
        id=rid,
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
        metadata={},
    )


class TestPatchResult:
    def test_succeeded_when_no_error(self):
        r = PatchResult(record_id="x", applied={"method": "POST"}, skipped={})
        assert r.succeeded() is True

    def test_not_succeeded_when_error(self):
        r = PatchResult(record_id="x", applied={}, skipped={}, error="boom")
        assert r.succeeded() is False

    def test_summary_shows_applied_fields(self):
        r = PatchResult(record_id="x", applied={"method": "POST"}, skipped={})
        assert "applied" in r.summary()
        assert "method" in r.summary()

    def test_summary_shows_skipped_fields(self):
        r = PatchResult(record_id="x", applied={}, skipped={"foo": 1})
        assert "skipped" in r.summary()
        assert "foo" in r.summary()

    def test_summary_shows_error(self):
        r = PatchResult(record_id="x", applied={}, skipped={}, error="bad")
        assert "failed" in r.summary()
        assert "bad" in r.summary()

    def test_summary_no_changes(self):
        r = PatchResult(record_id="x", applied={}, skipped={})
        assert "no changes" in r.summary()


def test_patch_record_changes_method():
    rec = _make_record(method="GET")
    result = patch_record(rec, {"method": "POST"})
    assert rec.method == "POST"
    assert result.succeeded()
    assert "method" in result.applied


def test_patch_record_changes_url():
    rec = _make_record(url="http://old.example.com")
    patch_record(rec, {"url": "http://new.example.com"})
    assert rec.url == "http://new.example.com"


def test_patch_record_skips_unknown_field():
    rec = _make_record()
    result = patch_record(rec, {"nonexistent_field": "value"})
    assert "nonexistent_field" in result.skipped
    assert "nonexistent_field" not in result.applied


def test_patch_record_mixed_known_and_unknown():
    rec = _make_record()
    result = patch_record(rec, {"method": "DELETE", "bogus": True})
    assert rec.method == "DELETE"
    assert "method" in result.applied
    assert "bogus" in result.skipped


def test_patch_record_updates_metadata():
    rec = _make_record()
    patch_record(rec, {"metadata": {"env": "staging"}})
    assert rec.metadata == {"env": "staging"}


def test_patch_all_applies_to_every_record():
    records = [_make_record(rid=str(i), method="GET") for i in range(4)]
    results = patch_all(records, {"method": "PATCH"})
    assert all(r.method == "PATCH" for r in records)
    assert len(results) == 4
    assert all(res.succeeded() for res in results)


def test_patch_summary_all_ok():
    results = [
        PatchResult(record_id=str(i), applied={"method": "X"}, skipped={})
        for i in range(3)
    ]
    msg = patch_summary(results)
    assert "3/3" in msg
    assert "failed" not in msg


def test_patch_summary_with_failures():
    results = [
        PatchResult(record_id="1", applied={}, skipped={}, error="oops"),
        PatchResult(record_id="2", applied={"url": "x"}, skipped={}),
    ]
    msg = patch_summary(results)
    assert "1/2" in msg
    assert "failed" in msg
