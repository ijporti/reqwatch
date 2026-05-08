"""Tests for reqwatch.report."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from argparse import Namespace
from datetime import datetime, timezone

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.report import ReportResult, generate_report
from reqwatch.cli_report import cmd_report


def _make_record(method="GET", url="http://example.com/api", status=200):
    return RequestRecord(
        request_id="id-1",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
    )


class TestReportResult(unittest.TestCase):
    def test_succeeded_when_no_error(self):
        r = ReportResult("T", 0, {}, {}, [], 0.0)
        self.assertTrue(r.succeeded())

    def test_not_succeeded_when_error(self):
        r = ReportResult("T", 0, {}, {}, [], 0.0, error="boom")
        self.assertFalse(r.succeeded())

    def test_summary_contains_title(self):
        r = ReportResult("My Report", 3, {"GET": 3}, {"200": 3}, [], 0.0)
        self.assertIn("My Report", r.summary())

    def test_summary_contains_total(self):
        r = ReportResult("T", 7, {}, {}, [], 0.0)
        self.assertIn("7", r.summary())

    def test_summary_error_message(self):
        r = ReportResult("T", 0, {}, {}, [], 0.0, error="oops")
        self.assertIn("oops", r.summary())

    def test_summary_shows_error_rate(self):
        r = ReportResult("T", 10, {}, {}, [], 0.25)
        self.assertIn("25.0%", r.summary())


class TestGenerateReport(unittest.TestCase):
    def _make_store(self, records):
        store = RequestStore()
        for rec in records:
            store.add(rec)
        return store

    def test_total_matches_record_count(self):
        store = self._make_store([_make_record() for _ in range(4)])
        result = generate_report(store)
        self.assertEqual(result.total, 4)

    def test_method_counts_populated(self):
        store = self._make_store([
            _make_record(method="GET"),
            _make_record(method="POST"),
            _make_record(method="GET"),
        ])
        result = generate_report(store)
        self.assertEqual(result.method_counts.get("GET"), 2)
        self.assertEqual(result.method_counts.get("POST"), 1)

    def test_error_rate_correct(self):
        store = self._make_store([
            _make_record(status=200),
            _make_record(status=500),
            _make_record(status=404),
            _make_record(status=200),
        ])
        result = generate_report(store)
        self.assertAlmostEqual(result.error_rate, 0.5)

    def test_empty_store_zero_error_rate(self):
        store = self._make_store([])
        result = generate_report(store)
        self.assertEqual(result.error_rate, 0.0)

    def test_top_urls_respects_top_n(self):
        records = [
            _make_record(url="http://example.com/a"),
            _make_record(url="http://example.com/a"),
            _make_record(url="http://example.com/b"),
        ]
        store = self._make_store(records)
        result = generate_report(store, top_n=1)
        self.assertEqual(len(result.top_urls), 1)
        self.assertIn("http://example.com/a", result.top_urls)

    def test_custom_title_preserved(self):
        store = self._make_store([])
        result = generate_report(store, title="Custom")
        self.assertEqual(result.title, "Custom")


class TestCLIReport(unittest.TestCase):
    def _write_store(self, records):
        store = RequestStore()
        for rec in records:
            store.add(rec)
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        store.save(f.name)
        return f.name

    def _run(self, path, fmt="text", title="Report"):
        import io
        from unittest.mock import patch
        buf = io.StringIO()
        args = Namespace(store=path, format=fmt, title=title, top=5, func=cmd_report)
        with patch("sys.stdout", buf):
            cmd_report(args)
        return buf.getvalue()

    def test_text_output_contains_total(self):
        path = self._write_store([_make_record() for _ in range(3)])
        try:
            out = self._run(path)
            self.assertIn("3", out)
        finally:
            os.unlink(path)

    def test_json_output_is_valid(self):
        path = self._write_store([_make_record()])
        try:
            out = self._run(path, fmt="json")
            data = json.loads(out)
            self.assertIn("total", data)
            self.assertIn("error_rate", data)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
