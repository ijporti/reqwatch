"""Tests for reqwatch.cli_compare module."""

import json
import os
import tempfile
from io import StringIO
from unittest import mock

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_compare import cmd_compare, build_compare_parser


def _make_record(method="GET", url="http://example.com/api", status_code=200):
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body="",
        response_status=status_code,
        response_headers={},
        response_body="ok",
        timestamp="2024-01-01T00:00:00",
        duration_ms=5.0,
    )


def _write_store(path, records):
    store = RequestStore(path)
    for r in records:
        store.save(r)


class TestCLICompare:
    def _run_compare(self, baseline_records, current_records, extra_args=None):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            baseline_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            current_path = f.name
        try:
            _write_store(baseline_path, baseline_records)
            _write_store(current_path, current_records)
            args = mock.Namespace(
                baseline=baseline_path,
                current=current_path,
                format="text",
                verbose=False,
            )
            if extra_args:
                for k, v in extra_args.items():
                    setattr(args, k, v)
            with mock.patch("sys.stdout", new_callable=StringIO) as mock_out:
                cmd_compare(args)
                return mock_out.getvalue()
        finally:
            os.unlink(baseline_path)
            os.unlink(current_path)

    def test_summary_shown_in_text_mode(self):
        rec = _make_record()
        output = self._run_compare([rec], [rec])
        assert "Added" in output
        assert "Removed" in output
        assert "Unchanged" in output

    def test_added_count_reflected(self):
        new_rec = _make_record(url="http://example.com/new")
        output = self._run_compare([], [new_rec])
        assert "Added:     1" in output

    def test_removed_count_reflected(self):
        old_rec = _make_record(url="http://example.com/old")
        output = self._run_compare([old_rec], [])
        assert "Removed:   1" in output

    def test_verbose_shows_added_details(self):
        new_rec = _make_record(url="http://example.com/added")
        output = self._run_compare([], [new_rec], extra_args={"verbose": True})
        assert "+" in output
        assert "http://example.com/added" in output

    def test_json_format_output(self):
        rec = _make_record()
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            baseline_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            current_path = f.name
        try:
            _write_store(baseline_path, [rec])
            _write_store(current_path, [])
            args = mock.Namespace(
                baseline=baseline_path,
                current=current_path,
                format="json",
                verbose=False,
            )
            with mock.patch("sys.stdout", new_callable=StringIO) as mock_out:
                cmd_compare(args)
                data = json.loads(mock_out.getvalue())
            assert "added" in data
            assert "removed" in data
            assert "changed" in data
        finally:
            os.unlink(baseline_path)
            os.unlink(current_path)
