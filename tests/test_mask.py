"""Tests for reqwatch.mask."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.mask import (
    mask_body,
    mask_headers,
    mask_record,
    mask_summary,
)


def _make_record(**kwargs) -> RequestRecord:
    defaults = dict(
        id="rec-1",
        timestamp="2024-01-01T00:00:00",
        method="GET",
        url="https://example.com/api",
        request_headers={"Authorization": "Bearer secret", "Accept": "application/json"},
        request_body=None,
        status_code=200,
        response_headers={"Set-Cookie": "session=abc", "Content-Type": "application/json"},
        response_body='{"token": "my-secret-token"}',
        duration_ms=42.0,
        metadata={},
    )
    defaults.update(kwargs)
    return RequestRecord(**defaults)


class TestMaskHeaders:
    def test_masks_authorization_by_default(self):
        result = mask_headers({"Authorization": "Bearer xyz", "Accept": "*/*"})
        assert result["Authorization"] == "***"
        assert result["Accept"] == "*/*"

    def test_masks_cookie_by_default(self):
        result = mask_headers({"Cookie": "session=abc"})
        assert result["Cookie"] == "***"

    def test_case_insensitive_matching(self):
        result = mask_headers({"authorization": "secret"})
        assert result["authorization"] == "***"

    def test_custom_key_masked(self):
        result = mask_headers({"X-Custom": "value"}, keys=["X-Custom"])
        assert result["X-Custom"] == "***"

    def test_custom_mask_string(self):
        result = mask_headers({"Authorization": "Bearer xyz"}, mask="[REDACTED]")
        assert result["Authorization"] == "[REDACTED]"

    def test_empty_headers_returns_empty(self):
        assert mask_headers({}) == {}


class TestMaskBody:
    def test_replaces_pattern_in_body(self):
        result = mask_body('{"password": "secret123"}', patterns=[r'"secret\w+"'])
        assert "secret123" not in result
        assert "***" in result

    def test_none_body_returns_empty_string(self):
        assert mask_body(None, patterns=[r"\d+"]) == ""

    def test_empty_body_returns_empty_string(self):
        assert mask_body("", patterns=[r"\d+"]) == ""

    def test_no_patterns_returns_original(self):
        body = '{"key": "value"}'
        assert mask_body(body, patterns=[]) == body

    def test_multiple_patterns_applied(self):
        body = "email: user@example.com token: abc123"
        result = mask_body(body, patterns=[r"\S+@\S+", r"abc\d+"])
        assert "user@example.com" not in result
        assert "abc123" not in result


class TestMaskRecord:
    def test_returns_new_record(self):
        rec = _make_record()
        masked = mask_record(rec)
        assert masked is not rec

    def test_original_not_mutated(self):
        rec = _make_record()
        original_header = rec.request_headers["Authorization"]
        mask_record(rec)
        assert rec.request_headers["Authorization"] == original_header

    def test_default_sensitive_headers_masked(self):
        rec = _make_record()
        masked = mask_record(rec)
        assert masked.request_headers["Authorization"] == "***"
        assert masked.response_headers["Set-Cookie"] == "***"

    def test_body_pattern_applied(self):
        rec = _make_record()
        masked = mask_record(rec, body_patterns=[r'"my-secret-token"'])
        assert "my-secret-token" not in masked.response_body

    def test_non_sensitive_fields_preserved(self):
        rec = _make_record()
        masked = mask_record(rec)
        assert masked.method == rec.method
        assert masked.url == rec.url
        assert masked.status_code == rec.status_code
        assert masked.duration_ms == rec.duration_ms


class TestMaskSummary:
    def test_nothing_masked_when_no_sensitive_headers(self):
        rec = _make_record(
            request_headers={"Accept": "*/*"},
            response_headers={"Content-Type": "application/json"},
        )
        masked = mask_record(rec)
        assert mask_summary(rec, masked) == "nothing masked"

    def test_reports_masked_headers(self):
        rec = _make_record()
        masked = mask_record(rec)
        summary = mask_summary(rec, masked)
        assert "request header" in summary or "response header" in summary

    def test_reports_body_change(self):
        rec = _make_record()
        masked = mask_record(rec, body_patterns=[r'"my-secret-token"'])
        assert "body" in mask_summary(rec, masked)
