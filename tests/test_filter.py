"""Tests for reqwatch.filter module."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.filter import (
    apply_filters,
    filter_by_method,
    filter_by_status,
    filter_by_status_range,
    filter_by_url_pattern,
)


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api/v1/users",
    status_code: int = 200,
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        status_code=status_code,
        response_headers={},
        response_body=b"",
        elapsed_ms=42.0,
    )


RECORDS = [
    _make_record("GET", "http://example.com/api/v1/users", 200),
    _make_record("POST", "http://example.com/api/v1/users", 201),
    _make_record("DELETE", "http://example.com/api/v1/users/1", 204),
    _make_record("GET", "http://example.com/api/v1/orders", 404),
    _make_record("GET", "http://example.com/health", 500),
]


class TestFilterByMethod:
    def test_returns_matching_method(self):
        result = filter_by_method(RECORDS, "GET")
        assert all(r.method == "GET" for r in result)
        assert len(result) == 3

    def test_case_insensitive(self):
        assert filter_by_method(RECORDS, "post") == filter_by_method(RECORDS, "POST")

    def test_no_match_returns_empty(self):
        assert filter_by_method(RECORDS, "PATCH") == []


class TestFilterByStatus:
    def test_exact_match(self):
        result = filter_by_status(RECORDS, 200)
        assert len(result) == 1
        assert result[0].status_code == 200

    def test_no_match(self):
        assert filter_by_status(RECORDS, 302) == []


class TestFilterByUrlPattern:
    def test_simple_substring(self):
        result = filter_by_url_pattern(RECORDS, "users")
        assert len(result) == 3

    def test_regex_pattern(self):
        result = filter_by_url_pattern(RECORDS, r"/v1/(users|orders)")
        assert len(result) == 4

    def test_no_match(self):
        assert filter_by_url_pattern(RECORDS, "nonexistent") == []


class TestFilterByStatusRange:
    def test_2xx_range(self):
        result = filter_by_status_range(RECORDS, 200, 299)
        assert all(200 <= r.status_code <= 299 for r in result)
        assert len(result) == 3

    def test_5xx_range(self):
        result = filter_by_status_range(RECORDS, 500, 599)
        assert len(result) == 1


class TestApplyFilters:
    def test_no_filters_returns_all(self):
        assert apply_filters(RECORDS) == list(RECORDS)

    def test_combined_method_and_status(self):
        result = apply_filters(RECORDS, method="GET", status=200)
        assert len(result) == 1

    def test_url_pattern_and_status_range(self):
        result = apply_filters(RECORDS, url_pattern="users", min_status=200, max_status=299)
        assert all(200 <= r.status_code <= 299 for r in result)
        assert all("users" in r.url for r in result)
