"""Tests for reqwatch.summarize."""

from __future__ import annotations

from reqwatch.core import RequestRecord
from reqwatch.summarize import SummarizeResult, summarize_records


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api",
    response_status: int = 200,
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=response_status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
        metadata={},
    )


class TestSummarizeEmpty:
    def test_empty_total_is_zero(self):
        result = summarize_records([])
        assert result.total == 0

    def test_empty_method_counts_empty(self):
        result = summarize_records([])
        assert result.method_counts == {}

    def test_empty_status_counts_empty(self):
        result = summarize_records([])
        assert result.status_counts == {}

    def test_empty_error_count_zero(self):
        result = summarize_records([])
        assert result.error_count == 0

    def test_empty_note_present(self):
        result = summarize_records([])
        assert any("No records" in n for n in result.notes)


class TestSummarizeCounts:
    def test_total_matches_record_count(self):
        records = [_make_record() for _ in range(5)]
        result = summarize_records(records)
        assert result.total == 5

    def test_method_counts_aggregated(self):
        records = [
            _make_record(method="GET"),
            _make_record(method="GET"),
            _make_record(method="POST"),
        ]
        result = summarize_records(records)
        assert result.method_counts["GET"] == 2
        assert result.method_counts["POST"] == 1

    def test_method_normalised_to_upper(self):
        records = [_make_record(method="get")]
        result = summarize_records(records)
        assert "GET" in result.method_counts

    def test_status_counts_aggregated(self):
        records = [
            _make_record(response_status=200),
            _make_record(response_status=200),
            _make_record(response_status=404),
        ]
        result = summarize_records(records)
        assert result.status_counts[200] == 2
        assert result.status_counts[404] == 1

    def test_error_count_only_5xx(self):
        records = [
            _make_record(response_status=200),
            _make_record(response_status=500),
            _make_record(response_status=503),
        ]
        result = summarize_records(records)
        assert result.error_count == 2

    def test_unique_hosts_extracted(self):
        records = [
            _make_record(url="http://alpha.com/x"),
            _make_record(url="http://beta.com/y"),
            _make_record(url="http://alpha.com/z"),
        ]
        result = summarize_records(records)
        assert sorted(result.unique_hosts) == ["alpha.com", "beta.com"]


class TestSummarizeResultSummary:
    def test_summary_contains_total(self):
        result = SummarizeResult(
            total=3,
            method_counts={"GET": 3},
            status_counts={200: 3},
            error_count=0,
            unique_hosts=["example.com"],
        )
        assert "3" in result.summary()

    def test_summary_contains_method(self):
        result = SummarizeResult(
            total=1,
            method_counts={"DELETE": 1},
            status_counts={204: 1},
            error_count=0,
            unique_hosts=[],
        )
        assert "DELETE" in result.summary()

    def test_summary_contains_error_count(self):
        result = SummarizeResult(
            total=2,
            method_counts={"POST": 2},
            status_counts={500: 2},
            error_count=2,
            unique_hosts=[],
        )
        assert "2" in result.summary()
