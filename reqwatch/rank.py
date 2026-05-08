"""Rank request records by a numeric criterion."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.core import RequestRecord


_CRITERIA = ("response_time", "body_size", "status")


@dataclass
class RankResult:
    records: List[RequestRecord]
    criterion: str
    ascending: bool
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"rank error: {self.error}"
        direction = "asc" if self.ascending else "desc"
        return (
            f"ranked {len(self.records)} record(s) by '{self.criterion}' ({direction})"
        )


def _key_for(record: RequestRecord, criterion: str) -> float:
    if criterion == "response_time":
        return float(record.metadata.get("response_time", 0.0))
    if criterion == "body_size":
        body = record.response_body or ""
        return float(len(body))
    if criterion == "status":
        return float(record.status_code or 0)
    return 0.0


def rank_records(
    records: List[RequestRecord],
    criterion: str = "response_time",
    ascending: bool = False,
    top_n: Optional[int] = None,
) -> RankResult:
    if criterion not in _CRITERIA:
        return RankResult(
            records=[],
            criterion=criterion,
            ascending=ascending,
            error=f"unknown criterion '{criterion}'; choose from {_CRITERIA}",
        )
    sorted_records = sorted(
        records,
        key=lambda r: _key_for(r, criterion),
        reverse=not ascending,
    )
    if top_n is not None and top_n > 0:
        sorted_records = sorted_records[:top_n]
    return RankResult(records=sorted_records, criterion=criterion, ascending=ascending)


def rank_summary(result: RankResult) -> str:
    return result.summary()
