"""Tests for reqwatch.route."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.route import (
    match_route,
    group_by_route,
    route_records,
    RouteResult,
)


def _make_record(method: str = "GET", url: str = "http://example.com/") -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
    )


class TestMatchRoute:
    def test_exact_match(self):
        r = _make_record(url="http://api.local/users")
        assert match_route(r, "/users") is True

    def test_no_match(self):
        r = _make_record(url="http://api.local/orders")
        assert match_route(r, "/users") is False

    def test_param_match_curly(self):
        r = _make_record(url="http://api.local/users/42")
        assert match_route(r, "/users/{id}") is True

    def test_param_match_colon(self):
        r = _make_record(url="http://api.local/users/99")
        assert match_route(r, "/users/:id") is True

    def test_query_string_ignored(self):
        r = _make_record(url="http://api.local/users/5?foo=bar")
        assert match_route(r, "/users/{id}") is True

    def test_trailing_slash_normalised(self):
        r = _make_record(url="http://api.local/users/")
        assert match_route(r, "/users") is True


class TestGroupByRoute:
    def test_groups_into_correct_bucket(self):
        r1 = _make_record(url="http://x.com/users/1")
        r2 = _make_record(url="http://x.com/orders/9")
        result = group_by_route([r1, r2], ["/users/{id}", "/orders/{id}"])
        assert r1 in result["/users/{id}"]
        assert r2 in result["/orders/{id}"]

    def test_unmatched_bucket(self):
        r = _make_record(url="http://x.com/unknown/path")
        result = group_by_route([r], ["/users/{id}"])
        assert r in result["<unmatched>"]

    def test_first_match_wins(self):
        r = _make_record(url="http://x.com/users/7")
        result = group_by_route([r], ["/users/{id}", "/users/:uid"])
        assert r in result["/users/{id}"]
        assert r not in result["/users/:uid"]

    def test_empty_records_returns_empty_buckets(self):
        result = group_by_route([], ["/a", "/b"])
        assert result["/a"] == []
        assert result["/b"] == []


class TestRouteResult:
    def test_has_error_false_when_no_error(self):
        rr = RouteResult(groups={})
        assert rr.has_error is False

    def test_has_error_true_when_error_set(self):
        rr = RouteResult(error="boom")
        assert rr.has_error is True

    def test_summary_no_error(self):
        r = _make_record(url="http://x.com/users/1")
        groups = {"/users/{id}": [r], "<unmatched>": []}
        rr = RouteResult(groups=groups)
        s = rr.summary()
        assert "/users/{id}" in s
        assert "1 record" in s

    def test_summary_error(self):
        rr = RouteResult(error="bad template")
        assert "bad template" in rr.summary()


def test_route_records_returns_route_result():
    r = _make_record(url="http://x.com/items/3")
    result = route_records([r], ["/items/{id}"])
    assert isinstance(result, RouteResult)
    assert not result.has_error
    assert r in result.groups["/items/{id}"]
