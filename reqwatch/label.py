"""Label records with key-value pairs for categorisation and filtering."""

from __future__ import annotations

from typing import Dict, List, Optional

from reqwatch.core import RequestRecord


def add_label(record: RequestRecord, key: str, value: str) -> RequestRecord:
    """Return a copy of *record* with the label *key*=*value* added."""
    meta = dict(record.metadata or {})
    labels: Dict[str, str] = dict(meta.get("labels", {}))
    labels[key] = value
    meta["labels"] = labels
    return RequestRecord(
        id=record.id,
        method=record.method,
        url=record.url,
        request_headers=record.request_headers,
        request_body=record.request_body,
        response_status=record.response_status,
        response_headers=record.response_headers,
        response_body=record.response_body,
        timestamp=record.timestamp,
        metadata=meta,
    )


def remove_label(record: RequestRecord, key: str) -> RequestRecord:
    """Return a copy of *record* with label *key* removed (no-op if absent)."""
    meta = dict(record.metadata or {})
    labels: Dict[str, str] = dict(meta.get("labels", {}))
    labels.pop(key, None)
    meta["labels"] = labels
    return RequestRecord(
        id=record.id,
        method=record.method,
        url=record.url,
        request_headers=record.request_headers,
        request_body=record.request_body,
        response_status=record.response_status,
        response_headers=record.response_headers,
        response_body=record.response_body,
        timestamp=record.timestamp,
        metadata=meta,
    )


def get_labels(record: RequestRecord) -> Dict[str, str]:
    """Return the labels dict attached to *record* (empty dict if none)."""
    return dict((record.metadata or {}).get("labels", {}))


def filter_by_label(
    records: List[RequestRecord],
    key: str,
    value: Optional[str] = None,
) -> List[RequestRecord]:
    """Return records that have label *key*, optionally matching *value*."""
    out = []
    for r in records:
        labels = get_labels(r)
        if key in labels:
            if value is None or labels[key] == value:
                out.append(r)
    return out


def label_summary(records: List[RequestRecord]) -> str:
    """Return a human-readable summary of label usage across *records*."""
    counts: Dict[str, Dict[str, int]] = {}
    for r in records:
        for k, v in get_labels(r).items():
            counts.setdefault(k, {})
            counts[k][v] = counts[k].get(v, 0) + 1
    if not counts:
        return "labels: none"
    lines = ["labels:"]
    for key in sorted(counts):
        for val in sorted(counts[key]):
            lines.append(f"  {key}={val}: {counts[key][val]}")
    return "\n".join(lines)
