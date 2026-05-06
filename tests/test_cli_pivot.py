"""CLI tests for the pivot command."""

from __future__ import annotations

import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_pivot import cmd_pivot


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api",
    status: int = 200,
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
    )


def _write_store(path: str, records) -> None:
    store = RequestStore(path)
    store.save(records)


class _Args:
    def __init__(self, store, dimension, fmt="text"):
        self.store = store
        self.dimension = dimension
        self.format = fmt


class TestCLIPivot:
    def test_text_output_shows_dimension(self, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record()])
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cmd_pivot(_Args(p, "method"))
            out = mock_out.getvalue()
        assert "method" in out

    def test_text_output_shows_groups(self, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record(method="GET"), _make_record(method="POST")])
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cmd_pivot(_Args(p, "method"))
            out = mock_out.getvalue()
        assert "GET" in out
        assert "POST" in out

    def test_json_output_has_groups_key(self, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record()])
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cmd_pivot(_Args(p, "status", fmt="json"))
            data = json.loads(mock_out.getvalue())
        assert "groups" in data
        assert "dimension" in data

    def test_json_output_dimension_matches(self, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record()])
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cmd_pivot(_Args(p, "host", fmt="json"))
            data = json.loads(mock_out.getvalue())
        assert data["dimension"] == "host"

    def test_missing_store_exits(self, tmp_path):
        p = str(tmp_path / "missing.json")
        with pytest.raises(SystemExit):
            cmd_pivot(_Args(p, "method"))
