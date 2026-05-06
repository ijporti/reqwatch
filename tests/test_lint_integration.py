"""Integration tests for lint applied with filters."""

from reqwatch.core import RequestRecord
from reqwatch.filter import filter_by_method, filter_by_status_range
from reqwatch.lint import lint_all, lint_summary


def _make_record(
    method="GET",
    url="http://example.com/api",
    request_headers=None,
    response_status=200,
    request_body=None,
):
    return RequestRecord(
        method=method,
        url=url,
        request_headers=request_headers or {"Authorization": "Bearer tok"},
        request_body=request_body,
        response_status=response_status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
        duration_ms=20,
        metadata={},
    )


class TestLintWithFilter:
    def test_lint_only_post_records(self):
        records = [
            _make_record(method="GET"),
            _make_record(method="POST", request_headers={"Authorization": "Bearer tok"}),
        ]
        posts = filter_by_method(records, "POST")
        results = lint_all(posts, rules=["missing_content_type"])
        assert len(results) == 1
        assert any("Content-Type" in w for w in results[0].warnings)

    def test_lint_only_error_responses(self):
        records = [
            _make_record(response_status=200),
            _make_record(response_status=404),
            _make_record(response_status=500),
        ]
        errors = filter_by_status_range(records, 400, 599)
        results = lint_all(errors, rules=["error_status"])
        assert len(results) == 2
        for r in results:
            assert not r.is_clean

    def test_summary_reflects_filtered_set(self):
        records = [
            _make_record(response_status=200),
            _make_record(response_status=500),
            _make_record(response_status=503),
        ]
        errors = filter_by_status_range(records, 500, 599)
        results = lint_all(errors, rules=["error_status"])
        summary = lint_summary(results)
        assert "2" in summary
        assert "0 clean" in summary

    def test_all_clean_after_filtering_out_errors(self):
        records = [
            _make_record(response_status=200),
            _make_record(response_status=500),
        ]
        ok_records = filter_by_status_range(records, 200, 299)
        results = lint_all(ok_records, rules=["error_status"])
        assert all(r.is_clean for r in results)
