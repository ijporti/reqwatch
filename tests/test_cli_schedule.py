"""Tests for reqwatch.cli_schedule."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_schedule import cmd_schedule, build_schedule_parser
from reqwatch.schedule import ScheduleResult
from reqwatch.replay import ReplayResult


def _make_record(method: str = "GET", url: str = "http://example.com") -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00Z",
        metadata={},
    )


def _write_store(records, path):
    store = RequestStore()
    for r in records:
        store.add(r)
    store.save(path)


def _make_args(
    store_path,
    runs=1,
    interval=0.0,
    dry_run=True,
    fmt="text",
):
    return argparse.Namespace(
        store=store_path,
        runs=runs,
        interval=interval,
        dry_run=dry_run,
        format=fmt,
    )


class TestCLISchedule:
    def test_text_output_shows_summary(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store([_make_record()], p)
        cmd_schedule(_make_args(p))
        out = capsys.readouterr().out
        assert "run" in out.lower()

    def test_json_output_has_keys(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store([_make_record()], p)
        cmd_schedule(_make_args(p, fmt="json"))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "runs" in data
        assert "total_requests" in data
        assert "succeeded" in data
        assert "failed" in data

    def test_multiple_runs_reflected_in_json(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store([_make_record(), _make_record(method="POST")], p)
        cmd_schedule(_make_args(p, runs=3, fmt="json"))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["runs"] == 3
        assert data["total_requests"] == 6

    def test_missing_store_exits(self, tmp_path):
        args = _make_args(str(tmp_path / "missing.json"))
        with pytest.raises(SystemExit):
            cmd_schedule(args)

    def test_build_schedule_parser_registers_command(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_schedule_parser(sub)
        # Should not raise
