"""Tests for reqwatch.transform module."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.transform import (
    transform_url,
    transform_request_headers,
    transform_response_headers,
    transform_body,
    apply_transforms,
    replace_host,
    set_request_header,
    remove_request_header,
    transform_summary,
)


def _make_record(**kwargs) -> RequestRecord:
    defaults = dict(
        method="GET",
        url="http://old.example.com/api/v1",
        status=200,
        request_headers={"Authorization": "Bearer token"},
        response_headers={"Content-Type": "application/json"},
        body="hello",
        response_body='{"ok": true}',
        timestamp="2024-01-01T00:00:00",
        metadata={},
    )
    defaults.update(kwargs)
    return RequestRecord.from_dict(defaults)


class TestTransformUrl:
    def test_url_is_changed(self):
        r = _make_record(url="http://old.host/path")
        result = transform_url(r, lambda u: u.replace("old.host", "new.host"))
        assert result.to_dict()["url"] == "http://new.host/path"

    def test_original_is_not_mutated(self):
        r = _make_record(url="http://original/path")
        transform_url(r, lambda u: "http://changed/path")
        assert r.to_dict()["url"] == "http://original/path"


class TestTransformRequestHeaders:
    def test_header_added(self):
        r = _make_record(request_headers={"X-Old": "val"})
        result = transform_request_headers(r, lambda h: {**h, "X-New": "new"})
        assert result.to_dict()["request_headers"]["X-New"] == "new"

    def test_original_header_preserved(self):
        r = _make_record(request_headers={"X-Old": "val"})
        result = transform_request_headers(r, lambda h: {**h, "X-New": "new"})
        assert result.to_dict()["request_headers"]["X-Old"] == "val"


class TestTransformResponseHeaders:
    def test_header_removed(self):
        r = _make_record(response_headers={"X-Remove": "yes", "Keep": "me"})
        result = transform_response_headers(r, lambda h: {k: v for k, v in h.items() if k != "X-Remove"})
        assert "X-Remove" not in result.to_dict()["response_headers"]
        assert result.to_dict()["response_headers"]["Keep"] == "me"


class TestTransformBody:
    def test_body_uppercased(self):
        r = _make_record(body="hello world")
        result = transform_body(r, lambda b: b.upper() if b else b)
        assert result.to_dict()["body"] == "HELLO WORLD"

    def test_none_body_handled(self):
        r = _make_record(body=None)
        result = transform_body(r, lambda b: b)
        assert result.to_dict()["body"] is None


class TestApplyTransforms:
    def test_multiple_transforms_applied_in_order(self):
        records = [_make_record(url="http://old.host/path")]
        t1 = lambda rec: replace_host(rec, "old.host", "mid.host")
        t2 = lambda rec: replace_host(rec, "mid.host", "new.host")
        result = apply_transforms(records, [t1, t2])
        assert result[0].to_dict()["url"] == "http://new.host/path"

    def test_empty_transforms_returns_same_values(self):
        records = [_make_record()]
        result = apply_transforms(records, [])
        assert result[0].to_dict() == records[0].to_dict()


class TestHelpers:
    def test_replace_host(self):
        r = _make_record(url="http://old.example.com/api")
        result = replace_host(r, "old.example.com", "new.example.com")
        assert "new.example.com" in result.to_dict()["url"]

    def test_set_request_header(self):
        r = _make_record(request_headers={})
        result = set_request_header(r, "X-Custom", "value123")
        assert result.to_dict()["request_headers"]["X-Custom"] == "value123"

    def test_remove_request_header(self):
        r = _make_record(request_headers={"X-Remove": "bye", "Keep": "yes"})
        result = remove_request_header(r, "X-Remove")
        assert "X-Remove" not in result.to_dict()["request_headers"]

    def test_remove_nonexistent_header_is_safe(self):
        r = _make_record(request_headers={"Keep": "yes"})
        result = remove_request_header(r, "Ghost")
        assert result.to_dict()["request_headers"] == {"Keep": "yes"}


class TestTransformSummary:
    def test_reports_changed_count(self):
        original = [_make_record(url="http://old/"), _make_record(url="http://same/")]
        transformed = [
            replace_host(original[0], "old", "new"),
            original[1],
        ]
        msg = transform_summary(original, transformed)
        assert "1/2" in msg

    def test_no_changes(self):
        records = [_make_record()]
        msg = transform_summary(records, records[:])
        assert "0/1" in msg
