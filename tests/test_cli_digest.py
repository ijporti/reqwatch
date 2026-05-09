"""Tests for reqwatch.cli_digest."""
import json
import os
import tempfile
import argparse

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_digest import cmd_digest


def _make_record(method="GET", url="http://example.com/api", status=200):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_headers={},
        response_body=None,
        status_code=status,
        timestamp="2024-01-01T00:00:00",
        duration_ms=5.0,
        metadata={},
    )


def _write_store(path, records):
    store = RequestStore(path)
    for r in records:
        store.add(r)
    store.save()


def _run_digest(store_path, fmt="text", method=None, status=None):
    args = argparse.Namespace(
        store=store_path,
        format=fmt,
        method=method,
        status=status,
    )
    return args


class TestCLIDigest:
    def test_text_output_shows_digest(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record()])
        cmd_digest(_run_digest(p))
        out = capsys.readouterr().out
        assert "Digest" in out

    def test_text_output_shows_total(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record(), _make_record("POST")])
        cmd_digest(_run_digest(p))
        out = capsys.readouterr().out
        assert "total=2" in out

    def test_json_output_has_digest_key(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record()])
        cmd_digest(_run_digest(p, fmt="json"))
        data = json.loads(capsys.readouterr().out)
        assert "digest" in data
        assert len(data["digest"]) == 64

    def test_json_output_has_method_counts(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record("GET"), _make_record("POST")])
        cmd_digest(_run_digest(p, fmt="json"))
        data = json.loads(capsys.readouterr().out)
        assert data["method_counts"]["GET"] == 1
        assert data["method_counts"]["POST"] == 1

    def test_method_filter_reduces_total(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record("GET"), _make_record("POST"), _make_record("GET")])
        cmd_digest(_run_digest(p, fmt="json", method="GET"))
        data = json.loads(capsys.readouterr().out)
        assert data["total"] == 2

    def test_missing_store_exits(self, tmp_path):
        p = str(tmp_path / "missing.json")
        with pytest.raises(SystemExit):
            cmd_digest(_run_digest(p))
