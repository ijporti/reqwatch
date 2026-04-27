"""Utilities for diffing two RequestRecord responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from reqwatch.core import RequestRecord


@dataclass
class DiffResult:
    original: RequestRecord
    replayed: RequestRecord
    status_changed: bool
    body_changed: bool
    headers_changed: bool
    status_diff: Optional[tuple[int, int]]
    missing_headers: list[str]
    added_headers: list[str]

    @property
    def has_diff(self) -> bool:
        return self.status_changed or self.body_changed or self.headers_changed

    def summary(self) -> str:
        if not self.has_diff:
            return "No differences detected."
        parts = []
        if self.status_changed and self.status_diff:
            parts.append(
                f"Status: {self.status_diff[0]} -> {self.status_diff[1]}"
            )
        if self.body_changed:
            parts.append("Body: changed")
        if self.headers_changed:
            if self.missing_headers:
                parts.append(f"Headers missing: {', '.join(self.missing_headers)}")
            if self.added_headers:
                parts.append(f"Headers added: {', '.join(self.added_headers)}")
        return " | ".join(parts)


def _normalize_body(body: Optional[str]) -> str:
    return (body or "").strip()


def _compare_headers(
    original: dict, replayed: dict
) -> tuple[bool, list[str], list[str]]:
    orig_keys = {k.lower() for k in original}
    rep_keys = {k.lower() for k in replayed}
    missing = sorted(orig_keys - rep_keys)
    added = sorted(rep_keys - orig_keys)
    changed = any(
        original.get(k, "").lower() != replayed.get(k, "").lower()
        for k in orig_keys & rep_keys
    )
    has_diff = bool(missing or added or changed)
    return has_diff, missing, added


def diff_records(original: RequestRecord, replayed: RequestRecord) -> DiffResult:
    """Compare two RequestRecord instances and return a DiffResult."""
    status_changed = original.response_status != replayed.response_status
    status_diff = (
        (original.response_status, replayed.response_status) if status_changed else None
    )

    body_changed = _normalize_body(original.response_body) != _normalize_body(
        replayed.response_body
    )

    orig_headers = original.response_headers or {}
    rep_headers = replayed.response_headers or {}
    headers_changed, missing_headers, added_headers = _compare_headers(
        orig_headers, rep_headers
    )

    return DiffResult(
        original=original,
        replayed=replayed,
        status_changed=status_changed,
        body_changed=body_changed,
        headers_changed=headers_changed,
        status_diff=status_diff,
        missing_headers=missing_headers,
        added_headers=added_headers,
    )
