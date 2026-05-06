"""Validate recorded requests and responses against basic rules."""

from dataclasses import dataclass, field
from typing import List, Optional
from reqwatch.core import RequestRecord


_VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"}


@dataclass
class ValidationResult:
    record: RequestRecord
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        if self.is_valid:
            return f"[OK] {self.record.method} {self.record.url}"
        joined = "; ".join(self.errors)
        return f"[INVALID] {self.record.method} {self.record.url} — {joined}"


def validate_record(record: RequestRecord) -> ValidationResult:
    """Run all validation checks against a single record."""
    errors: List[str] = []

    if not record.method or record.method.upper() not in _VALID_METHODS:
        errors.append(f"invalid HTTP method: {record.method!r}")

    if not record.url or not record.url.startswith(("http://", "https://")):
        errors.append(f"invalid URL: {record.url!r}")

    if record.status_code is not None:
        if not (100 <= record.status_code <= 599):
            errors.append(f"invalid status code: {record.status_code}")

    if record.timestamp is not None and record.timestamp < 0:
        errors.append(f"negative timestamp: {record.timestamp}")

    return ValidationResult(record=record, errors=errors)


def validate_all(records: List[RequestRecord]) -> List[ValidationResult]:
    """Validate every record in a list."""
    return [validate_record(r) for r in records]


def validation_summary(results: List[ValidationResult]) -> str:
    """Return a human-readable summary of validation results."""
    total = len(results)
    invalid = [r for r in results if not r.is_valid]
    if total == 0:
        return "No records to validate."
    if not invalid:
        return f"All {total} record(s) valid."
    return (
        f"{len(invalid)} of {total} record(s) invalid: "
        + ", ".join(r.record.url for r in invalid)
    )
