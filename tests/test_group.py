"""Tests for reqwatch.group module."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.group import (
    group_by_method,
    group_by_status,
    group_by_host,
    group_by,
    group_summary,
)


def _make_record(method="GET", url="http://example.com/api", status_code=200):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_headers={},
        response_body=None,
        status_code=status_code,
        elapsed_ms=50.0,
        timestamp="2024-01-01T00:00:00",
    )


class TestGroupByMethod:
    def test_groups_correctly(self):
        records = [_make_record("GET"), _make_record("POST"), _make_record("GET")]
        result = group_by_method(records)
        assert len(result["GET"]) == 2
        assert len(result["POST"]) == 1

    def test_case_normalised_to_upper(self):
        records = [_make_record("get"), _make_record("Get")]
        result = group_by_method(records)
        assert "GET" in result
        assert len(result["GET"]) == 2

    def test_empty_returns_empty_dict(self):
        assert group_by_method([]) == {}


class TestGroupByStatus:
    def test_groups_by_status_code(self):
        records = [_make_record(status_code=200), _make_record(status_code=404),
                   _make_record(status_code=200)]
        result = group_by_status(records)
        assert len(result[200]) == 2
        assert len(result[404]) == 1

    def test_single_status(self):
        records = [_make_record(status_code=500)]
        result = group_by_status(records)
        assert 500 in result


class TestGroupByHost:
    def test_groups_by_host(self):
        records = [
            _make_record(url="http://api.example.com/v1"),
            _make_record(url="http://other.com/data"),
            _make_record(url="http://api.example.com/v2"),
        ]
        result = group_by_host(records)
        assert len(result["api.example.com"]) == 2
        assert len(result["other.com"]) == 1


class TestGroupBy:
    def test_custom_key_function(self):
        records = [_make_record(status_code=201), _make_record(status_code=404),
                   _make_record(status_code=500)]
        result = group_by(records, lambda r: "error" if r.status_code >= 400 else "ok")
        assert len(result["ok"]) == 1
        assert len(result["error"]) == 2


class TestGroupSummary:
    def test_returns_counts(self):
        records = [_make_record("GET"), _make_record("POST"), _make_record("GET")]
        groups = group_by_method(records)
        summary = group_summary(groups)
        assert summary["GET"] == 2
        assert summary["POST"] == 1

    def test_empty_groups(self):
        assert group_summary({}) == {}
