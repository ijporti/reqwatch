"""Snapshot support: capture and restore named point-in-time copies of a store."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional

from reqwatch.core import RequestStore, RequestRecord, to_dict, from_dict


@dataclass
class SnapshotResult:
    name: str
    record_count: int
    path: str
    error: Optional[str] = None

    def succeeded(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.succeeded():
            return f"Snapshot '{self.name}' failed: {self.error}"
        return (
            f"Snapshot '{self.name}' saved {self.record_count} record(s) "
            f"to {self.path}"
        )


def _snapshot_path(directory: str, name: str) -> str:
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, f"{name}.snapshot.json")


def save_snapshot(
    store: RequestStore, name: str, directory: str = ".reqwatch_snapshots"
) -> SnapshotResult:
    path = _snapshot_path(directory, name)
    records = store.all()
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([to_dict(r) for r in records], fh, indent=2)
    except OSError as exc:
        return SnapshotResult(name=name, record_count=0, path=path, error=str(exc))
    return SnapshotResult(name=name, record_count=len(records), path=path)


def load_snapshot(
    name: str, directory: str = ".reqwatch_snapshots"
) -> Optional[RequestStore]:
    path = _snapshot_path(directory, name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    store = RequestStore()
    for item in data:
        store.add(from_dict(item))
    return store


def list_snapshots(directory: str = ".reqwatch_snapshots") -> List[str]:
    if not os.path.isdir(directory):
        return []
    names = []
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".snapshot.json"):
            names.append(fname[: -len(".snapshot.json")])
    return names


def delete_snapshot(
    name: str, directory: str = ".reqwatch_snapshots"
) -> bool:
    path = _snapshot_path(directory, name)
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True


def snapshot_summary(names: List[str]) -> str:
    if not names:
        return "No snapshots found."
    lines = [f"  - {n}" for n in names]
    return "Snapshots:\n" + "\n".join(lines)
