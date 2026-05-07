"""CLI sub-command: trim — remove old or excess records from a store."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from reqwatch.core import RequestStore
from reqwatch.trim import trim_after, trim_before, trim_to_last_n


def cmd_trim(args: argparse.Namespace) -> None:
    store = RequestStore(args.store)
    store.load()
    records = store.records

    if args.last is not None:
        result = trim_to_last_n(records, args.last)
    elif args.before:
        try:
            cutoff = datetime.fromisoformat(args.before)
        except ValueError as exc:
            print(f"Invalid --before date: {exc}")
            return
        result = trim_before(records, cutoff)
    elif args.after:
        try:
            cutoff = datetime.fromisoformat(args.after)
        except ValueError as exc:
            print(f"Invalid --after date: {exc}")
            return
        result = trim_after(records, cutoff)
    else:
        print("Specify one of --last, --before, or --after.")
        return

    if not result.succeeded():
        print(result.summary())
        return

    store.save()

    if args.format == "json":
        print(
            json.dumps(
                {
                    "original_count": result.original_count,
                    "trimmed_count": result.trimmed_count,
                    "removed": result.original_count - result.trimmed_count,
                }
            )
        )
    else:
        print(result.summary())


def build_trim_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("trim", help="Remove old or excess records")
    p.add_argument("store", help="Path to the request store file")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--last", type=int, metavar="N", help="Keep only the most recent N records"
    )
    group.add_argument(
        "--before", metavar="ISO_DATE", help="Remove records before this date"
    )
    group.add_argument(
        "--after", metavar="ISO_DATE", help="Remove records after this date"
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    p.set_defaults(func=cmd_trim)
