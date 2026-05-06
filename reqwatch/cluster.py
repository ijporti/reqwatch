"""Cluster records by similarity using URL patterns and method."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from reqwatch.core import RequestRecord

# Replace path segments that look like IDs with a placeholder
_ID_PATTERN = re.compile(r"(?<=/)(\d+|[0-9a-f]{8,})(?=/|$)", re.IGNORECASE)


def _url_template(url: str) -> str:
    """Collapse numeric / UUID path segments to {id}."""
    return _ID_PATTERN.sub("{id}", url)


@dataclass
class ClusterResult:
    key: str
    records: List[RequestRecord] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_error(self) -> bool:
        return self.error is not None

    @property
    def size(self) -> int:
        return len(self.records)

    def summary(self) -> str:
        if self.has_error:
            return f"[{self.key}] error: {self.error}"
        return f"[{self.key}] {self.size} record(s)"


def cluster(
    records: List[RequestRecord],
    by: str = "method+template",
) -> Dict[str, ClusterResult]:
    """Group *records* into clusters.

    Parameters
    ----------
    records:
        Input records to cluster.
    by:
        Clustering strategy.  Supported values:
        ``"method+template"``  (default) – method + normalised URL template.
        ``"template"``         – normalised URL template only.
        ``"method"``           – HTTP method only.
    """
    if by not in ("method+template", "template", "method"):
        return {
            "__error__": ClusterResult(
                key="__error__",
                error=f"Unknown clustering strategy: {by!r}",
            )
        }

    clusters: Dict[str, ClusterResult] = {}
    for record in records:
        template = _url_template(record.url)
        method = (record.method or "UNKNOWN").upper()

        if by == "method+template":
            key = f"{method} {template}"
        elif by == "template":
            key = template
        else:
            key = method

        if key not in clusters:
            clusters[key] = ClusterResult(key=key)
        clusters[key].records.append(record)

    return clusters


def cluster_summary(clusters: Dict[str, ClusterResult]) -> str:
    """Return a human-readable summary of all clusters."""
    if not clusters:
        return "No clusters."
    lines = [f"{len(clusters)} cluster(s):"]
    for result in sorted(clusters.values(), key=lambda c: -c.size):
        lines.append(f"  {result.summary()}")
    return "\n".join(lines)
