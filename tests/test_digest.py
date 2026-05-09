"""Tests for reqwatch.digest."""
import pytest
from reqwatch.digest import DigestResult, compute_digest, digest_summary
from reqwatch.core import RequestRecord


def _make_record(method="GET", url="http://example.com/api", status=200, ts="2024-01-01T00:00:00"):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_headers={},
        response_body=None,
        status_code=status,
        timestamp=ts,
        duration_ms=10.0,
        metadata={},
    )


class TestDigestResult:
    def test_succeeded_when_no_error(self):
        r = DigestResult(digest="abc", total=1, method_counts={}, status_counts={})
        assert r.succeeded() is True

    def test_not_succeeded_when_error(self):
        r = DigestResult(digest="", total=0, method_counts={}, status_counts={}, error="oops")
        assert r.succeeded() is False

    def test_summary_contains_digest_prefix(self):
        r = DigestResult(digest="deadbeef1234abcd", total=3, method_counts={"GET": 3}, status_counts={"200": 3})
        s = r.summary()
        assert "deadbeef1234" in s

    def test_summary_contains_total(self):
        r = DigestResult(digest="abc123", total=7, method_counts={}, status_counts={})
        assert "total=7" in r.summary()

    def test_summary_error_branch(self):
        r = DigestResult(digest="", total=0, method_counts={}, status_counts={}, error="bad")
        assert "error" in r.summary().lower()


class TestComputeDigest:
    def test_empty_list_returns_zero_total(self):
        result = compute_digest([])
        assert result.total == 0

    def test_empty_list_returns_non_empty_digest(self):
        result = compute_digest([])
        assert len(result.digest) == 64  # sha256 hex

    def test_single_record_total_one(self):
        result = compute_digest([_make_record()])
        assert result.total == 1

    def test_method_counts_populated(self):
        records = [_make_record("GET"), _make_record("POST"), _make_record("GET")]
        result = compute_digest(records)
        assert result.method_counts["GET"] == 2
        assert result.method_counts["POST"] == 1

    def test_status_counts_populated(self):
        records = [_make_record(status=200), _make_record(status=404), _make_record(status=200)]
        result = compute_digest(records)
        assert result.status_counts["200"] == 2
        assert result.status_counts["404"] == 1

    def test_same_records_same_digest(self):
        r1 = _make_record("GET", "http://a.com", 200, "2024-01-01T00:00:00")
        r2 = _make_record("GET", "http://a.com", 200, "2024-01-01T00:00:00")
        d1 = compute_digest([r1])
        d2 = compute_digest([r2])
        assert d1.digest == d2.digest

    def test_different_records_different_digest(self):
        r1 = _make_record("GET", "http://a.com")
        r2 = _make_record("POST", "http://b.com")
        d1 = compute_digest([r1])
        d2 = compute_digest([r2])
        assert d1.digest != d2.digest

    def test_order_independent_digest(self):
        r1 = _make_record("GET", "http://a.com", 200, "2024-01-01T00:00:00")
        r2 = _make_record("POST", "http://b.com", 201, "2024-01-02T00:00:00")
        d1 = compute_digest([r1, r2])
        d2 = compute_digest([r2, r1])
        assert d1.digest == d2.digest

    def test_method_normalised_to_upper(self):
        r_lower = _make_record(method="get")
        r_upper = _make_record(method="GET")
        # method_counts key should be uppercase
        result = compute_digest([r_lower])
        assert "GET" in result.method_counts

    def test_digest_summary_returns_string(self):
        records = [_make_record()]
        s = digest_summary(records)
        assert isinstance(s, str)
        assert "Digest" in s
