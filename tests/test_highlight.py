"""Tests for reqwatch.highlight."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.highlight import (
    HighlightResult,
    highlight_all,
    highlight_record,
    _apply_colour,
    ANSI_YELLOW,
    ANSI_RESET,
)


def _make_record(
    request_id: str = "r1",
    url: str = "http://example.com/api/users",
    method: str = "GET",
    request_body: str = "",
    response_body: str = "",
    status_code: int = 200,
) -> RequestRecord:
    return RequestRecord(
        request_id=request_id,
        url=url,
        method=method,
        request_headers={},
        request_body=request_body,
        response_status=status_code,
        response_headers={},
        response_body=response_body,
        timestamp="2024-01-01T00:00:00",
    )


class TestHighlightResult:
    def test_has_match_false_when_no_fields(self):
        r = HighlightResult(record_id="x", url="http://example.com")
        assert r.has_match is False

    def test_has_match_true_when_fields_populated(self):
        r = HighlightResult(record_id="x", url="http://example.com", matched_fields=["url"])
        assert r.has_match is True

    def test_summary_no_match(self):
        r = HighlightResult(record_id="abc", url="http://example.com")
        assert "no matches" in r.summary()

    def test_summary_with_match(self):
        r = HighlightResult(record_id="abc", url="http://example.com", matched_fields=["url"])
        assert "url" in r.summary()
        assert "abc" in r.summary()


class TestApplyColour:
    def test_wraps_match_with_ansi(self):
        result = _apply_colour("hello world", "world", "yellow")
        assert ANSI_YELLOW in result
        assert ANSI_RESET in result

    def test_unknown_colour_falls_back_to_yellow(self):
        result = _apply_colour("hello world", "world", "purple")
        assert ANSI_YELLOW in result

    def test_case_insensitive_match(self):
        result = _apply_colour("Hello World", "hello", "yellow")
        assert ANSI_YELLOW in result


def test_highlight_record_url_match():
    rec = _make_record(url="http://example.com/api/users")
    result = highlight_record(rec, "users")
    assert "url" in result.matched_fields
    assert result.highlighted_url is not None
    assert ANSI_YELLOW in result.highlighted_url


def test_highlight_record_no_match():
    rec = _make_record(url="http://example.com/health")
    result = highlight_record(rec, "users")
    assert not result.has_match


def test_highlight_record_body_match():
    rec = _make_record(response_body='{"token": "abc123"}')
    result = highlight_record(rec, "token", fields=["response_body"])
    assert "response_body" in result.matched_fields
    assert result.highlighted_body is not None


def test_highlight_record_respects_fields_filter():
    rec = _make_record(url="http://example.com/users", response_body="users list")
    result = highlight_record(rec, "users", fields=["response_body"])
    assert "url" not in result.matched_fields
    assert "response_body" in result.matched_fields


def test_highlight_all_filters_non_matching():
    records = [
        _make_record(request_id="r1", url="http://example.com/users"),
        _make_record(request_id="r2", url="http://example.com/health"),
        _make_record(request_id="r3", url="http://example.com/users/42"),
    ]
    results = highlight_all(records, "users")
    assert len(results) == 2
    ids = {r.record_id for r in results}
    assert ids == {"r1", "r3"}


def test_highlight_all_empty_list():
    assert highlight_all([], "anything") == []
