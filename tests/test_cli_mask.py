"""Integration tests for the CLI mask command."""

from __future__ import annotations

import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_mask import cmd_mask, build_mask_parser
import argparse


def _make_record(id: str = "r1", **kwargs) -> RequestRecord:
    defaults = dict(
        id=id,
        timestamp="2024-06-01T12:00:00",
        method="POST",
        url="https://api.example.com/login",
        request_headers={"Authorization": "Bearer tok", "Content-Type": "application/json"},
        request_body='{"password": "hunter2"}',
        status_code=200,
        response_headers={"Set-Cookie": "session=xyz", "Content-Type": "application/json"},
        response_body='{"token": "secret-jwt"}',
        duration_ms=55.0,
        metadata={},
    )
    defaults.update(kwargs)
    return RequestRecord(**defaults)


def _write_store(records: list[RequestRecord]) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = RequestStore()
    for r in records:
        store.add(r)
    store.save(path)
    return path


def _run_mask(store_path: str, extra_args: list[str] | None = None) -> str:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    build_mask_parser(subs)
    args = parser.parse_args(["mask", store_path] + (extra_args or []))
    buf = StringIO()
    with patch("sys.stdout", buf):
        args.func(args)
    return buf.getvalue()


class TestCLIMask:
    def test_text_output_lists_records(self):
        path = _write_store([_make_record()])
        out = _run_mask(path)
        assert "r1" in out

    def test_empty_store_prints_message(self):
        path = _write_store([])
        out = _run_mask(path)
        assert "No records" in out

    def test_verbose_shows_summary(self):
        path = _write_store([_make_record()])
        out = _run_mask(path, ["--verbose"])
        assert "r1" in out

    def test_json_format_output(self):
        path = _write_store([_make_record()])
        out = _run_mask(path, ["--format", "json"])
        parsed = json.loads(out)
        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_authorization_header_masked_in_output_store(self):
        path = _write_store([_make_record()])
        fd, out_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            _run_mask(path, ["--output", out_path])
            loaded = RequestStore.load(out_path)
            rec = loaded.all()[0]
            assert rec.request_headers.get("Authorization") == "***"
        finally:
            os.unlink(out_path)

    def test_custom_mask_string_used(self):
        path = _write_store([_make_record()])
        fd, out_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            _run_mask(path, ["--mask", "[HIDDEN]", "--output", out_path])
            loaded = RequestStore.load(out_path)
            rec = loaded.all()[0]
            assert rec.request_headers.get("Authorization") == "[HIDDEN]"
        finally:
            os.unlink(out_path)

    def test_body_pattern_masked_in_output_store(self):
        path = _write_store([_make_record()])
        fd, out_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            _run_mask(path, ["--body-pattern", r'"hunter2"', "--output", out_path])
            loaded = RequestStore.load(out_path)
            rec = loaded.all()[0]
            assert "hunter2" not in rec.request_body
        finally:
            os.unlink(out_path)
