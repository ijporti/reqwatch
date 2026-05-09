"""Digest: produce a compact summary digest of a request store."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import List, Optional

from reqwatch.core import RequestRecord


@dataclass
class DigestResult:
    digest: str
    total: int
    method_counts: dict
    status_counts: dict
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.error:
            return f"Digest error: {self.error}"
        methods = ", ".join(f"{k}:{v}" for k, v in sorted(self.method_counts.items()))
        statuses = ", ".join(f"{k}:{v}" for k, v in sorted(self.status_counts.items()))
        return (
            f"Digest: {self.digest[:12]}  "
            f"total={self.total}  "
            f"methods=[{methods}]  "
            f"statuses=[{statuses}]"
        )


def _record_fingerprint(record: RequestRecord) -> str:
    parts = [
        record.method.upper(),
        record.url,
        str(record.status_code),
        record.timestamp,
    ]
    return "|".join(parts)


def compute_digest(records: List[RequestRecord]) -> DigestResult:
    """Compute a stable digest over a list of records."""
    try:
        method_counts: dict = {}
        status_counts: dict = {}
        fingerprints = []

        for r in records:
            m = r.method.upper()
            method_counts[m] = method_counts.get(m, 0) + 1
            s = str(r.status_code)
            status_counts[s] = status_counts.get(s, 0) + 1
            fingerprints.append(_record_fingerprint(r))

        fingerprints.sort()
        payload = json.dumps(fingerprints, sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()

        return DigestResult(
            digest=digest,
            total=len(records),
            method_counts=method_counts,
            status_counts=status_counts,
        )
    except Exception as exc:  # pragma: no cover
        return DigestResult(digest="", total=0, method_counts={}, status_counts={}, error=str(exc))


def digest_summary(records: List[RequestRecord]) -> str:
    return compute_digest(records).summary()
