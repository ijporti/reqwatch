"""Lint HTTP request records for common issues and anti-patterns."""

from dataclasses import dataclass, field
from typing import List
from reqwatch.core import RequestRecord


LINT_RULES = [
    "missing_content_type",
    "large_body",
    "non_standard_method",
    "missing_auth",
    "error_status",
]

STANDARD_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
LARGE_BODY_THRESHOLD = 1024 * 100  # 100 KB


@dataclass
class LintResult:
    record: RequestRecord
    warnings: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        method = self.record.method.upper()
        url = self.record.url
        if self.is_clean:
            return f"OK  {method} {url}"
        joined = "; ".join(self.warnings)
        return f"WARN {method} {url} — {joined}"


def lint_record(record: RequestRecord, rules: List[str] = None) -> LintResult:
    """Run lint checks against a single record."""
    active = set(rules) if rules else set(LINT_RULES)
    warnings: List[str] = []

    req_headers = {k.lower(): v for k, v in (record.request_headers or {}).items()}

    if "missing_content_type" in active:
        if record.method.upper() in {"POST", "PUT", "PATCH"}:
            if "content-type" not in req_headers:
                warnings.append("missing Content-Type header on request")

    if "large_body" in active:
        body = record.request_body or ""
        if len(body.encode()) > LARGE_BODY_THRESHOLD:
            warnings.append(f"request body exceeds {LARGE_BODY_THRESHOLD // 1024} KB")

    if "non_standard_method" in active:
        if record.method.upper() not in STANDARD_METHODS:
            warnings.append(f"non-standard HTTP method '{record.method}'")

    if "missing_auth" in active:
        auth_headers = {"authorization", "x-api-key", "x-auth-token"}
        if not auth_headers.intersection(req_headers):
            warnings.append("no authentication header detected")

    if "error_status" in active:
        status = record.response_status or 0
        if status >= 400:
            warnings.append(f"response status {status} indicates an error")

    return LintResult(record=record, warnings=warnings)


def lint_all(records: List[RequestRecord], rules: List[str] = None) -> List[LintResult]:
    """Lint a list of records and return all results."""
    return [lint_record(r, rules) for r in records]


def lint_summary(results: List[LintResult]) -> str:
    """Return a human-readable summary of lint results."""
    total = len(results)
    clean = sum(1 for r in results if r.is_clean)
    warned = total - clean
    return f"Linted {total} record(s): {clean} clean, {warned} with warnings."
