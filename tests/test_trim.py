"""Tests for reqwatch.trim."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from reqwatch.core import RequestRecord
from reqwatch.trim import TrimResult, trim_after, trim_before, trim_to_last_n


def _make_record(timestamp: str, url: str = "http://example.com") -> RequestRecord:
    return RequestRecord(
        id="abc",
        timestamp=timestamp,
        method="GET",
        url=url,
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body=None,
        metadata={},
    )


class TestTrimResult:
    def test_succeeded_when_no_error(self):
        r = TrimResult(original_count=5, trimmed_count=3)
        assert r.succeeded() is True

    def test_not_succeeded_when_error(self):
        r = TrimResult(original_count=5, trimmed_count=5, error="oops")
        assert r.succeeded() is False

    def test_summary_shows_counts(self):
        r = TrimResult(original_count=10, trimmed_count=4)
        s = r.summary()
        assert "10" in s
        assert "4" in s

    def test_summary_error(self):
        r = TrimResult(original_count=3, trimmed_count=3, error="bad n")
        assert "failed" in r.summary().lower()


class TestTrimToLastN:
    def _records(self) -> List[RequestRecord]:
        return [
            _make_record("2024-01-01T00:00:00"),
            _make_record("2024-01-02T00:00:00"),
            _make_record("2024-01-03T00:00:00"),
            _make_record("2024-01-04T00:00:00"),
        ]

    def test_keeps_most_recent(self):
        recs = self._records()
        result = trim_to_last_n(recs, 2)
        assert result.trimmed_count == 2
        assert recs[0].timestamp == "2024-01-03T00:00:00"
        assert recs[1].timestamp == "2024-01-04T00:00:00"

    def test_zero_keeps_none(self):
        recs = self._records()
        result = trim_to_last_n(recs, 0)
        assert result.trimmed_count == 0
        assert recs == []

    def test_n_larger_than_list_keeps_all(self):
        recs = self._records()
        result = trim_to_last_n(recs, 100)
        assert result.trimmed_count == 4

    def test_negative_n_returns_error(self):
        recs = self._records()
        result = trim_to_last_n(recs, -1)
        assert not result.succeeded()
        assert len(recs) == 4  # unchanged


class TestTrimBefore:
    def test_removes_older_records(self):
        recs = [
            _make_record("2024-01-01T00:00:00"),
            _make_record("2024-01-05T00:00:00"),
        ]
        cutoff = datetime(2024, 1, 3)
        result = trim_before(recs, cutoff)
        assert result.trimmed_count == 1
        assert recs[0].timestamp == "2024-01-05T00:00:00"

    def test_keeps_all_when_none_before_cutoff(self):
        recs = [_make_record("2024-06-01T00:00:00")]
        result = trim_before(recs, datetime(2024, 1, 1))
        assert result.trimmed_count == 1


class TestTrimAfter:
    def test_removes_newer_records(self):
        recs = [
            _make_record("2024-01-01T00:00:00"),
            _make_record("2024-06-01T00:00:00"),
        ]
        cutoff = datetime(2024, 3, 1)
        result = trim_after(recs, cutoff)
        assert result.trimmed_count == 1
        assert recs[0].timestamp == "2024-01-01T00:00:00"

    def test_keeps_all_when_none_after_cutoff(self):
        recs = [_make_record("2024-01-01T00:00:00")]
        result = trim_after(recs, datetime(2025, 1, 1))
        assert result.trimmed_count == 1
