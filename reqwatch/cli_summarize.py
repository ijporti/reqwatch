"""CLI command for summarizing a request store."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.summarize import summarize_records


def cmd_summarize(args: argparse.Namespace) -> None:
    store = RequestStore(args.store)
    records = store.load()

    if not records:
        print("No records found in store.", file=sys.stderr)

    result = summarize_records(records)

    if args.format == "json":
        data = {
            "total": result.total,
            "method_counts": result.method_counts,
            "status_counts": {str(k): v for k, v in result.status_counts.items()},
            "error_count": result.error_count,
            "unique_hosts": result.unique_hosts,
            "notes": result.notes,
        }
        print(json.dumps(data, indent=2))
    else:
        print(result.summary())


def build_summarize_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "summarize",
        help="Print a summary report of recorded requests.",
    )
    parser.add_argument(
        "--store",
        default="reqwatch.json",
        help="Path to the request store file (default: reqwatch.json).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.set_defaults(func=cmd_summarize)
