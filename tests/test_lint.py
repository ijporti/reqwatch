"""Tests for reqwatch.lint."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.lint import (
    LintResult,
    lint_record,
    lint_all,
    lint_summary,
)


def _make_record(
    method="GET",
    url="http://example.com/api",
    request_headers=None,
    request_body=None,
    response_status=200,
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
        duration_ms=50,
        metadata={},
    )


class TestLintResult:
    def test_is_clean_when_no_warnings(self):
        rec = _make_record()
        result = LintResult(record=rec, warnings=[])
        assert result.is_clean is True

    def test_not_clean_when_warnings_present(self):
        rec = _make_record()
        result = LintResult(record=rec, warnings=["some issue"])
        assert result.is_clean is False

    def test_summary_ok_format(self):
        rec = _make_record(method="GET")
        result = LintResult(record=rec, warnings=[])
        assert result.summary().startswith("OK")

    def test_summary_warn_format(self):
        rec = _make_record(method="POST")
        result = LintResult(record=rec, warnings=["missing Content-Type"])
        assert result.summary().startswith("WARN")
        assert "missing Content-Type" in result.summary()


def test_clean_get_request():
    rec = _make_record(method="GET", response_status=200)
    result = lint_record(rec)
    # GET with auth and 200 should only potentially warn about missing_content_type (not applicable)
    assert "missing Content-Type header on request" not in result.warnings


def test_post_without_content_type_warns():
    rec = _make_record(
        method="POST",
        request_headers={"Authorization": "Bearer tok"},
    )
    result = lint_record(rec)
    assert any("Content-Type" in w for w in result.warnings)


def test_post_with_content_type_no_warn():
    rec = _make_record(
        method="POST",
        request_headers={"Authorization": "Bearer tok", "Content-Type": "application/json"},
    )
    result = lint_record(rec)
    assert not any("Content-Type" in w for w in result.warnings)


def test_large_body_warns():
    big_body = "x" * (1024 * 101)
    rec = _make_record(method="POST", request_body=big_body,
                       request_headers={"Authorization": "Bearer tok", "Content-Type": "application/json"})
    result = lint_record(rec)
    assert any("body exceeds" in w for w in result.warnings)


def test_non_standard_method_warns():
    rec = _make_record(method="BREW")
    result = lint_record(rec)
    assert any("non-standard" in w for w in result.warnings)


def test_missing_auth_warns():
    rec = _make_record(method="GET", request_headers={})
    result = lint_record(rec)
    assert any("authentication" in w for w in result.warnings)


def test_error_status_warns():
    rec = _make_record(response_status=500)
    result = lint_record(rec)
    assert any("500" in w for w in result.warnings)


def test_rule_filtering_skips_disabled_rule():
    rec = _make_record(method="GET", request_headers={}, response_status=200)
    result = lint_record(rec, rules=["large_body"])
    # missing_auth rule is not active, so no auth warning
    assert not any("authentication" in w for w in result.warnings)


def test_lint_all_returns_one_per_record():
    records = [_make_record(), _make_record(method="POST")]
    results = lint_all(records)
    assert len(results) == 2


def test_lint_summary_counts():
    records = [_make_record(), _make_record(method="GET", request_headers={})]
    results = lint_all(records)
    summary = lint_summary(results)
    assert "2" in summary
