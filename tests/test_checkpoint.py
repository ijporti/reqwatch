"""Tests for reqwatch.checkpoint."""

from __future__ import annotations

import os
import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.checkpoint import (
    checkpoint_summary,
    delete_checkpoint,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


def _make_record(method: str = "GET", url: str = "http://example.com", status: int = 200) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body="ok",
        timestamp="2024-01-01T00:00:00",
        duration_ms=10.0,
        metadata={},
    )


def _make_store(*records: RequestRecord) -> RequestStore:
    store = RequestStore()
    for r in records:
        store.add(r)
    return store


class TestSaveAndLoad:
    def test_roundtrip_preserves_record_count(self, tmp_path):
        store = _make_store(_make_record(), _make_record(method="POST"))
        save_checkpoint(store, "snap1", directory=str(tmp_path))
        loaded = load_checkpoint("snap1", directory=str(tmp_path))
        assert len(loaded.all()) == 2

    def test_roundtrip_preserves_fields(self, tmp_path):
        record = _make_record(method="DELETE", url="http://api.test/items/1", status=204)
        store = _make_store(record)
        save_checkpoint(store, "snap2", directory=str(tmp_path))
        loaded = load_checkpoint("snap2", directory=str(tmp_path))
        r = loaded.all()[0]
        assert r.method == "DELETE"
        assert r.url == "http://api.test/items/1"
        assert r.response_status == 204

    def test_save_returns_correct_path(self, tmp_path):
        store = _make_store(_make_record())
        path = save_checkpoint(store, "mysnap", directory=str(tmp_path))
        assert path == os.path.join(str(tmp_path), "mysnap.checkpoint.json")
        assert os.path.isfile(path)

    def test_load_missing_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_checkpoint("nonexistent", directory=str(tmp_path))


class TestListCheckpoints:
    def test_empty_directory_returns_empty(self, tmp_path):
        assert list_checkpoints(str(tmp_path)) == []

    def test_missing_directory_returns_empty(self, tmp_path):
        assert list_checkpoints(str(tmp_path / "nope")) == []

    def test_lists_saved_checkpoints(self, tmp_path):
        store = _make_store(_make_record())
        save_checkpoint(store, "alpha", directory=str(tmp_path))
        save_checkpoint(store, "beta", directory=str(tmp_path))
        names = list_checkpoints(str(tmp_path))
        assert "alpha" in names
        assert "beta" in names

    def test_ignores_non_checkpoint_files(self, tmp_path):
        (tmp_path / "other.json").write_text("{}")
        store = _make_store(_make_record())
        save_checkpoint(store, "only_one", directory=str(tmp_path))
        names = list_checkpoints(str(tmp_path))
        assert names == ["only_one"]


class TestDeleteCheckpoint:
    def test_delete_existing_returns_true(self, tmp_path):
        store = _make_store(_make_record())
        save_checkpoint(store, "to_delete", directory=str(tmp_path))
        result = delete_checkpoint("to_delete", directory=str(tmp_path))
        assert result is True
        assert list_checkpoints(str(tmp_path)) == []

    def test_delete_missing_returns_false(self, tmp_path):
        result = delete_checkpoint("ghost", directory=str(tmp_path))
        assert result is False


class TestCheckpointSummary:
    def test_summary_contains_name(self):
        store = _make_store(_make_record())
        s = checkpoint_summary("mysnap", store)
        assert "mysnap" in s

    def test_summary_contains_record_count(self):
        store = _make_store(_make_record(), _make_record(), _make_record())
        s = checkpoint_summary("snap", store)
        assert "3" in s
