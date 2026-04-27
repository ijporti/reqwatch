"""Tests for reqwatch.tag module."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.tag import add_tag, remove_tag, get_tags, filter_by_tag, tag_summary


def _make_record(record_id="r1", method="GET", url="http://example.com/",
                 status=200, metadata=None):
    return RequestRecord(
        id=record_id,
        timestamp="2024-01-01T00:00:00",
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        duration_ms=10.0,
        metadata=metadata or {},
    )


class TestAddTag:
    def test_adds_tag_to_empty_metadata(self):
        r = _make_record()
        r2 = add_tag(r, "slow")
        assert "slow" in get_tags(r2)

    def test_does_not_duplicate_existing_tag(self):
        r = _make_record(metadata={"tags": ["slow"]})
        r2 = add_tag(r, "slow")
        assert get_tags(r2).count("slow") == 1

    def test_preserves_other_metadata(self):
        r = _make_record(metadata={"env": "prod"})
        r2 = add_tag(r, "important")
        assert r2.metadata["env"] == "prod"

    def test_original_record_unchanged(self):
        r = _make_record()
        add_tag(r, "slow")
        assert get_tags(r) == []


class TestRemoveTag:
    def test_removes_existing_tag(self):
        r = _make_record(metadata={"tags": ["slow", "error"]})
        r2 = remove_tag(r, "slow")
        assert "slow" not in get_tags(r2)
        assert "error" in get_tags(r2)

    def test_remove_nonexistent_tag_is_noop(self):
        r = _make_record(metadata={"tags": ["error"]})
        r2 = remove_tag(r, "missing")
        assert get_tags(r2) == ["error"]


class TestFilterByTag:
    def test_returns_only_tagged_records(self):
        r1 = _make_record(record_id="r1", metadata={"tags": ["slow"]})
        r2 = _make_record(record_id="r2", metadata={"tags": ["error"]})
        r3 = _make_record(record_id="r3", metadata={"tags": ["slow", "error"]})
        result = filter_by_tag([r1, r2, r3], "slow")
        ids = [r.id for r in result]
        assert ids == ["r1", "r3"]

    def test_empty_list_returns_empty(self):
        assert filter_by_tag([], "slow") == []

    def test_no_match_returns_empty(self):
        r = _make_record(metadata={"tags": ["error"]})
        assert filter_by_tag([r], "slow") == []


class TestTagSummary:
    def test_counts_tags_correctly(self):
        r1 = _make_record(record_id="r1", metadata={"tags": ["slow", "error"]})
        r2 = _make_record(record_id="r2", metadata={"tags": ["slow"]})
        r3 = _make_record(record_id="r3", metadata={})
        summary = tag_summary([r1, r2, r3])
        assert summary["slow"] == 2
        assert summary["error"] == 1

    def test_empty_records_returns_empty_dict(self):
        assert tag_summary([]) == {}

    def test_record_with_no_tags_ignored(self):
        r = _make_record(metadata={})
        assert tag_summary([r]) == {}
