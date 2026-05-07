"""Live watch mode: tail a request store file and print new records as they arrive."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from reqwatch.core import RequestRecord, RequestStore


@dataclass
class WatchResult:
    seen: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def summary(self) -> str:
        if self.has_errors:
            return f"Watch ended with {len(self.errors)} error(s) after {self.seen} record(s)"
        return f"Watch ended after {self.seen} record(s)"


def watch_store(
    path: str,
    on_record: Callable[[RequestRecord], None],
    poll_interval: float = 0.5,
    max_records: Optional[int] = None,
    timeout: Optional[float] = None,
) -> WatchResult:
    """Poll *path* for new records and call *on_record* for each one.

    Stops when *max_records* have been seen or *timeout* seconds have elapsed.
    """
    result = WatchResult()
    seen_ids: set = set()
    deadline = time.monotonic() + timeout if timeout is not None else None

    while True:
        if deadline is not None and time.monotonic() >= deadline:
            break

        try:
            store = RequestStore.load(path)
            for record in store.records:
                rid = record.id
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    result.seen += 1
                    on_record(record)
                    if max_records is not None and result.seen >= max_records:
                        return result
        except Exception as exc:  # noqa: BLE001
            result.errors.append(str(exc))

        time.sleep(poll_interval)

    return result
