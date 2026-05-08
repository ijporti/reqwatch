"""CLI command for generating request reports."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.report import generate_report


def _load_store(path: str) -> RequestStore:
    store = RequestStore()
    store.load(path)
    return store


def cmd_report(args: argparse.Namespace) -> None:
    try:
        store = _load_store(args.store)
    except FileNotFoundError:
        print(f"Error: store file not found: {args.store}", file=sys.stderr)
        sys.exit(1)

    result = generate_report(store, title=args.title, top_n=args.top)

    if not result.succeeded():
        print(f"Error: {result.error}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "title": result.title,
                    "total": result.total,
                    "error_rate": result.error_rate,
                    "method_counts": result.method_counts,
                    "status_counts": result.status_counts,
                    "top_urls": result.top_urls,
                },
                indent=2,
            )
        )
    else:
        print(result.summary())


def build_report_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("report", help="Generate a summary report of recorded requests")
    p.add_argument("store", help="Path to the request store JSON file")
    p.add_argument("--title", default="Request Report", help="Report title")
    p.add_argument("--top", type=int, default=5, metavar="N", help="Number of top URLs to show (default: 5)")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_report)
