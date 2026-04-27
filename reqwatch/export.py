"""Export RequestStore records to common formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Iterable, List

from reqwatch.core import RequestRecord, to_dict


def to_json(records: Iterable[RequestRecord], indent: int = 2) -> str:
    """Serialise records to a JSON string."""
    data = [to_dict(r) for r in records]
    return json.dumps(data, indent=indent, default=str)


def to_csv(records: Iterable[RequestRecord]) -> str:
    """Serialise records to a CSV string with a header row."""
    fieldnames = [
        "method",
        "url",
        "status_code",
        "elapsed_ms",
        "request_body",
        "response_body",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in records:
        row = {
            "method": r.method,
            "url": r.url,
            "status_code": r.status_code,
            "elapsed_ms": r.elapsed_ms,
            "request_body": r.request_body or "",
            "response_body": r.response_body.decode("utf-8", errors="replace")
            if r.response_body
            else "",
        }
        writer.writerow(row)
    return buf.getvalue()


def to_curl(records: Iterable[RequestRecord]) -> str:
    """Generate a series of curl commands from records."""
    lines: List[str] = []
    for r in records:
        parts = [f"curl -X {r.method}"]
        for key, value in r.request_headers.items():
            parts.append(f"  -H '{key}: {value}'")
        if r.request_body:
            body = r.request_body.replace("'", "'\"'\"'")
            parts.append(f"  --data '{body}'")
        parts.append(f"  '{r.url}'")
        lines.append(" \\\n".join(parts))
    return "\n\n".join(lines)
