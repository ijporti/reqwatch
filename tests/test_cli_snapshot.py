"""CLI-level tests for the snapshot sub-command."""

from __future__ import annotations

import json
import os
from io import StringIO
from unittest.mock import patch

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_snapshot import build_snapshot_parser, cmd_snapshot

import argparse


def _make_record(method: str = "GET", url: str = "http://example.com") -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body="ok",
        timestamp="2024-01-01T00:00:00",
        metadata={},
    )


def _write_store(path: str, *records: RequestRecord) -> None:
    store = RequestStore()
    for r in records:
        store.add(r)
    store.save(path)


def _run_snapshot(tmp_path, *argv: str) -> str:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    build_snapshot_parser(subs)
    store_file = str(tmp_path / "store.json")
    snap_dir = str(tmp_path / "snaps")
    full_argv = [
        "snapshot",
        "--store", store_file,
        "--dir", snap_dir,
    ] + list(argv)
    args = parser.parse_args(full_argv)
    buf = StringIO()
    with patch("sys.stdout", buf):
        args.func(args)
    return buf.getvalue()


class TestCLISnapshot:
    def test_save_text_output_mentions_name(self, tmp_path):
        _write_store(str(tmp_path / "store.json"), _make_record())
        out = _run_snapshot(tmp_path, "save", "mysnap")
        assert "mysnap" in out

    def test_save_json_output_has_keys(self, tmp_path):
        _write_store(str(tmp_path / "store.json"), _make_record())
        out = _run_snapshot(tmp_path, "--format", "json", "save", "s1")
        data = json.loads(out)
        assert "name" in data
        assert "record_count" in data
        assert data["succeeded"] is True

    def test_list_shows_saved_snapshot(self, tmp_path):
        _write_store(str(tmp_path / "store.json"), _make_record())
        _run_snapshot(tmp_path, "save", "listed")
        out = _run_snapshot(tmp_path, "list")
        assert "listed" in out

    def test_list_json_returns_list(self, tmp_path):
        _write_store(str(tmp_path / "store.json"), _make_record())
        _run_snapshot(tmp_path, "save", "j1")
        out = _run_snapshot(tmp_path, "--format", "json", "list")
        data = json.loads(out)
        assert isinstance(data, list)
        assert "j1" in data

    def test_restore_writes_store(self, tmp_path):
        store_file = str(tmp_path / "store.json")
        _write_store(store_file, _make_record(method="DELETE"))
        _run_snapshot(tmp_path, "save", "r1")
        # clear the store
        _write_store(store_file)
        _run_snapshot(tmp_path, "restore", "r1")
        restored = RequestStore()
        restored.load(store_file)
        assert len(restored.all()) == 1
        assert restored.all()[0].method == "DELETE"

    def test_delete_removes_from_list(self, tmp_path):
        _write_store(str(tmp_path / "store.json"), _make_record())
        _run_snapshot(tmp_path, "save", "todel")
        _run_snapshot(tmp_path, "delete", "todel")
        out = _run_snapshot(tmp_path, "list")
        assert "todel" not in out
