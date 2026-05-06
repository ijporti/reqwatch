"""Checkpoint support: save and restore named snapshots of a RequestStore."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from reqwatch.core import RequestRecord, RequestStore, from_dict, to_dict


def save_checkpoint(store: RequestStore, name: str, directory: str = ".") -> str:
    """Persist *store* as a named checkpoint JSON file.

    Returns the path of the file that was written.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{name}.checkpoint.json")
    payload = {"name": name, "records": [to_dict(r) for r in store.all()]}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return path


def load_checkpoint(name: str, directory: str = ".") -> RequestStore:
    """Load a previously saved checkpoint and return a populated RequestStore."""
    path = os.path.join(directory, f"{name}.checkpoint.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Checkpoint '{name}' not found at {path}")
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    store = RequestStore()
    for raw in payload.get("records", []):
        store.add(from_dict(raw))
    return store


def list_checkpoints(directory: str = ".") -> List[str]:
    """Return the names of all checkpoints found in *directory*."""
    if not os.path.isdir(directory):
        return []
    names: List[str] = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".checkpoint.json"):
            names.append(filename[: -len(".checkpoint.json")])
    return names


def delete_checkpoint(name: str, directory: str = ".") -> bool:
    """Delete a checkpoint file.  Returns True if the file existed."""
    path = os.path.join(directory, f"{name}.checkpoint.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def checkpoint_summary(name: str, store: RequestStore) -> str:
    """Return a human-readable summary line for a checkpoint."""
    total = len(store.all())
    return f"Checkpoint '{name}': {total} record(s)"
