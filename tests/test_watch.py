"""Tests for reqwatch.watch."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from datetime import datetime, timezone

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.watch import WatchResult, watch_store


def _make_record(record_id: str = "r1", method: str = "GET") -> RequestRecord:
    return RequestRecord(
        id=record_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        method=method,
        url="http://example.com/api",
        request_headers={},
        request_body=None,
        status_code=200,
        response_headers={},
        response_body=None,
        duration_ms=10.0,
        metadata={},
    )


def _write_store(path: str, records) -> None:
    data = {"records": [r.to_dict() for r in records]}
    with open(path, "w") as fh:
        json.dump(data, fh)


class TestWatchResult:
    def test_has_errors_false_when_empty(self):
        r = WatchResult(seen=3)
        assert not r.has_errors

    def test_has_errors_true_when_errors(self):
        r = WatchResult(seen=1, errors=["oops"])
        assert r.has_errors

    def test_summary_no_errors(self):
        r = WatchResult(seen=5)
        assert "5" in r.summary()
        assert "error" not in r.summary().lower()

    def test_summary_with_errors(self):
        r = WatchResult(seen=2, errors=["bad"])
        assert "error" in r.summary().lower()


class TestWatchStore:
    def test_picks_up_existing_records(self, tmp_path):
        store_path = str(tmp_path / "store.json")
        records = [_make_record("a"), _make_record("b")]
        _write_store(store_path, records)

        collected = []
        result = watch_store(
            store_path,
            on_record=collected.append,
            poll_interval=0.05,
            max_records=2,
        )
        assert len(collected) == 2
        assert result.seen == 2

    def test_does_not_duplicate_records(self, tmp_path):
        store_path = str(tmp_path / "store.json")
        _write_store(store_path, [_make_record("x")])

        collected = []
        result = watch_store(
            store_path,
            on_record=collected.append,
            poll_interval=0.05,
            max_records=1,
        )
        assert len(collected) == 1

    def test_stops_after_timeout(self, tmp_path):
        store_path = str(tmp_path / "store.json")
        _write_store(store_path, [])

        result = watch_store(
            store_path,
            on_record=lambda r: None,
            poll_interval=0.05,
            timeout=0.15,
        )
        assert result.seen == 0
        assert not result.has_errors

    def test_records_error_on_bad_path(self):
        result = watch_store(
            "/nonexistent/path/store.json",
            on_record=lambda r: None,
            poll_interval=0.05,
            timeout=0.12,
        )
        assert result.has_errors
