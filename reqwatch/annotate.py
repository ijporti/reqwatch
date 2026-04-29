"""Annotation support for RequestRecord — attach free-form notes to records."""

from __future__ import annotations

from typing import List

from reqwatch.core import RequestRecord

_ANNOTATIONS_KEY = "annotations"


def add_annotation(record: RequestRecord, note: str) -> RequestRecord:
    """Append *note* to the record's annotation list (idempotent for duplicates)."""
    meta = dict(record.metadata or {})
    notes: List[str] = list(meta.get(_ANNOTATIONS_KEY, []))
    if note not in notes:
        notes.append(note)
    meta[_ANNOTATIONS_KEY] = notes
    record.metadata = meta
    return record


def remove_annotation(record: RequestRecord, note: str) -> RequestRecord:
    """Remove *note* from the record's annotation list if present."""
    meta = dict(record.metadata or {})
    notes: List[str] = list(meta.get(_ANNOTATIONS_KEY, []))
    notes = [n for n in notes if n != note]
    meta[_ANNOTATIONS_KEY] = notes
    record.metadata = meta
    return record


def get_annotations(record: RequestRecord) -> List[str]:
    """Return the list of annotations attached to *record*."""
    return list((record.metadata or {}).get(_ANNOTATIONS_KEY, []))


def filter_by_annotation(records: List[RequestRecord], note: str) -> List[RequestRecord]:
    """Return records that contain *note* in their annotation list."""
    return [r for r in records if note in get_annotations(r)]


def annotation_summary(record: RequestRecord) -> str:
    """Return a human-readable summary of annotations on *record*."""
    notes = get_annotations(record)
    if not notes:
        return "No annotations."
    lines = [f"  [{i + 1}] {n}" for i, n in enumerate(notes)]
    return "Annotations:\n" + "\n".join(lines)
