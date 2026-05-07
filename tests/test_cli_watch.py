"""Tests for reqwatch.cli_watch."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

import pytest

from reqwatch.core import RequestRecord
from reqwatch.cli_watch import cmd_watch, build_watch_parser
from reqwatch.watch import WatchResult


def _make_record(record_id: str = "r1") -> RequestRecord:
    return RequestRecord(
        id=record_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        method="GET",
        url="http://example.com/test",
        request_headers={},
        request_body=None,
        status_code=200,
        response_headers={},
        response_body=None,
        duration_ms=5.0,
        metadata={},
    )


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "store": "store.json",
        "format": "text",
        "poll": 0.5,
        "timeout": None,
        "max_records": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCLIWatch:
    def test_text_output_shows_summary(self, capsys):
        record = _make_record()
        captured = []

        def fake_watch(path, on_record, poll_interval, max_records, timeout):
            on_record(record)
            captured.append(record)
            return WatchResult(seen=1)

        with patch("reqwatch.cli_watch.watch_store", side_effect=fake_watch):
            cmd_watch(_make_args())

        out, err = capsys.readouterr()
        assert "1" in err  # summary mentions count

    def test_json_output_is_valid(self, capsys):
        record = _make_record()

        def fake_watch(path, on_record, poll_interval, max_records, timeout):
            on_record(record)
            return WatchResult(seen=1)

        with patch("reqwatch.cli_watch.watch_store", side_effect=fake_watch):
            cmd_watch(_make_args(format="json"))

        out, _ = capsys.readouterr()
        parsed = json.loads(out.strip())
        assert parsed["id"] == "r1"

    def test_keyboard_interrupt_handled_gracefully(self, capsys):
        def fake_watch(**kwargs):
            raise KeyboardInterrupt

        with patch("reqwatch.cli_watch.watch_store", side_effect=fake_watch):
            cmd_watch(_make_args())  # should not raise

        _, err = capsys.readouterr()
        assert "Interrupted" in err

    def test_build_watch_parser_registers_subcommand(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_watch_parser(sub)
        args = parser.parse_args(["watch", "mystore.json", "--format", "json"])
        assert args.store == "mystore.json"
        assert args.format == "json"
