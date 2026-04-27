"""Tests for reqwatch CLI commands."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli import cmd_replay, cmd_list, build_parser
from reqwatch.replay import ReplayResult


def _write_store(records: list) -> str:
    store = RequestStore()
    for r in records:
        store.add(r)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
    store.save(tmp.name)
    tmp.close()
    return tmp.name


def _make_record(uid="id-1", url="http://example.com/test") -> RequestRecord:
    return RequestRecord(
        id=uid,
        method="GET",
        url=url,
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
    )


class TestCLIList(unittest.TestCase):
    def test_list_prints_records(self):
        path = _write_store([_make_record()])
        try:
            args = build_parser().parse_args(["list", path])
            ret = cmd_list(args)
            self.assertEqual(ret, 0)
        finally:
            os.unlink(path)

    def test_list_empty_store(self, capsys=None):
        path = _write_store([])
        try:
            args = build_parser().parse_args(["list", path])
            ret = cmd_list(args)
            self.assertEqual(ret, 0)
        finally:
            os.unlink(path)


class TestCLIReplay(unittest.TestCase):
    def _make_success_result(self, record):
        return ReplayResult(record=record, status_code=200, elapsed_ms=10.0)

    @patch("reqwatch.cli.replay_all")
    def test_replay_all_success(self, mock_replay_all):
        rec = _make_record()
        mock_replay_all.return_value = [self._make_success_result(rec)]
        path = _write_store([rec])
        try:
            args = build_parser().parse_args(["replay", path])
            ret = cmd_replay(args)
            self.assertEqual(ret, 0)
        finally:
            os.unlink(path)

    @patch("reqwatch.cli.replay_all")
    def test_replay_failure_returns_nonzero(self, mock_replay_all):
        rec = _make_record()
        mock_replay_all.return_value = [
            ReplayResult(record=rec, error="connection refused")
        ]
        path = _write_store([rec])
        try:
            args = build_parser().parse_args(["replay", path])
            ret = cmd_replay(args)
            self.assertNotEqual(ret, 0)
        finally:
            os.unlink(path)

    @patch("reqwatch.cli.replay_request")
    def test_replay_single_by_id(self, mock_replay_request):
        rec = _make_record(uid="abc-123")
        mock_replay_request.return_value = self._make_success_result(rec)
        path = _write_store([rec])
        try:
            args = build_parser().parse_args(["replay", path, "--id", "abc-123"])
            ret = cmd_replay(args)
            self.assertEqual(ret, 0)
            mock_replay_request.assert_called_once()
        finally:
            os.unlink(path)

    def test_replay_unknown_id_returns_error(self):
        path = _write_store([_make_record()])
        try:
            args = build_parser().parse_args(["replay", path, "--id", "nonexistent"])
            ret = cmd_replay(args)
            self.assertEqual(ret, 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
