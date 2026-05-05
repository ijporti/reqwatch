"""CLI sub-command: highlight — search and highlight patterns in stored requests."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.highlight import highlight_all


def cmd_highlight(args: argparse.Namespace) -> None:
    store = RequestStore(args.store)
    records = store.load()

    if not records:
        print("No records found.")
        return

    fields = args.fields.split(",") if args.fields else None
    results = highlight_all(records, args.pattern, colour=args.colour, fields=fields)

    if not results:
        print(f"No matches found for pattern: {args.pattern!r}")
        return

    if args.format == "json":
        output = [
            {
                "record_id": r.record_id,
                "url": r.url,
                "matched_fields": r.matched_fields,
                "highlighted_url": r.highlighted_url,
                "highlighted_body": r.highlighted_body,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
        return

    print(f"Found {len(results)} matching record(s) for pattern: {args.pattern!r}\n")
    for r in results:
        print(r.summary())
        if r.highlighted_url:
            print(f"  URL : {r.highlighted_url}")
        if r.highlighted_body:
            preview = r.highlighted_body[:200]
            suffix = "..." if len(r.highlighted_body) > 200 else ""
            print(f"  Body: {preview}{suffix}")
        print()


def build_highlight_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "highlight",
        help="Search for a pattern and highlight matches in stored requests.",
    )
    p.add_argument("pattern", help="Text pattern to search for (case-insensitive).")
    p.add_argument(
        "--store",
        default="reqwatch.json",
        help="Path to the request store file (default: reqwatch.json).",
    )
    p.add_argument(
        "--colour",
        default="yellow",
        choices=["yellow", "red", "cyan"],
        help="ANSI highlight colour (default: yellow).",
    )
    p.add_argument(
        "--fields",
        default=None,
        help="Comma-separated list of fields to search: url,request_body,response_body.",
    )
    p.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_highlight)
