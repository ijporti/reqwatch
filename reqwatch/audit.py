"""Audit log: record which operations have been applied to a store."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEntry:
    operation: str
    timestamp: str
    details: dict = field(default_factory=dict)


@dataclass
class AuditLog:
    entries: List[AuditEntry] = field(default_factory=list)


def add_entry(log: AuditLog, operation: str, details: Optional[dict] = None) -> AuditLog:
    """Return a new AuditLog with the entry appended."""
    entry = AuditEntry(
        operation=operation,
        timestamp=datetime.now(timezone.utc).isoformat(),
        details=details or {},
    )
    return AuditLog(entries=log.entries + [entry])


def save_audit_log(log: AuditLog, path: str) -> None:
    """Persist the audit log as JSON."""
    data = [
        {"operation": e.operation, "timestamp": e.timestamp, "details": e.details}
        for e in log.entries
    ]
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_audit_log(path: str) -> AuditLog:
    """Load an audit log from a JSON file; return empty log if missing."""
    if not os.path.exists(path):
        return AuditLog()
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    entries = [
        AuditEntry(
            operation=item["operation"],
            timestamp=item["timestamp"],
            details=item.get("details", {}),
        )
        for item in data
    ]
    return AuditLog(entries=entries)


def audit_summary(log: AuditLog) -> str:
    """Return a human-readable summary of the audit log."""
    if not log.entries:
        return "audit log: no entries"
    lines = [f"audit log: {len(log.entries)} entr{'y' if len(log.entries) == 1 else 'ies'}"]
    for e in log.entries:
        detail_str = f" {e.details}" if e.details else ""
        lines.append(f"  [{e.timestamp}] {e.operation}{detail_str}")
    return "\n".join(lines)
