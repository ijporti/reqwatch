"""Tests for reqwatch.cli_label."""

import json
import os
import tempfile

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.cli_label import cmd_label
from reqwatch.label import add_label


def _make_record(method="GET", url="http://example.com/", status=200):
    return RequestRecord(
        id="id1",
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
        metadata={},
    )


def _write_store(path, records):
    store = RequestStore(path)
    store.records = records
    store.save()


class _Args:
    def __init__(self, **kwargs):
        defaults = {"action": "summary", "label": "", "key": "", "format": "text"}
        defaults.update(kwargs)
        self.__dict__.update(defaults)


class TestCLILabel:
    def test_summary_text_output(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        r = add_label(_make_record(), "env", "prod")
        _write_store(p, [r])
        cmd_label(_Args(store=p, action="summary", format="text"))
        out = capsys.readouterr().out
        assert "env=prod" in out

    def test_summary_json_output(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        r = add_label(_make_record(), "env", "prod")
        _write_store(p, [r])
        cmd_label(_Args(store=p, action="summary", format="json"))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "summary" in data

    def test_add_label_persists(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record()])
        cmd_label(_Args(store=p, action="add", label="env=prod", format="text"))
        store = RequestStore(p)
        store.load()
        labels = (store.records[0].metadata or {}).get("labels", {})
        assert labels.get("env") == "prod"

    def test_add_label_text_confirms(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record()])
        cmd_label(_Args(store=p, action="add", label="env=prod", format="text"))
        out = capsys.readouterr().out
        assert "env=prod" in out

    def test_remove_label_text_confirms(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        r = add_label(_make_record(), "env", "prod")
        _write_store(p, [r])
        cmd_label(_Args(store=p, action="remove", key="env", format="text"))
        out = capsys.readouterr().out
        assert "env" in out

    def test_filter_prints_matching_records(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        r1 = add_label(_make_record(), "env", "prod")
        r2 = _make_record(url="http://example.com/other")
        _write_store(p, [r1, r2])
        cmd_label(_Args(store=p, action="filter", label="env=prod", format="text"))
        out = capsys.readouterr().out
        assert "example.com" in out

    def test_filter_no_match_message(self, capsys, tmp_path):
        p = str(tmp_path / "store.json")
        _write_store(p, [_make_record()])
        cmd_label(_Args(store=p, action="filter", label="env=prod", format="text"))
        out = capsys.readouterr().out
        assert "No records" in out
