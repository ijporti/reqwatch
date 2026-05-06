"""Tests for reqwatch.snapshot."""

from __future__ import annotations

import os

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.snapshot import (
    SnapshotResult,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
    snapshot_summary,
)


def _make_record(method: str = "GET", url: str = "http://example.com") -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body='{"ok": true}',
        timestamp="2024-01-01T00:00:00",
        metadata={},
    )


def _make_store(*records: RequestRecord) -> RequestStore:
    store = RequestStore()
    for r in records:
        store.add(r)
    return store


class TestSnapshotResult:
    def test_succeeded_when_no_error(self):
        r = SnapshotResult(name="snap1", record_count=3, path="/tmp/snap1.snapshot.json")
        assert r.succeeded() is True

    def test_not_succeeded_when_error(self):
        r = SnapshotResult(name="snap1", record_count=0, path="/tmp/x", error="oops")
        assert r.succeeded() is False

    def test_summary_success(self):
        r = SnapshotResult(name="snap1", record_count=2, path="/tmp/snap1.snapshot.json")
        assert "snap1" in r.summary()
        assert "2" in r.summary()

    def test_summary_failure(self):
        r = SnapshotResult(name="snap1", record_count=0, path="/tmp/x", error="disk full")
        assert "failed" in r.summary()
        assert "disk full" in r.summary()


class TestSaveAndLoad:
    def test_roundtrip_preserves_count(self, tmp_path):
        store = _make_store(_make_record(), _make_record(method="POST"))
        result = save_snapshot(store, "test", directory=str(tmp_path))
        assert result.succeeded()
        assert result.record_count == 2
        loaded = load_snapshot("test", directory=str(tmp_path))
        assert loaded is not None
        assert len(loaded.all()) == 2

    def test_roundtrip_preserves_method(self, tmp_path):
        store = _make_store(_make_record(method="DELETE", url="http://x.com/res"))
        save_snapshot(store, "s", directory=str(tmp_path))
        loaded = load_snapshot("s", directory=str(tmp_path))
        assert loaded.all()[0].method == "DELETE"

    def test_load_missing_returns_none(self, tmp_path):
        result = load_snapshot("nonexistent", directory=str(tmp_path))
        assert result is None


class TestListAndDelete:
    def test_list_empty_dir(self, tmp_path):
        assert list_snapshots(directory=str(tmp_path)) == []

    def test_list_missing_dir(self, tmp_path):
        assert list_snapshots(directory=str(tmp_path / "nope")) == []

    def test_lists_saved_snapshots(self, tmp_path):
        store = _make_store(_make_record())
        save_snapshot(store, "alpha", directory=str(tmp_path))
        save_snapshot(store, "beta", directory=str(tmp_path))
        names = list_snapshots(directory=str(tmp_path))
        assert "alpha" in names
        assert "beta" in names

    def test_delete_removes_snapshot(self, tmp_path):
        store = _make_store(_make_record())
        save_snapshot(store, "todel", directory=str(tmp_path))
        assert delete_snapshot("todel", directory=str(tmp_path)) is True
        assert list_snapshots(directory=str(tmp_path)) == []

    def test_delete_nonexistent_returns_false(self, tmp_path):
        assert delete_snapshot("ghost", directory=str(tmp_path)) is False


class TestSnapshotSummary:
    def test_empty_list(self):
        assert "No snapshots" in snapshot_summary([])

    def test_lists_names(self):
        text = snapshot_summary(["a", "b"])
        assert "a" in text
        assert "b" in text
