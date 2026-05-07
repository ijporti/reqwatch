"""Route-based grouping and matching for request records."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from reqwatch.core import RequestRecord

_PARAM_RE = re.compile(r"\{[^}]+\}|:[a-zA-Z_][a-zA-Z0-9_]*")


def _route_pattern(template: str) -> re.Pattern:
    """Compile a route template like /users/{id} into a regex."""
    escaped = re.escape(template)
    escaped = _PARAM_RE.sub(lambda _: "[^/]+", escaped)
    return re.compile(f"^{escaped}$")


def match_route(record: RequestRecord, template: str) -> bool:
    """Return True if the record's URL path matches the route template."""
    path = record.url.split("?")[0].rstrip("/") or "/"
    pattern = _route_pattern(template.rstrip("/") or "/")
    return bool(pattern.match(path))


def group_by_route(
    records: List[RequestRecord], templates: List[str]
) -> Dict[str, List[RequestRecord]]:
    """Group records by the first matching route template.

    Records that match no template are placed under the key '<unmatched>'.
    """
    buckets: Dict[str, List[RequestRecord]] = {t: [] for t in templates}
    buckets["<unmatched>"] = []
    for record in records:
        placed = False
        for template in templates:
            if match_route(record, template):
                buckets[template].append(record)
                placed = True
                break
        if not placed:
            buckets["<unmatched>"].append(record)
    return buckets


@dataclass
class RouteResult:
    groups: Dict[str, List[RequestRecord]] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def has_error(self) -> bool:
        return self.error is not None

    def summary(self) -> str:
        if self.has_error:
            return f"route error: {self.error}"
        lines = []
        for template, records in self.groups.items():
            lines.append(f"  {template}: {len(records)} record(s)")
        total = sum(len(v) for v in self.groups.values())
        return f"{total} record(s) across {len(self.groups)} route(s)\n" + "\n".join(lines)


def route_records(
    records: List[RequestRecord], templates: List[str]
) -> RouteResult:
    """Group records by route templates and return a RouteResult."""
    try:
        groups = group_by_route(records, templates)
        return RouteResult(groups=groups)
    except Exception as exc:  # pragma: no cover
        return RouteResult(error=str(exc))
