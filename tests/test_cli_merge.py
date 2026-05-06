"""Tests for reqwatch.cli_merge."""

import json
import os
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_merge import cmd_merge, build_merge_parser
import argparse


def _make_record(method="GET", url="http://example.com/", status=200):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body="ok",
        timestamp="2024-01-01T00:00:00",
    )


def _write_store(path, *records):
    store = RequestStore()
    for r in records:
        store.add(r)
    store.save(path)


def _run_merge(base_path, other_path, extra_args=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_merge_parser(sub)
    argv = ["merge", base_path, other_path] + (extra_args or [])
    args = parser.parse_args(argv)
    buf = StringIO()
    with patch("sys.stdout", buf):
        args.func(args)
    return buf.getvalue()


class TestCLIMerge:
    def test_text_output_shows_summary(self, tmp_path):
        base = str(tmp_path / "base.json")
        other = str(tmp_path / "other.json")
        _write_store(base, _make_record(url="http://a.com/"))
        _write_store(other, _make_record(url="http://b.com/"))
        out = _run_merge(base, other)
        assert "2" in out

    def test_json_output_has_keys(self, tmp_path):
        base = str(tmp_path / "base.json")
        other = str(tmp_path / "other.json")
        _write_store(base, _make_record())
        _write_store(other, _make_record())
        out = _run_merge(base, other, ["--format", "json"])
        data = json.loads(out)
        assert "total_before" in data
        assert "total_after" in data
        assert "duplicates_removed" in data

    def test_output_file_is_written(self, tmp_path):
        base = str(tmp_path / "base.json")
        other = str(tmp_path / "other.json")
        out_path = str(tmp_path / "merged.json")
        _write_store(base, _make_record(url="http://a.com/"))
        _write_store(other, _make_record(url="http://b.com/"))
        _run_merge(base, other, ["-o", out_path])
        assert os.path.exists(out_path)

    def test_missing_base_exits(self, tmp_path):
        other = str(tmp_path / "other.json")
        _write_store(other, _make_record())
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_merge_parser(sub)
        args = parser.parse_args(["merge", "nonexistent.json", other])
        with pytest.raises(SystemExit):
            args.func(args)

    def test_dedupe_flag_reduces_duplicates(self, tmp_path):
        rec = _make_record()
        base = str(tmp_path / "base.json")
        other = str(tmp_path / "other.json")
        _write_store(base, rec)
        _write_store(other, rec)
        out = _run_merge(base, other, ["--dedupe", "--format", "json"])
        data = json.loads(out)
        assert data["duplicates_removed"] >= 1
