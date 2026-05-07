"""Integration tests for label round-trip through RequestStore."""

import pytest

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.label import add_label, filter_by_label, get_labels, label_summary


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


class TestLabelRoundtrip:
    def _roundtrip(self, tmp_path, records):
        p = str(tmp_path / "store.json")
        store = RequestStore(p)
        store.records = records
        store.save()
        store2 = RequestStore(p)
        store2.load()
        return store2.records

    def test_label_survives_save_and_load(self, tmp_path):
        r = add_label(_make_record(), "env", "prod")
        loaded = self._roundtrip(tmp_path, [r])
        assert get_labels(loaded[0]).get("env") == "prod"

    def test_multiple_labels_survive_roundtrip(self, tmp_path):
        r = add_label(_make_record(), "env", "prod")
        r = add_label(r, "team", "backend")
        loaded = self._roundtrip(tmp_path, [r])
        labels = get_labels(loaded[0])
        assert labels["env"] == "prod"
        assert labels["team"] == "backend"

    def test_filter_after_roundtrip(self, tmp_path):
        r1 = add_label(_make_record(url="http://a.com/"), "env", "prod")
        r2 = add_label(_make_record(url="http://b.com/"), "env", "staging")
        loaded = self._roundtrip(tmp_path, [r1, r2])
        prod = filter_by_label(loaded, "env", "prod")
        assert len(prod) == 1
        assert prod[0].url == "http://a.com/"

    def test_summary_after_roundtrip(self, tmp_path):
        r1 = add_label(_make_record(url="http://a.com/"), "env", "prod")
        r2 = add_label(_make_record(url="http://b.com/"), "env", "prod")
        loaded = self._roundtrip(tmp_path, [r1, r2])
        out = label_summary(loaded)
        assert "env=prod" in out
        assert "2" in out
