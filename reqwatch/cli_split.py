"""CLI command for splitting a request store into labelled buckets."""
from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.split import split_by


def _load_store(path: str) -> RequestStore:
    store = RequestStore()
    store.load(path)
    return store


def cmd_split(args: argparse.Namespace) -> None:
    try:
        store = _load_store(args.store)
    except Exception as exc:
        print(f"Error loading store: {exc}", file=sys.stderr)
        sys.exit(1)

    result = split_by(store.records, args.by)

    if not result.succeeded:
        print(f"Error: {result.error}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = {
            bucket: [r.to_dict() for r in recs]
            for bucket, recs in result.buckets.items()
        }
        print(json.dumps(output, indent=2))
    else:
        print(result.summary())
        for bucket, recs in sorted(result.buckets.items()):
            print(f"  [{bucket}]")
            for r in recs:
                print(f"    {r.summary()}")


def build_split_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("split", help="Split a store into buckets")
    p.add_argument("store", help="Path to request store JSON file")
    p.add_argument(
        "--by",
        choices=["method", "status", "host"],
        default="method",
        help="Criterion to split by (default: method)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_split)
