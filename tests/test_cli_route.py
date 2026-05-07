"""Tests for reqwatch.cli_route."""

import json
import os
import tempfile
from types import SimpleNamespace

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_route import cmd_route


def _make_record(method: str = "GET", url: str = "http://example.com/") -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
    )


def _write_store(records, tmp_path: str) -> str:
    store = RequestStore()
    for r in records:
        store.add(r)
    path = os.path.join(tmp_path, "store.json")
    store.save(path)
    return path


def _run_route(store_path, routes, fmt="text", capsys=None):
    args = SimpleNamespace(store=store_path, routes=routes, format=fmt)
    cmd_route(args)
    if capsys:
        return capsys.readouterr()
    return None


class TestCLIRoute:
    def test_text_output_shows_summary(self, tmp_path, capsys):
        r = _make_record(url="http://api.local/users/1")
        path = _write_store([r], str(tmp_path))
        out, _ = _run_route(path, ["/users/{id}"], capsys=capsys)
        assert "record" in out

    def test_json_output_is_valid(self, tmp_path, capsys):
        r = _make_record(url="http://api.local/orders/9")
        path = _write_store([r], str(tmp_path))
        out, _ = _run_route(path, ["/orders/{id}"], fmt="json", capsys=capsys)
        data = json.loads(out)
        assert "/orders/{id}" in data

    def test_unmatched_in_json(self, tmp_path, capsys):
        r = _make_record(url="http://api.local/unknown")
        path = _write_store([r], str(tmp_path))
        out, _ = _run_route(path, ["/users/{id}"], fmt="json", capsys=capsys)
        data = json.loads(out)
        assert "<unmatched>" in data
        assert len(data["<unmatched>"]) == 1

    def test_missing_store_exits(self, tmp_path):
        args = SimpleNamespace(
            store=str(tmp_path / "missing.json"),
            routes=["/a"],
            format="text",
        )
        with pytest.raises(SystemExit):
            cmd_route(args)

    def test_no_routes_exits(self, tmp_path):
        r = _make_record()
        path = _write_store([r], str(tmp_path))
        args = SimpleNamespace(store=path, routes=[], format="text")
        with pytest.raises(SystemExit):
            cmd_route(args)
