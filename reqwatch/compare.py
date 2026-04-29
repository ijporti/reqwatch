"""Compare two request stores to find new, removed, or changed records."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from reqwatch.core import RequestRecord


@dataclass
class CompareResult:
    added: List[RequestRecord] = field(default_factory=list)
    removed: List[RequestRecord] = field(default_factory=list)
    changed: List[Tuple[RequestRecord, RequestRecord]] = field(default_factory=list)
    unchanged: List[RequestRecord] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = [
            f"Added:     {len(self.added)}",
            f"Removed:   {len(self.removed)}",
            f"Changed:   {len(self.changed)}",
            f"Unchanged: {len(self.unchanged)}",
        ]
        return "\n".join(lines)


def _record_key(record: RequestRecord) -> str:
    return f"{record.method.upper()}:{record.url}"


def _records_differ(a: RequestRecord, b: RequestRecord) -> bool:
    return (
        a.status_code != b.status_code
        or a.request_body != b.request_body
        or a.response_body != b.response_body
    )


def compare_stores(
    baseline: List[RequestRecord],
    current: List[RequestRecord],
) -> CompareResult:
    """Compare baseline records against current records by method+url key."""
    baseline_map: Dict[str, RequestRecord] = {_record_key(r): r for r in baseline}
    current_map: Dict[str, RequestRecord] = {_record_key(r): r for r in current}

    result = CompareResult()

    for key, cur_rec in current_map.items():
        if key not in baseline_map:
            result.added.append(cur_rec)
        elif _records_differ(baseline_map[key], cur_rec):
            result.changed.append((baseline_map[key], cur_rec))
        else:
            result.unchanged.append(cur_rec)

    for key, base_rec in baseline_map.items():
        if key not in current_map:
            result.removed.append(base_rec)

    return result
