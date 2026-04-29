"""Tests for reqwatch.annotate."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.annotate import (
    add_annotation,
    remove_annotation,
    get_annotations,
    filter_by_annotation,
    annotation_summary,
)


def _make_record(url: str = "http://example.com", metadata: dict | None = None) -> RequestRecord:
    return RequestRecord(
        method="GET",
        url=url,
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body=None,
        timestamp="2024-01-01T00:00:00",
        metadata=metadata or {},
    )


class TestAddAnnotation:
    def test_adds_note_to_empty_metadata(self):
        r = _make_record()
        add_annotation(r, "needs review")
        assert "needs review" in get_annotations(r)

    def test_does_not_duplicate_existing_note(self):
        r = _make_record()
        add_annotation(r, "important")
        add_annotation(r, "important")
        assert get_annotations(r).count("important") == 1

    def test_preserves_other_metadata(self):
        r = _make_record(metadata={"tag": "slow"})
        add_annotation(r, "check this")
        assert r.metadata["tag"] == "slow"

    def test_multiple_distinct_notes(self):
        r = _make_record()
        add_annotation(r, "alpha")
        add_annotation(r, "beta")
        notes = get_annotations(r)
        assert "alpha" in notes
        assert "beta" in notes
        assert len(notes) == 2


class TestRemoveAnnotation:
    def test_removes_existing_note(self):
        r = _make_record()
        add_annotation(r, "to remove")
        remove_annotation(r, "to remove")
        assert "to remove" not in get_annotations(r)

    def test_no_error_when_note_absent(self):
        r = _make_record()
        remove_annotation(r, "ghost")  # should not raise
        assert get_annotations(r) == []

    def test_leaves_other_notes_intact(self):
        r = _make_record()
        add_annotation(r, "keep")
        add_annotation(r, "drop")
        remove_annotation(r, "drop")
        assert get_annotations(r) == ["keep"]


class TestFilterByAnnotation:
    def test_returns_matching_records(self):
        r1 = _make_record(url="http://a.com")
        r2 = _make_record(url="http://b.com")
        add_annotation(r1, "critical")
        result = filter_by_annotation([r1, r2], "critical")
        assert result == [r1]

    def test_empty_list_returns_empty(self):
        assert filter_by_annotation([], "any") == []

    def test_no_match_returns_empty(self):
        r = _make_record()
        assert filter_by_annotation([r], "missing") == []


class TestAnnotationSummary:
    def test_no_annotations_message(self):
        r = _make_record()
        assert annotation_summary(r) == "No annotations."

    def test_lists_notes_with_index(self):
        r = _make_record()
        add_annotation(r, "first")
        add_annotation(r, "second")
        summary = annotation_summary(r)
        assert "[1] first" in summary
        assert "[2] second" in summary
