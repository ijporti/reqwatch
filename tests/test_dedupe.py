"""Tests for reqwatch.dedupe module."""

import pytest
from datetime import datetime
from reqwatch.core import RequestRecord
from reqwatch.dedupe import find_duplicates, deduplicate, dedupe_summary


def _make_record(method="GET", url="http://example.com/api", status=200,
                 body=None, timestamp=None):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=body,
        response_headers={},
        response_body="ok",
        status_code=status,
        timestamp=timestamp or datetime(2024, 1, 1, 12, 0, 0).isoformat(),
        duration_ms=50.0,
    )


class TestFindDuplicates:
    def test_no_duplicates_returns_empty(self):
        records = [
            _make_record(url="http://a.com"),
            _make_record(url="http://b.com"),
        ]
        assert find_duplicates(records) == {}

    def test_finds_duplicate_group(self):
        r1 = _make_record(url="http://a.com")
        r2 = _make_record(url="http://a.com")
        result = find_duplicates([r1, r2])
        assert len(result) == 1
        assert len(list(result.values())[0]) == 2

    def test_different_methods_not_duplicates(self):
        r1 = _make_record(method="GET")
        r2 = _make_record(method="POST")
        assert find_duplicates([r1, r2]) == {}

    def test_match_response_considers_status(self):
        r1 = _make_record(status=200)
        r2 = _make_record(status=404)
        # Without match_response they are duplicates (same method+url+body)
        assert len(find_duplicates([r1, r2])) == 1
        # With match_response they differ by status
        assert find_duplicates([r1, r2], match_response=True) == {}

    def test_empty_list_returns_empty(self):
        assert find_duplicates([]) == {}


class TestDeduplicate:
    def test_keep_first_removes_later_duplicates(self):
        r1 = _make_record(url="http://a.com", timestamp="2024-01-01T10:00:00")
        r2 = _make_record(url="http://a.com", timestamp="2024-01-01T11:00:00")
        result = deduplicate([r1, r2], keep="first")
        assert len(result) == 1
        assert result[0] is r1

    def test_keep_last_removes_earlier_duplicates(self):
        r1 = _make_record(url="http://a.com", timestamp="2024-01-01T10:00:00")
        r2 = _make_record(url="http://a.com", timestamp="2024-01-01T11:00:00")
        result = deduplicate([r1, r2], keep="last")
        assert len(result) == 1
        assert result[0] is r2

    def test_no_duplicates_unchanged(self):
        records = [
            _make_record(url="http://a.com"),
            _make_record(url="http://b.com"),
        ]
        result = deduplicate(records)
        assert len(result) == 2

    def test_invalid_keep_raises(self):
        with pytest.raises(ValueError, match="keep must be"):
            deduplicate([], keep="middle")

    def test_preserves_original_order(self):
        r1 = _make_record(url="http://a.com")
        r2 = _make_record(url="http://b.com")
        r3 = _make_record(url="http://a.com")
        result = deduplicate([r1, r2, r3], keep="first")
        assert result == [r1, r2]


class TestDedupeSummary:
    def test_summary_no_duplicates(self):
        records = [_make_record(url="http://a.com"), _make_record(url="http://b.com")]
        s = dedupe_summary(records)
        assert "Total records: 2" in s
        assert "Duplicate groups: 0" in s
        assert "Redundant records: 0" in s

    def test_summary_with_duplicates(self):
        r1 = _make_record(url="http://a.com")
        r2 = _make_record(url="http://a.com")
        r3 = _make_record(url="http://a.com")
        s = dedupe_summary([r1, r2, r3])
        assert "Total records: 3" in s
        assert "Duplicate groups: 1" in s
        assert "Redundant records: 2" in s
