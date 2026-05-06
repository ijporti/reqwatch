"""CLI integration tests for archive/restore commands."""

import gzip
import json
import os
import tempfile
from datetime import datetime, timezone
from io import StringIO
from unittest import mock

import pytest

from reqwatch.cli_archive import cmd_archive, cmd_restore
from reqwatch.core import RequestRecord, to_dict


def _make_record(method="GET", url="http://example.com/", status=200) -> RequestRecord:
    return RequestRecord(
        id="id1",
        timestamp=datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        metadata={},
    )


def _write_store(path: str, records) -> None:
    with open(path, "w") as fh:
        json.dump([to_dict(r) for r in records], fh)


class TestCLIArchive:
    def test_archive_creates_gz_file(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "store.json")
            archive_path = os.path.join(tmpdir, "out.gz")
            _write_store(store_path, [_make_record()])

            args = mock.Namespace(
                store=store_path, output=archive_path, format="text"
            )
            cmd_archive(args)
            assert os.path.exists(archive_path)

    def test_archive_text_output_mentions_record_count(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "store.json")
            archive_path = os.path.join(tmpdir, "out.gz")
            _write_store(store_path, [_make_record(), _make_record(method="POST")])

            args = mock.Namespace(
                store=store_path, output=archive_path, format="text"
            )
            cmd_archive(args)
            out = capsys.readouterr().out
            assert "2" in out

    def test_archive_json_output_has_keys(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "store.json")
            archive_path = os.path.join(tmpdir, "out.gz")
            _write_store(store_path, [_make_record()])

            args = mock.Namespace(
                store=store_path, output=archive_path, format="json"
            )
            cmd_archive(args)
            data = json.loads(capsys.readouterr().out)
            assert "record_count" in data
            assert "size_bytes" in data
            assert data["succeeded"] is True

    def test_restore_text_output_lists_records(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "store.json")
            archive_path = os.path.join(tmpdir, "out.gz")
            _write_store(store_path, [_make_record(url="http://api.local/ping")])

            arch_args = mock.Namespace(
                store=store_path, output=archive_path, format="text"
            )
            cmd_archive(arch_args)

            rest_args = mock.Namespace(input=archive_path, format="text")
            cmd_restore(rest_args)
            out = capsys.readouterr().out
            assert "http://api.local/ping" in out

    def test_restore_json_output_is_list(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = os.path.join(tmpdir, "store.json")
            archive_path = os.path.join(tmpdir, "out.gz")
            _write_store(store_path, [_make_record()])

            arch_args = mock.Namespace(
                store=store_path, output=archive_path, format="text"
            )
            cmd_archive(arch_args)

            rest_args = mock.Namespace(input=archive_path, format="json")
            cmd_restore(rest_args)
            data = json.loads(capsys.readouterr().out)
            assert isinstance(data, list)
            assert len(data) == 1
