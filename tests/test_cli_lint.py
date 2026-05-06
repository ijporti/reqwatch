"""Tests for reqwatch.cli_lint."""

import json
import os
import tempfile
import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_lint import cmd_lint, build_lint_parser
import argparse


def _make_record(
    method="GET",
    url="http://example.com/api",
    request_headers=None,
    response_status=200,
):
    return RequestRecord(
        method=method,
        url=url,
        request_headers=request_headers or {"Authorization": "Bearer tok"},
        request_body=None,
        response_status=response_status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
        duration_ms=10,
        metadata={},
    )


def _write_store(records, path):
    store = RequestStore(records=records)
    store.save(path)


def _run_lint(tmp_path, records, extra_args=None):
    store_path = str(tmp_path / "store.json")
    _write_store(records, store_path)
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    build_lint_parser(subs)
    args_list = ["lint", store_path] + (extra_args or [])
    args = parser.parse_args(args_list)
    return args, store_path


class TestCLILint:
    def test_text_output_shows_ok(self, tmp_path, capsys):
        records = [_make_record()]
        args, _ = _run_lint(tmp_path, records)
        cmd_lint(args)
        out = capsys.readouterr().out
        assert "OK" in out

    def test_text_output_shows_summary(self, tmp_path, capsys):
        records = [_make_record(), _make_record()]
        args, _ = _run_lint(tmp_path, records)
        cmd_lint(args)
        out = capsys.readouterr().out
        assert "Linted 2" in out

    def test_json_output_has_keys(self, tmp_path, capsys):
        records = [_make_record()]
        args, _ = _run_lint(tmp_path, records, extra_args=["--format", "json"])
        cmd_lint(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert "is_clean" in data[0]
        assert "warnings" in data[0]

    def test_only_warnings_filters_clean(self, tmp_path, capsys):
        records = [
            _make_record(response_status=200),
            _make_record(response_status=500),
        ]
        args, _ = _run_lint(tmp_path, records, extra_args=["--only-warnings"])
        cmd_lint(args)
        out = capsys.readouterr().out
        assert "500" in out
        # Clean record (200) should not produce a WARN line
        lines = [l for l in out.splitlines() if l.startswith("OK")]
        assert len(lines) == 0

    def test_fail_on_warnings_exits_nonzero(self, tmp_path):
        records = [_make_record(response_status=500)]
        args, _ = _run_lint(tmp_path, records, extra_args=["--fail-on-warnings"])
        with pytest.raises(SystemExit) as exc_info:
            cmd_lint(args)
        assert exc_info.value.code == 1

    def test_no_fail_when_all_clean(self, tmp_path):
        records = [_make_record(response_status=200)]
        args, _ = _run_lint(
            tmp_path, records,
            extra_args=["--fail-on-warnings", "--rules", "large_body"]
        )
        # Should not raise SystemExit
        cmd_lint(args)
