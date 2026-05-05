"""Tests for reqwatch.cli_throttle."""

import json
import os
import tempfile
from argparse import Namespace
from unittest.mock import patch

import pytest

from reqwatch.cli_throttle import _run_throttle, build_throttle_parser, cmd_throttle
from reqwatch.core import RequestRecord, RequestStore


def _make_record(method="GET", url="http://example.com", status=200):
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


def _write_store(path, records):
    store = RequestStore(path)
    for r in records:
        store.add(r)
    store.save()


class TestCLIThrottle:
    def test_text_output_shows_summary(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            _write_store(path, [_make_record() for _ in range(3)])
            with patch("reqwatch.throttle.time.sleep"):
                _run_throttle(path, rps=5.0, burst=10, max_records=0, fmt="text")
            out = capsys.readouterr().out
            assert "5.0 req/s" in out
            assert "dispatched" in out
        finally:
            os.unlink(path)

    def test_json_output_has_keys(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            _write_store(path, [_make_record() for _ in range(2)])
            with patch("reqwatch.throttle.time.sleep"):
                _run_throttle(path, rps=10.0, burst=5, max_records=0, fmt="json")
            out = capsys.readouterr().out
            data = json.loads(out)
            assert "dispatched" in data
            assert "total" in data
            assert "actual_rps" in data
        finally:
            os.unlink(path)

    def test_empty_store_prints_message(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            _write_store(path, [])
            _run_throttle(path, rps=10.0, burst=1, max_records=0, fmt="text")
            out = capsys.readouterr().out
            assert "No records" in out
        finally:
            os.unlink(path)

    def test_max_records_limits_output(self, capsys):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            _write_store(path, [_make_record() for _ in range(8)])
            with patch("reqwatch.throttle.time.sleep"):
                _run_throttle(path, rps=0, burst=10, max_records=3, fmt="json")
            data = json.loads(capsys.readouterr().out)
            assert data["dispatched"] == 3
            assert data["dropped"] == 5
        finally:
            os.unlink(path)

    def test_build_throttle_parser_registers_command(self):
        import argparse
        root = argparse.ArgumentParser()
        sub = root.add_subparsers()
        build_throttle_parser(sub)
        args = root.parse_args(["throttle", "store.json", "--rps", "20", "--burst", "3"])
        assert args.rps == 20.0
        assert args.burst == 3
