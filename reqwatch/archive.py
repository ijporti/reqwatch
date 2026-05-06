"""Archive and restore request stores to/from compressed bundles."""

import gzip
import json
import os
from dataclasses import dataclass
from typing import List, Optional

from reqwatch.core import RequestStore, RequestRecord, from_dict, to_dict


@dataclass
class ArchiveResult:
    path: str
    record_count: int
    size_bytes: int
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.succeeded:
            return f"Archive failed: {self.error}"
        kb = self.size_bytes / 1024
        return (
            f"Archived {self.record_count} record(s) to '{self.path}' "
            f"({kb:.1f} KB)"
        )


def archive_store(store: RequestStore, dest_path: str) -> ArchiveResult:
    """Write all records in *store* to a gzip-compressed JSON file."""
    records = store.all()
    payload = json.dumps([to_dict(r) for r in records], indent=2).encode("utf-8")
    try:
        with gzip.open(dest_path, "wb") as fh:
            fh.write(payload)
        size = os.path.getsize(dest_path)
        return ArchiveResult(path=dest_path, record_count=len(records), size_bytes=size)
    except OSError as exc:
        return ArchiveResult(
            path=dest_path, record_count=0, size_bytes=0, error=str(exc)
        )


def restore_store(src_path: str) -> List[RequestRecord]:
    """Read records from a gzip-compressed JSON archive file."""
    with gzip.open(src_path, "rb") as fh:
        data = json.loads(fh.read().decode("utf-8"))
    return [from_dict(d) for d in data]


def archive_summary(result: ArchiveResult) -> str:
    return result.summary()
