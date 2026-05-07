"""Tests for reqwatch.label."""

import pytest

from reqwatch.core import RequestRecord
from reqwatch.label import (
    add_label,
    filter_by_label,
    get_labels,
    label_summary,
    remove_label,
)


def _make_record(method="GET", url="http://example.com/", status=200, metadata=None):
    return RequestRecord(
        id="abc",
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
        metadata=metadata or {},
    )


class TestAddLabel:
    def test_adds_label_to_empty_metadata(self):
        r = _make_record()
        r2 = add_label(r, "env", "prod")
        assert get_labels(r2) == {"env": "prod"}

    def test_does_not_mutate_original(self):
        r = _make_record()
        add_label(r, "env", "prod")
        assert get_labels(r) == {}

    def test_overwrites_existing_key(self):
        r = _make_record(metadata={"labels": {"env": "staging"}})
        r2 = add_label(r, "env", "prod")
        assert get_labels(r2)["env"] == "prod"

    def test_preserves_other_labels(self):
        r = _make_record(metadata={"labels": {"team": "backend"}})
        r2 = add_label(r, "env", "prod")
        assert get_labels(r2)["team"] == "backend"

    def test_preserves_other_metadata_keys(self):
        r = _make_record(metadata={"tags": ["important"]})
        r2 = add_label(r, "env", "prod")
        assert r2.metadata["tags"] == ["important"]


class TestRemoveLabel:
    def test_removes_existing_label(self):
        r = _make_record(metadata={"labels": {"env": "prod"}})
        r2 = remove_label(r, "env")
        assert "env" not in get_labels(r2)

    def test_noop_when_key_absent(self):
        r = _make_record()
        r2 = remove_label(r, "env")
        assert get_labels(r2) == {}

    def test_does_not_mutate_original(self):
        r = _make_record(metadata={"labels": {"env": "prod"}})
        remove_label(r, "env")
        assert get_labels(r) == {"env": "prod"}


class TestFilterByLabel:
    def test_returns_records_with_key(self):
        r1 = add_label(_make_record(), "env", "prod")
        r2 = _make_record(url="http://example.com/other")
        result = filter_by_label([r1, r2], "env")
        assert result == [r1]

    def test_filters_by_key_and_value(self):
        r1 = add_label(_make_record(), "env", "prod")
        r2 = add_label(_make_record(url="http://example.com/b"), "env", "staging")
        result = filter_by_label([r1, r2], "env", "prod")
        assert result == [r1]

    def test_empty_list_returns_empty(self):
        assert filter_by_label([], "env") == []

    def test_no_match_returns_empty(self):
        r = _make_record()
        assert filter_by_label([r], "env") == []


class TestLabelSummary:
    def test_no_labels_returns_none_message(self):
        r = _make_record()
        assert label_summary([r]) == "labels: none"

    def test_summary_contains_key_value(self):
        r = add_label(_make_record(), "env", "prod")
        out = label_summary([r])
        assert "env=prod" in out

    def test_summary_shows_counts(self):
        r1 = add_label(_make_record(), "env", "prod")
        r2 = add_label(_make_record(url="http://example.com/b"), "env", "prod")
        out = label_summary([r1, r2])
        assert "2" in out
