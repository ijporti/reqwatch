"""Tests for reqwatch.cluster."""
from __future__ import annotations

import pytest

from reqwatch.cluster import (
    ClusterResult,
    _url_template,
    cluster,
    cluster_summary,
)
from reqwatch.core import RequestRecord


def _make_record(method: str = "GET", url: str = "http://example.com/", status: int = 200) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
    )


# ---------------------------------------------------------------------------
# _url_template
# ---------------------------------------------------------------------------

class TestUrlTemplate:
    def test_leaves_plain_path_unchanged(self):
        assert _url_template("http://api.example.com/users") == "http://api.example.com/users"

    def test_replaces_numeric_segment(self):
        result = _url_template("http://api.example.com/users/42/posts")
        assert result == "http://api.example.com/users/{id}/posts"

    def test_replaces_uuid_segment(self):
        result = _url_template("http://api.example.com/items/deadbeef1234abcd")
        assert result == "http://api.example.com/items/{id}"

    def test_replaces_multiple_id_segments(self):
        result = _url_template("http://api.example.com/a/1/b/2")
        assert "{id}" in result
        assert "1" not in result
        assert "2" not in result


# ---------------------------------------------------------------------------
# ClusterResult
# ---------------------------------------------------------------------------

class TestClusterResult:
    def test_has_error_false_when_no_error(self):
        r = ClusterResult(key="GET /users")
        assert r.has_error is False

    def test_has_error_true_when_error_set(self):
        r = ClusterResult(key="k", error="bad")
        assert r.has_error is True

    def test_size_reflects_records(self):
        r = ClusterResult(key="k", records=[_make_record(), _make_record()])
        assert r.size == 2

    def test_summary_no_error(self):
        r = ClusterResult(key="GET /users", records=[_make_record()])
        assert "GET /users" in r.summary()
        assert "1" in r.summary()

    def test_summary_with_error(self):
        r = ClusterResult(key="k", error="oops")
        assert "oops" in r.summary()


# ---------------------------------------------------------------------------
# cluster
# ---------------------------------------------------------------------------

class TestCluster:
    def test_empty_returns_empty_dict(self):
        assert cluster([]) == {}

    def test_groups_by_method_and_template(self):
        records = [
            _make_record("GET", "http://api.example.com/users/1"),
            _make_record("GET", "http://api.example.com/users/2"),
            _make_record("POST", "http://api.example.com/users"),
        ]
        result = cluster(records, by="method+template")
        assert len(result) == 2
        assert any("GET" in k for k in result)
        assert any("POST" in k for k in result)

    def test_groups_by_template_only(self):
        records = [
            _make_record("GET", "http://api.example.com/users/1"),
            _make_record("DELETE", "http://api.example.com/users/2"),
        ]
        result = cluster(records, by="template")
        assert len(result) == 1

    def test_groups_by_method_only(self):
        records = [
            _make_record("GET", "http://a.com/x"),
            _make_record("GET", "http://b.com/y"),
            _make_record("POST", "http://c.com/z"),
        ]
        result = cluster(records, by="method")
        assert set(result.keys()) == {"GET", "POST"}

    def test_unknown_strategy_returns_error(self):
        result = cluster([_make_record()], by="unknown")
        assert "__error__" in result
        assert result["__error__"].has_error


# ---------------------------------------------------------------------------
# cluster_summary
# ---------------------------------------------------------------------------

def test_summary_empty():
    assert cluster_summary({}) == "No clusters."


def test_summary_shows_count():
    records = [_make_record("GET", "http://example.com/a") for _ in range(3)]
    clusters = cluster(records)
    summary = cluster_summary(clusters)
    assert "1 cluster" in summary
    assert "3" in summary
