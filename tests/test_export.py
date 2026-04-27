"""Tests for reqwatch.export module."""

import csv
import io
import json

import pytest
from reqwatch.core import RequestRecord
from reqwatch.export import to_csv, to_curl, to_json


def _make_record(
    method: str = "GET",
    url: str = "http://example.com/api/items",
    status_code: int = 200,
    request_body: str | None = None,
    response_body: bytes = b'{"items": []}',
) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={"Accept": "application/json"},
        request_body=request_body,
        status_code=status_code,
        response_headers={"Content-Type": "application/json"},
        response_body=response_body,
        elapsed_ms=55.0,
    )


class TestToJson:
    def test_returns_valid_json(self):
        records = [_make_record(), _make_record(method="POST", status_code=201)]
        output = to_json(records)
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_fields_present(self):
        record = _make_record()
        parsed = json.loads(to_json([record]))
        assert parsed[0]["method"] == "GET"
        assert parsed[0]["url"] == "http://example.com/api/items"
        assert parsed[0]["status_code"] == 200

    def test_empty_list(self):
        assert json.loads(to_json([])) == []


class TestToCsv:
    def test_header_row_present(self):
        output = to_csv([_make_record()])
        reader = csv.DictReader(io.StringIO(output))
        assert "method" in reader.fieldnames
        assert "url" in reader.fieldnames
        assert "status_code" in reader.fieldnames

    def test_row_values(self):
        output = to_csv([_make_record()])
        rows = list(csv.DictReader(io.StringIO(output)))
        assert len(rows) == 1
        assert rows[0]["method"] == "GET"
        assert rows[0]["status_code"] == "200"

    def test_multiple_records(self):
        records = [_make_record(), _make_record(method="DELETE", status_code=204)]
        rows = list(csv.DictReader(io.StringIO(to_csv(records))))
        assert len(rows) == 2


class TestToCurl:
    def test_basic_get(self):
        output = to_curl([_make_record()])
        assert "curl -X GET" in output
        assert "http://example.com/api/items" in output

    def test_includes_headers(self):
        output = to_curl([_make_record()])
        assert "-H 'Accept: application/json'" in output

    def test_post_with_body(self):
        record = _make_record(method="POST", request_body='{"name": "test"}')
        output = to_curl([record])
        assert "--data" in output
        assert "name" in output

    def test_multiple_records_separated(self):
        records = [_make_record(), _make_record(method="POST", status_code=201)]
        output = to_curl(records)
        assert output.count("curl -X") == 2
