"""Tests for reqwatch.replay module."""

import json
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.replay import ReplayResult, replay_request, replay_all


def _make_record(
    method="GET",
    url="http://example.com/api/test",
    headers=None,
    body=None,
) -> RequestRecord:
    return RequestRecord(
        id="test-id-1",
        method=method,
        url=url,
        headers=headers or {"Content-Type": "application/json"},
        body=body,
        timestamp="2024-01-01T00:00:00",
    )


class TestReplayResult(unittest.TestCase):
    def test_success_true_when_no_error(self):
        rec = _make_record()
        result = ReplayResult(record=rec, status_code=200, elapsed_ms=42.0)
        self.assertTrue(result.success)

    def test_success_false_when_error(self):
        rec = _make_record()
        result = ReplayResult(record=rec, error="Connection refused")
        self.assertFalse(result.success)

    def test_summary_success(self):
        rec = _make_record()
        result = ReplayResult(record=rec, status_code=200, elapsed_ms=55.5)
        self.assertIn("200", result.summary())
        self.assertIn("GET", result.summary())

    def test_summary_error(self):
        rec = _make_record()
        result = ReplayResult(record=rec, error="timeout")
        self.assertIn("ERROR", result.summary())
        self.assertIn("timeout", result.summary())


class TestReplayRequest(unittest.TestCase):
    def _mock_response(self, status=200, body=b"{}"):
        mock_resp = MagicMock()
        mock_resp.status = status
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    @patch("reqwatch.replay.urllib.request.urlopen")
    def test_successful_replay(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response(200, b'{"ok": true}')
        rec = _make_record()
        result = replay_request(rec)
        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertIsNotNone(result.elapsed_ms)

    @patch("reqwatch.replay.urllib.request.urlopen")
    def test_base_url_override(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response()
        rec = _make_record(url="http://prod.example.com/api/test")
        replay_request(rec, base_url="http://localhost:8080")
        called_url = mock_urlopen.call_args[0][0].full_url
        self.assertIn("localhost:8080", called_url)

    @patch("reqwatch.replay.urllib.request.urlopen", side_effect=Exception("timeout"))
    def test_exception_returns_error_result(self, _):
        rec = _make_record()
        result = replay_request(rec)
        self.assertFalse(result.success)
        self.assertIn("timeout", result.error)


class TestReplayAll(unittest.TestCase):
    @patch("reqwatch.replay.urllib.request.urlopen")
    def test_replay_all_returns_results_for_each_record(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"{}"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        store = RequestStore()
        store.add(_make_record(url="http://example.com/a"))
        store.add(_make_record(url="http://example.com/b"))

        results = replay_all(store)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))


if __name__ == "__main__":
    unittest.main()
