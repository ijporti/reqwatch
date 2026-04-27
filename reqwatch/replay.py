"""HTTP request replayer for reqwatch."""

import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

from reqwatch.core import RequestRecord, RequestStore


@dataclass
class ReplayResult:
    record: RequestRecord
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    elapsed_ms: Optional[float] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if self.success:
            return (
                f"[{self.status_code}] {self.record.method} {self.record.url} "
                f"({self.elapsed_ms:.1f}ms)"
            )
        return f"[ERROR] {self.record.method} {self.record.url} — {self.error}"


def replay_request(record: RequestRecord, base_url: Optional[str] = None) -> ReplayResult:
    """Replay a single RequestRecord, optionally overriding the base URL."""
    url = record.url
    if base_url:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(record.url)
        base = urlparse(base_url)
        url = urlunparse(parsed._replace(scheme=base.scheme, netloc=base.netloc))

    req = urllib.request.Request(
        url,
        method=record.method,
        headers=record.headers or {},
        data=record.body.encode() if record.body else None,
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed_ms = (time.monotonic() - start) * 1000
            body = resp.read().decode(errors="replace")
            return ReplayResult(
                record=record,
                status_code=resp.status,
                response_body=body,
                elapsed_ms=elapsed_ms,
            )
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        return ReplayResult(
            record=record,
            status_code=exc.code,
            elapsed_ms=elapsed_ms,
            error=str(exc),
        )
    except Exception as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        return ReplayResult(record=record, elapsed_ms=elapsed_ms, error=str(exc))


def replay_all(
    store: RequestStore,
    base_url: Optional[str] = None,
    delay_between: float = 0.0,
) -> list[ReplayResult]:
    """Replay all requests in the store, returning a list of results."""
    results = []
    records = store.all()
    for i, record in enumerate(records):
        result = replay_request(record, base_url=base_url)
        results.append(result)
        if delay_between > 0 and i < len(records) - 1:
            time.sleep(delay_between)
    return results
