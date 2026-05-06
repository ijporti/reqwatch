"""Request scoring: assign a numeric relevance score to records based on configurable criteria."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.core import RequestRecord


@dataclass
class ScoreResult:
    record: RequestRecord
    score: float
    reasons: List[str] = field(default_factory=list)

    def summary(self) -> str:
        reason_str = "; ".join(self.reasons) if self.reasons else "no criteria matched"
        return f"{self.record.method} {self.record.url} -> score={self.score:.2f} ({reason_str})"


def score_record(
    record: RequestRecord,
    *,
    error_weight: float = 5.0,
    slow_threshold_ms: float = 500.0,
    slow_weight: float = 3.0,
    server_error_weight: float = 4.0,
    client_error_weight: float = 2.0,
    method_weights: Optional[dict] = None,
) -> ScoreResult:
    """Compute a relevance/interest score for a single request record."""
    score = 0.0
    reasons: List[str] = []

    # Error in replay / capture
    if record.error:
        score += error_weight
        reasons.append(f"has error (+{error_weight})")

    # HTTP status scoring
    status = record.response_status or 0
    if 500 <= status < 600:
        score += server_error_weight
        reasons.append(f"5xx status {status} (+{server_error_weight})")
    elif 400 <= status < 500:
        score += client_error_weight
        reasons.append(f"4xx status {status} (+{client_error_weight})")

    # Slow response
    duration = record.duration_ms
    if duration is not None and duration > slow_threshold_ms:
        score += slow_weight
        reasons.append(f"slow {duration:.0f}ms (+{slow_weight})")

    # Method-based weight
    if method_weights:
        method = (record.method or "").upper()
        extra = method_weights.get(method, 0.0)
        if extra:
            score += extra
            reasons.append(f"method {method} (+{extra})")

    return ScoreResult(record=record, score=score, reasons=reasons)


def score_all(
    records: List[RequestRecord],
    **kwargs,
) -> List[ScoreResult]:
    """Score all records and return results sorted by descending score."""
    results = [score_record(r, **kwargs) for r in records]
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def score_summary(results: List[ScoreResult]) -> str:
    if not results:
        return "No records scored."
    top = results[0]
    total = len(results)
    high = sum(1 for r in results if r.score > 0)
    return (
        f"{total} record(s) scored; {high} with score > 0; "
        f"top: {top.record.method} {top.record.url} (score={top.score:.2f})"
    )
