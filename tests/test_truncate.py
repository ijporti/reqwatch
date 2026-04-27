"""Tests for reqwatch.truncate."""

import pytest

from reqwatch.truncate import (
    DEFAULT_MAX_BYTES,
    is_truncated,
    truncate_body,
    truncate_headers,
    truncation_summary,
)


# ---------------------------------------------------------------------------
# truncate_body
# ---------------------------------------------------------------------------

class TestTruncateBody:
    def test_none_returns_empty_string(self):
        assert truncate_body(None) == ""

    def test_empty_string_returns_empty_string(self):
        assert truncate_body("") == ""

    def test_short_body_returned_unchanged(self):
        body = "hello world"
        assert truncate_body(body) == body

    def test_exactly_max_bytes_not_truncated(self):
        body = "x" * DEFAULT_MAX_BYTES
        result = truncate_body(body)
        assert result == body
        assert "truncated" not in result

    def test_over_limit_is_truncated(self):
        body = "a" * (DEFAULT_MAX_BYTES + 50)
        result = truncate_body(body)
        assert result.startswith("a" * DEFAULT_MAX_BYTES)
        assert "truncated" in result

    def test_truncated_notice_contains_omitted_count(self):
        body = "b" * (DEFAULT_MAX_BYTES + 100)
        result = truncate_body(body)
        assert "100 chars truncated" in result

    def test_custom_max_bytes(self):
        body = "c" * 20
        result = truncate_body(body, max_bytes=10)
        assert result.startswith("c" * 10)
        assert "10 chars truncated" in result


# ---------------------------------------------------------------------------
# is_truncated
# ---------------------------------------------------------------------------

class TestIsTruncated:
    def test_none_returns_false(self):
        assert is_truncated(None) is False

    def test_empty_returns_false(self):
        assert is_truncated("") is False

    def test_short_body_returns_false(self):
        assert is_truncated("hi") is False

    def test_over_limit_returns_true(self):
        assert is_truncated("x" * (DEFAULT_MAX_BYTES + 1)) is True

    def test_custom_limit(self):
        assert is_truncated("abcde", max_bytes=4) is True
        assert is_truncated("abcd", max_bytes=4) is False


# ---------------------------------------------------------------------------
# truncate_headers
# ---------------------------------------------------------------------------

class TestTruncateHeaders:
    def test_short_values_unchanged(self):
        headers = {"Content-Type": "application/json", "X-Id": "123"}
        assert truncate_headers(headers) == headers

    def test_long_value_truncated(self):
        long_val = "v" * 200
        result = truncate_headers({"Authorization": long_val}, max_value_length=50)
        assert "truncated" in result["Authorization"]
        assert result["Authorization"].startswith("v" * 50)

    def test_original_dict_not_mutated(self):
        headers = {"X-Long": "z" * 200}
        truncate_headers(headers)
        assert len(headers["X-Long"]) == 200


# ---------------------------------------------------------------------------
# truncation_summary
# ---------------------------------------------------------------------------

class TestTruncationSummary:
    def test_none_body(self):
        assert truncation_summary(None) == "body: empty"

    def test_empty_body(self):
        assert truncation_summary("") == "body: empty"

    def test_short_body_not_truncated(self):
        summary = truncation_summary("hello")
        assert "not truncated" in summary
        assert "5 chars" in summary

    def test_long_body_truncated(self):
        body = "x" * (DEFAULT_MAX_BYTES + 1)
        summary = truncation_summary(body)
        assert "truncated" in summary
        assert str(DEFAULT_MAX_BYTES + 1) in summary
