"""Merge two RequestStores into one, with deduplication options."""

from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.core import RequestRecord, RequestStore
from reqwatch.dedupe import deduplicate


@dataclass
class MergeResult:
    records: List[RequestRecord]
    total_before: int
    total_after: int
    duplicates_removed: int
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"Merge failed: {self.error}"
        return (
            f"Merged {self.total_before} records into {self.total_after} "
            f"({self.duplicates_removed} duplicates removed)"
        )


def merge_stores(
    base: RequestStore,
    other: RequestStore,
    dedupe: bool = False,
) -> MergeResult:
    """Merge *other* into *base*, optionally deduplicating the result."""
    try:
        combined = list(base.records) + list(other.records)
        total_before = len(combined)

        if dedupe:
            combined = deduplicate(combined)

        duplicates_removed = total_before - len(combined)
        return MergeResult(
            records=combined,
            total_before=total_before,
            total_after=len(combined),
            duplicates_removed=duplicates_removed,
        )
    except Exception as exc:  # pragma: no cover
        return MergeResult(
            records=[],
            total_before=0,
            total_after=0,
            duplicates_removed=0,
            error=str(exc),
        )


def merge_summary(result: MergeResult) -> str:
    return result.summary()
