"""Integration tests combining compare + filter for focused diffing."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.compare import compare_stores
from reqwatch.filter import filter_by_method, filter_by_status


def _make_record(method="GET", url="http://example.com/api", status_code=200, response_body="ok"):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body="",
        response_status=status_code,
        response_headers={},
        response_body=response_body,
        timestamp="2024-01-01T00:00:00",
        duration_ms=8.0,
    )


class TestCompareWithFilter:
    def test_compare_only_post_requests(self):
        baseline = [
            _make_record(method="GET", url="http://example.com/a"),
            _make_record(method="POST", url="http://example.com/b", status_code=201),
        ]
        current = [
            _make_record(method="GET", url="http://example.com/a"),
            _make_record(method="POST", url="http://example.com/b", status_code=500),
        ]
        base_posts = filter_by_method(baseline, "POST")
        curr_posts = filter_by_method(current, "POST")
        result = compare_stores(base_posts, curr_posts)
        assert len(result.changed) == 1
        assert result.changed[0][0].response_status == 201
        assert result.changed[0][1].response_status == 500

    def test_compare_only_successful_baseline(self):
        baseline = [
            _make_record(url="http://example.com/ok", status_code=200),
            _make_record(url="http://example.com/err", status_code=500),
        ]
        current = [
            _make_record(url="http://example.com/ok", status_code=404),
        ]
        base_ok = filter_by_status(baseline, 200)
        result = compare_stores(base_ok, current)
        assert len(result.changed) == 1

    def test_no_overlap_all_added_and_removed(self):
        baseline = [_make_record(url="http://example.com/old")]
        current = [_make_record(url="http://example.com/new")]
        result = compare_stores(baseline, current)
        assert len(result.added) == 1
        assert len(result.removed) == 1
        assert result.has_changes

    def test_multiple_methods_tracked_independently(self):
        baseline = [
            _make_record(method="GET", url="http://example.com/x"),
            _make_record(method="POST", url="http://example.com/x"),
        ]
        current = [
            _make_record(method="GET", url="http://example.com/x"),
            _make_record(method="POST", url="http://example.com/x", status_code=422),
        ]
        result = compare_stores(baseline, current)
        assert len(result.unchanged) == 1
        assert len(result.changed) == 1
