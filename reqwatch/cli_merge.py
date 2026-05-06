"""CLI commands for merging two request stores."""

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.merge import merge_stores


def _load_store(path: str) -> RequestStore:
    store = RequestStore()
    store.load(path)
    return store


def cmd_merge(args: argparse.Namespace) -> None:
    try:
        base = _load_store(args.base)
    except FileNotFoundError:
        print(f"Error: base store not found: {args.base}", file=sys.stderr)
        sys.exit(1)

    try:
        other = _load_store(args.other)
    except FileNotFoundError:
        print(f"Error: other store not found: {args.other}", file=sys.stderr)
        sys.exit(1)

    result = merge_stores(base, other, dedupe=args.dedupe)

    if not result.succeeded():
        print(f"Error: {result.error}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_store = RequestStore()
        for rec in result.records:
            out_store.add(rec)
        out_store.save(args.output)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "total_before": result.total_before,
                    "total_after": result.total_after,
                    "duplicates_removed": result.duplicates_removed,
                },
                indent=2,
            )
        )
    else:
        print(result.summary())
        if args.output:
            print(f"Saved to {args.output}")


def build_merge_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("merge", help="Merge two request stores")
    p.add_argument("base", help="Path to the base store file")
    p.add_argument("other", help="Path to the store file to merge in")
    p.add_argument("-o", "--output", default=None, help="Save merged store to this path")
    p.add_argument("--dedupe", action="store_true", help="Remove duplicate records after merging")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_merge)
