"""Tests for the 'stats' subcommand in reqwatch CLI."""

import json
import os
import tempfile

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli import build_parser, cmd_stats


def _make_record(method="GET", url="http://example.com", status=200):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body="",
        response_status=status,
        response_headers={},
        response_body="",
    )


def _write_store(records, path):
    store = RequestStore(records=records)
    store.save(path)


class TestCLIStats:
    def _run_stats(self, records, extra_args=None, capsys=None):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            _write_store(records, tmp_path)
            parser = build_parser()
            argv = ["stats", tmp_path] + (extra_args or [])
            args = parser.parse_args(argv)
            cmd_stats(args)
        finally:
            os.unlink(tmp_path)

    def test_stats_prints_total(self, capsys):
        records = [_make_record() for _ in range(3)]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            _write_store(records, tmp_path)
            parser = build_parser()
            args = parser.parse_args(["stats", tmp_path])
            cmd_stats(args)
            captured = capsys.readouterr()
            assert "3" in captured.out
        finally:
            os.unlink(tmp_path)

    def test_stats_json_output(self, capsys):
        records = [_make_record(status=200), _make_record(status=404)]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            _write_store(records, tmp_path)
            parser = build_parser()
            args = parser.parse_args(["stats", tmp_path, "--json"])
            cmd_stats(args)
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["total"] == 2
            assert data["success_count"] == 1
            assert data["error_count"] == 1
        finally:
            os.unlink(tmp_path)

    def test_stats_json_by_method(self, capsys):
        records = [_make_record(method="GET"), _make_record(method="POST")]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            _write_store(records, tmp_path)
            parser = build_parser()
            args = parser.parse_args(["stats", tmp_path, "--json"])
            cmd_stats(args)
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["by_method"]["GET"] == 1
            assert data["by_method"]["POST"] == 1
        finally:
            os.unlink(tmp_path)

    def test_stats_empty_store(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            _write_store([], tmp_path)
            parser = build_parser()
            args = parser.parse_args(["stats", tmp_path])
            cmd_stats(args)
            captured = capsys.readouterr()
            assert "0" in captured.out
        finally:
            os.unlink(tmp_path)
