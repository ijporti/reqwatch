"""Tests for reqwatch.score."""

import pytest

from reqwatch.core import RequestRecord
from reqwatch.score import ScoreResult, score_record, score_all, score_summary


def _make_record(
    method="GET",
    url="http://example.com/api",
    response_status=200,
    duration_ms=100.0,
    error=None,
):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=response_status,
        response_headers={},
        response_body=None,
        duration_ms=duration_ms,
        error=error,
    )


class TestScoreResult:
    def test_summary_contains_score(self):
        r = _make_record()
        result = ScoreResult(record=r, score=3.5, reasons=["slow"])
        s = result.summary()
        assert "3.50" in s

    def test_summary_contains_method_and_url(self):
        r = _make_record(method="POST", url="http://svc/data")
        result = ScoreResult(record=r, score=0.0, reasons=[])
        s = result.summary()
        assert "POST" in s
        assert "http://svc/data" in s

    def test_summary_no_criteria_message(self):
        r = _make_record()
        result = ScoreResult(record=r, score=0.0, reasons=[])
        assert "no criteria matched" in result.summary()


class TestScoreRecord:
    def test_zero_score_for_clean_fast_2xx(self):
        r = _make_record(response_status=200, duration_ms=100.0)
        result = score_record(r)
        assert result.score == 0.0

    def test_error_adds_score(self):
        r = _make_record(error="connection refused")
        result = score_record(r, error_weight=5.0)
        assert result.score >= 5.0
        assert any("error" in reason for reason in result.reasons)

    def test_5xx_adds_server_error_weight(self):
        r = _make_record(response_status=503)
        result = score_record(r, server_error_weight=4.0)
        assert result.score >= 4.0
        assert any("5xx" in reason for reason in result.reasons)

    def test_4xx_adds_client_error_weight(self):
        r = _make_record(response_status=404)
        result = score_record(r, client_error_weight=2.0)
        assert result.score >= 2.0
        assert any("4xx" in reason for reason in result.reasons)

    def test_slow_request_adds_slow_weight(self):
        r = _make_record(duration_ms=1200.0)
        result = score_record(r, slow_threshold_ms=500.0, slow_weight=3.0)
        assert result.score >= 3.0
        assert any("slow" in reason for reason in result.reasons)

    def test_fast_request_no_slow_penalty(self):
        r = _make_record(duration_ms=50.0)
        result = score_record(r, slow_threshold_ms=500.0, slow_weight=3.0)
        assert not any("slow" in reason for reason in result.reasons)

    def test_method_weight_applied(self):
        r = _make_record(method="DELETE")
        result = score_record(r, method_weights={"DELETE": 1.5})
        assert result.score >= 1.5
        assert any("DELETE" in reason for reason in result.reasons)

    def test_none_duration_no_slow_penalty(self):
        r = _make_record(duration_ms=None)
        result = score_record(r)
        assert result.score == 0.0


class TestScoreAll:
    def test_sorted_descending(self):
        records = [
            _make_record(response_status=200),
            _make_record(response_status=500),
            _make_record(response_status=404),
        ]
        results = score_all(records)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_returns_empty(self):
        assert score_all([]) == []


class TestScoreSummary:
    def test_empty_returns_no_records_message(self):
        assert "No records" in score_summary([])

    def test_summary_contains_total_count(self):
        records = [_make_record() for _ in range(3)]
        results = score_all(records)
        s = score_summary(results)
        assert "3" in s

    def test_summary_mentions_top_record(self):
        records = [
            _make_record(method="GET", url="http://a.com", response_status=200),
            _make_record(method="POST", url="http://b.com", response_status=500),
        ]
        results = score_all(records)
        s = score_summary(results)
        assert "POST" in s or "http://b.com" in s
