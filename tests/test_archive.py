"""Tests for reqwatch.archive."""

import gzip
import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from reqwatch.archive import (
    ArchiveResult,
    archive_store,
    restore_store,
    archive_summary,
)
from reqwatch.core import RequestStore, RequestRecord


def _make_record(method="GET", url="http://example.com/", status=200) -> RequestRecord:
    return RequestRecord(
        id="abc123",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        metadata={},
    )


class TestArchiveResult:
    def test_succeeded_when_no_error(self):
        r = ArchiveResult(path="/tmp/x.gz", record_count=3, size_bytes=512)
        assert r.succeeded is True

    def test_not_succeeded_when_error(self):
        r = ArchiveResult(path="/tmp/x.gz", record_count=0, size_bytes=0, error="oops")
        assert r.succeeded is False

    def test_summary_success(self):
        r = ArchiveResult(path="out.gz", record_count=5, size_bytes=2048)
        assert "5 record" in r.summary()
        assert "out.gz" in r.summary()

    def test_summary_failure(self):
        r = ArchiveResult(path="out.gz", record_count=0, size_bytes=0, error="disk full")
        assert "failed" in r.summary().lower()
        assert "disk full" in r.summary()


class TestArchiveStore:
    def test_creates_file(self):
        store = RequestStore()
        store.add(_make_record())
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            result = archive_store(store, path)
            assert result.succeeded
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_record_count_matches(self):
        store = RequestStore()
        for _ in range(4):
            store.add(_make_record())
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            result = archive_store(store, path)
            assert result.record_count == 4
        finally:
            os.unlink(path)

    def test_invalid_path_returns_error(self):
        store = RequestStore()
        result = archive_store(store, "/no/such/directory/out.gz")
        assert not result.succeeded
        assert result.error is not None


class TestRestoreStore:
    def test_roundtrip(self):
        store = RequestStore()
        rec = _make_record(method="POST", url="http://api.local/v1", status=201)
        store.add(rec)
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive_store(store, path)
            records = restore_store(path)
            assert len(records) == 1
            assert records[0].method == "POST"
            assert records[0].url == "http://api.local/v1"
            assert records[0].response_status == 201
        finally:
            os.unlink(path)

    def test_empty_store_roundtrip(self):
        store = RequestStore()
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as f:
            path = f.name
        try:
            archive_store(store, path)
            records = restore_store(path)
            assert records == []
        finally:
            os.unlink(path)
