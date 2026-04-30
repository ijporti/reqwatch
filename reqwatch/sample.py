"""Sampling utilities for reqwatch — randomly or deterministically sample records."""

from __future__ import annotations

import hashlib
import random
from typing import List, Optional

from reqwatch.core import RequestRecord


def sample_random(
    records: List[RequestRecord],
    n: int,
    seed: Optional[int] = None,
) -> List[RequestRecord]:
    """Return up to *n* records chosen at random (without replacement)."""
    if n <= 0:
        return []
    rng = random.Random(seed)
    population = list(records)
    k = min(n, len(population))
    return rng.sample(population, k)


def sample_rate(
    records: List[RequestRecord],
    rate: float,
    seed: Optional[int] = None,
) -> List[RequestRecord]:
    """Return records kept with probability *rate* (0.0–1.0)."""
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"rate must be between 0.0 and 1.0, got {rate}")
    rng = random.Random(seed)
    return [r for r in records if rng.random() < rate]


def sample_deterministic(
    records: List[RequestRecord],
    every_n: int,
) -> List[RequestRecord]:
    """Return every *every_n*-th record (1-based index), e.g. every_n=3 keeps indices 0,3,6,…"""
    if every_n < 1:
        raise ValueError(f"every_n must be >= 1, got {every_n}")
    return [r for i, r in enumerate(records) if i % every_n == 0]


def sample_by_hash(
    records: List[RequestRecord],
    rate: float,
) -> List[RequestRecord]:
    """Stable sampling: keep a record if the MD5 of its request_id falls below *rate*.

    Produces the same subset across runs for the same data.
    """
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"rate must be between 0.0 and 1.0, got {rate}")
    result = []
    for r in records:
        digest = hashlib.md5(r.request_id.encode()).hexdigest()
        bucket = int(digest[:8], 16) / 0xFFFFFFFF
        if bucket < rate:
            result.append(r)
    return result


def sample_summary(original: List[RequestRecord], sampled: List[RequestRecord]) -> str:
    """Human-readable summary of a sampling operation."""
    total = len(original)
    kept = len(sampled)
    pct = (kept / total * 100) if total else 0.0
    return f"Sampled {kept}/{total} records ({pct:.1f}%)"
