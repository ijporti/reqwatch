"""Tests for reqwatch.cli_chain."""

from __future__ import annotations

import json
import os
import tempfile
from typing import List

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_chain import cmd_chain


def _make_record(method: str = "GET", url: str = "http://example.com", status: int = 200) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body="",
        response_headers={},
        response_body="",
        status_code=status,
        timestamp="2024-01-01T00:00:00",
        duration_ms=10.0,
    )


def _write_store(records: List[RequestRecord]) -> str:
    store = RequestStore()
    for r in records:
        store.add(r)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    store.save(tmp.name)
    return tmp.name


class _Args:
    def __init__(self, store: str, limit: int = 0, fmt: str = "text"):
        self.store = store
        self.limit = limit
        self.format = fmt


class TestCLIChain:
    def test_text_output_shows_summary(self, capsys):
        path = _write_store([_make_record(), _make_record()])
        try:
            cmd_chain(_Args(store=path))
            out = capsys.readouterr().out
            assert "2/2" in out
        finally:
            os.unlink(path)

    def test_json_output_has_keys(self, capsys):
        path = _write_store([_make_record()])
        try:
            cmd_chain(_Args(store=path, fmt="json"))
            out = capsys.readouterr().out
            data = json.loads(out)
            assert "succeeded" in data
            assert "length" in data
            assert "outputs" in data
        finally:
            os.unlink(path)

    def test_limit_restricts_records(self, capsys):
        path = _write_store([_make_record() for _ in range(5)])
        try:
            cmd_chain(_Args(store=path, limit=2))
            out = capsys.readouterr().out
            assert "2/2" in out
        finally:
            os.unlink(path)

    def test_empty_store_prints_message(self, capsys):
        path = _write_store([])
        try:
            cmd_chain(_Args(store=path))
            out = capsys.readouterr().out
            assert "No records" in out
        finally:
            os.unlink(path)

    def test_json_succeeded_true(self, capsys):
        path = _write_store([_make_record()])
        try:
            cmd_chain(_Args(store=path, fmt="json"))
            data = json.loads(capsys.readouterr().out)
            assert data["succeeded"] is True
        finally:
            os.unlink(path)
