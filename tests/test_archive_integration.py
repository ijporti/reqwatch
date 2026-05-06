"""Integration tests: archive -> restore preserves all record fields."""

import os
import tempfile
from datetime import datetime, timezone

import pytest

from reqwatch.archive import archive_store, restore_store
from reqwatch.core import RequestStore, RequestRecord


def _make_record(**kwargs) -> RequestRecord:
    defaults = dict(
        id="rec-01",
        timestamp=datetime(2024, 3, 15, 8, 30, 0, tzinfo=timezone.utc).isoformat(),
        method="GET",
        url="http://service.internal/health",
        request_headers={"Accept": "application/json"},
        request_body=None,
        response_status=200,
        response_headers={"Content-Type": "application/json"},
        response_body='{"status": "ok"}',
        metadata={"env": "staging"},
    )
    defaults.update(kwargs)
    return RequestRecord(**defaults)


class TestArchiveRoundtrip:
    def _roundtrip(self, records):
        store = RequestStore()
        for r in records:
            store.add(r)
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive_store(store, path)
            return restore_store(path)
        finally:
            os.unlink(path)

    def test_preserves_method(self):
        records = self._roundtrip([_make_record(method="DELETE")])
        assert records[0].method == "DELETE"

    def test_preserves_url(self):
        records = self._roundtrip([_make_record(url="http://api.example.com/v2/users")])
        assert records[0].url == "http://api.example.com/v2/users"

    def test_preserves_response_body(self):
        records = self._roundtrip([_make_record(response_body='{"id": 42}')])
        assert records[0].response_body == '{"id": 42}'

    def test_preserves_metadata(self):
        records = self._roundtrip([_make_record(metadata={"tag": "slow"})])
        assert records[0].metadata.get("tag") == "slow"

    def test_multiple_records_order_preserved(self):
        recs = [
            _make_record(id=f"r{i}", url=f"http://host/{i}")
            for i in range(5)
        ]
        restored = self._roundtrip(recs)
        assert len(restored) == 5
        for i, r in enumerate(restored):
            assert r.url == f"http://host/{i}"

    def test_large_body_survives_compression(self):
        big_body = "x" * 50_000
        records = self._roundtrip([_make_record(response_body=big_body)])
        assert records[0].response_body == big_body
