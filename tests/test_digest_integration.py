"""Integration tests for digest: verify stability and sensitivity."""
import pytest
from reqwatch.core import RequestRecord
from reqwatch.digest import compute_digest


def _make_record(method="GET", url="http://example.com", status=200, ts="2024-01-01T00:00:00"):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_headers={},
        response_body=None,
        status_code=status,
        timestamp=ts,
        duration_ms=1.0,
        metadata={},
    )


class TestDigestIntegration:
    def test_adding_record_changes_digest(self):
        r1 = _make_record()
        d1 = compute_digest([r1])
        r2 = _make_record("POST", "http://example.com/other", 201, "2024-02-01T00:00:00")
        d2 = compute_digest([r1, r2])
        assert d1.digest != d2.digest

    def test_digest_stable_across_calls(self):
        records = [
            _make_record("GET", "http://a.com", 200, "2024-01-01T00:00:00"),
            _make_record("POST", "http://b.com", 201, "2024-01-02T00:00:00"),
        ]
        d1 = compute_digest(records)
        d2 = compute_digest(records)
        assert d1.digest == d2.digest

    def test_url_change_changes_digest(self):
        r1 = _make_record(url="http://a.com")
        r2 = _make_record(url="http://b.com")
        assert compute_digest([r1]).digest != compute_digest([r2]).digest

    def test_status_change_changes_digest(self):
        r1 = _make_record(status=200)
        r2 = _make_record(status=500)
        assert compute_digest([r1]).digest != compute_digest([r2]).digest

    def test_empty_digest_is_deterministic(self):
        assert compute_digest([]).digest == compute_digest([]).digest
