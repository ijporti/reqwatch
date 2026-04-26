"""Core HTTP request logging and replaying functionality for reqwatch."""

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RequestRecord:
    """Represents a captured HTTP request and its associated response."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    method: str = ""
    url: str = ""
    headers: dict = field(default_factory=dict)
    body: Optional[str] = None
    response_status: Optional[int] = None
    response_headers: dict = field(default_factory=dict)
    response_body: Optional[str] = None
    duration_ms: Optional[float] = None
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize the record to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RequestRecord":
        """Deserialize a RequestRecord from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def summary(self) -> str:
        """Return a short human-readable summary of the request."""
        status = self.response_status or "???"
        duration = f"{self.duration_ms:.1f}ms" if self.duration_ms is not None else "N/A"
        return f"[{self.timestamp}] {self.method} {self.url} -> {status} ({duration})"


class RequestStore:
    """In-memory store for captured request records with optional persistence."""

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the store.

        Args:
            log_file: Optional path to a JSONL file for persistent logging.
        """
        self._records: list[RequestRecord] = []
        self.log_file = log_file

        if log_file:
            self._load_from_file(log_file)

    def add(self, record: RequestRecord) -> None:
        """Add a new request record to the store and optionally persist it."""
        self._records.append(record)
        if self.log_file:
            self._append_to_file(record)

    def get(self, record_id: str) -> Optional[RequestRecord]:
        """Retrieve a record by its unique ID."""
        for record in self._records:
            if record.id == record_id:
                return record
        return None

    def all(self) -> list[RequestRecord]:
        """Return all stored records in insertion order."""
        return list(self._records)

    def filter(self, method: Optional[str] = None, url_contains: Optional[str] = None,
               status: Optional[int] = None) -> list[RequestRecord]:
        """Filter records by method, URL substring, or response status."""
        results = self._records
        if method:
            results = [r for r in results if r.method.upper() == method.upper()]
        if url_contains:
            results = [r for r in results if url_contains in r.url]
        if status is not None:
            results = [r for r in results if r.response_status == status]
        return list(results)

    def clear(self) -> None:
        """Remove all records from the in-memory store."""
        self._records.clear()

    def _append_to_file(self, record: RequestRecord) -> None:
        """Append a single record as a JSON line to the log file."""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def _load_from_file(self, path: str) -> None:
        """Load existing records from a JSONL log file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self._records.append(RequestRecord.from_dict(data))
                        except (json.JSONDecodeError, TypeError):
                            # Skip malformed lines
                            continue
        except FileNotFoundError:
            pass  # File will be created on first write
