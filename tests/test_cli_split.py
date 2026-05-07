"""Tests for reqwatch.cli_split."""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_split import cmd_split


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api",
    response_status: int = 200,
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=response_status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
    )


def _write_store(path: Path, records: list) -> None:
    store = RequestStore()
    for r in records:
        store.add(r)
    store.save(str(path))


class _Args:
    def __init__(self, store: str, by: str = "method", fmt: str = "text"):
        self.store = store
        self.by = by
        self.format = fmt


class TestCLISplit:
    def test_text_output_shows_summary(self, tmp_path, capsys):
        p = tmp_path / "store.json"
        _write_store(p, [_make_record("GET"), _make_record("POST")])
        cmd_split(_Args(str(p)))
        out = capsys.readouterr().out
        assert "GET" in out
        assert "POST" in out

    def test_json_output_is_valid(self, tmp_path, capsys):
        p = tmp_path / "store.json"
        _write_store(p, [_make_record("GET"), _make_record("GET")])
        cmd_split(_Args(str(p), fmt="json"))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "GET" in data
        assert len(data["GET"]) == 2

    def test_split_by_status(self, tmp_path, capsys):
        p = tmp_path / "store.json"
        _write_store(p, [_make_record(response_status=200), _make_record(response_status=500)])
        cmd_split(_Args(str(p), by="status"))
        out = capsys.readouterr().out
        assert "200" in out
        assert "500" in out

    def test_bad_store_path_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            cmd_split(_Args(str(tmp_path / "missing.json")))
