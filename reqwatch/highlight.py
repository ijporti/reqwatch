"""Highlight matching patterns in request/response fields for visual debugging."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.core import RequestRecord

ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_CYAN = "\033[36m"
ANSI_RESET = "\033[0m"

_COLOUR_MAP = {
    "yellow": ANSI_YELLOW,
    "red": ANSI_RED,
    "cyan": ANSI_CYAN,
}


@dataclass
class HighlightResult:
    record_id: str
    url: str
    matched_fields: List[str] = field(default_factory=list)
    highlighted_url: Optional[str] = None
    highlighted_body: Optional[str] = None

    @property
    def has_match(self) -> bool:
        return bool(self.matched_fields)

    def summary(self) -> str:
        if not self.has_match:
            return f"[{self.record_id}] no matches"
        fields = ", ".join(self.matched_fields)
        return f"[{self.record_id}] matched in: {fields}"


def _apply_colour(text: str, pattern: str, colour: str) -> str:
    code = _COLOUR_MAP.get(colour, ANSI_YELLOW)
    try:
        return re.sub(
            f"({re.escape(pattern)})",
            f"{code}\\1{ANSI_RESET}",
            text,
            flags=re.IGNORECASE,
        )
    except re.error:
        return text


def highlight_record(
    record: RequestRecord,
    pattern: str,
    colour: str = "yellow",
    fields: Optional[List[str]] = None,
) -> HighlightResult:
    """Search for *pattern* in the given record fields and return a HighlightResult."""
    if fields is None:
        fields = ["url", "request_body", "response_body"]

    result = HighlightResult(record_id=record.request_id, url=record.url)

    if "url" in fields and re.search(pattern, record.url, re.IGNORECASE):
        result.matched_fields.append("url")
        result.highlighted_url = _apply_colour(record.url, pattern, colour)

    body = record.request_body or ""
    if "request_body" in fields and re.search(pattern, body, re.IGNORECASE):
        result.matched_fields.append("request_body")
        result.highlighted_body = _apply_colour(body, pattern, colour)

    resp = record.response_body or ""
    if "response_body" in fields and re.search(pattern, resp, re.IGNORECASE):
        if "response_body" not in result.matched_fields:
            result.matched_fields.append("response_body")
        result.highlighted_body = _apply_colour(resp, pattern, colour)

    return result


def highlight_all(
    records: List[RequestRecord],
    pattern: str,
    colour: str = "yellow",
    fields: Optional[List[str]] = None,
) -> List[HighlightResult]:
    """Apply highlight_record to every record; return only those with matches."""
    results = [highlight_record(r, pattern, colour, fields) for r in records]
    return [r for r in results if r.has_match]
