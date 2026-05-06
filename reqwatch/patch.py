"""Patch fields on stored request records in-place."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from reqwatch.core import RequestRecord


@dataclass
class PatchResult:
    record_id: str
    applied: Dict[str, Any]
    skipped: Dict[str, Any]
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"[{self.record_id}] patch failed: {self.error}"
        parts = []
        if self.applied:
            keys = ", ".join(self.applied.keys())
            parts.append(f"applied: {keys}")
        if self.skipped:
            keys = ", ".join(self.skipped.keys())
            parts.append(f"skipped (unknown field): {keys}")
        detail = "; ".join(parts) if parts else "no changes"
        return f"[{self.record_id}] {detail}"


_PATCHABLE_FIELDS = {
    "method",
    "url",
    "request_headers",
    "request_body",
    "response_status",
    "response_headers",
    "response_body",
    "metadata",
}


def patch_record(record: RequestRecord, updates: Dict[str, Any]) -> PatchResult:
    """Apply *updates* to *record*, mutating it in place.

    Only fields listed in ``_PATCHABLE_FIELDS`` are accepted; all others are
    collected in ``skipped`` and left untouched.
    """
    applied: Dict[str, Any] = {}
    skipped: Dict[str, Any] = {}

    try:
        for key, value in updates.items():
            if key in _PATCHABLE_FIELDS:
                setattr(record, key, value)
                applied[key] = value
            else:
                skipped[key] = value
    except Exception as exc:  # noqa: BLE001
        return PatchResult(
            record_id=record.id,
            applied=applied,
            skipped=skipped,
            error=str(exc),
        )

    return PatchResult(record_id=record.id, applied=applied, skipped=skipped)


def patch_all(
    records: List[RequestRecord], updates: Dict[str, Any]
) -> List[PatchResult]:
    """Apply the same *updates* dict to every record in *records*."""
    return [patch_record(r, updates) for r in records]


def patch_summary(results: List[PatchResult]) -> str:
    total = len(results)
    ok = sum(1 for r in results if r.succeeded())
    failed = total - ok
    return f"Patched {ok}/{total} records" + (f", {failed} failed" if failed else "")
