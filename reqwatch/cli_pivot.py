"""CLI command for pivoting request records by a chosen dimension."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.pivot import VALID_DIMENSIONS, pivot, pivot_summary


def cmd_pivot(args: argparse.Namespace) -> None:
    store = RequestStore(args.store)
    try:
        records = store.load()
    except FileNotFoundError:
        print(f"Store not found: {args.store}", file=sys.stderr)
        sys.exit(1)

    result = pivot(records, args.dimension)

    if result.has_error:
        print(result.summary(), file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = {
            "dimension": result.dimension,
            "groups": {
                key: [r.to_dict() for r in recs]
                for key, recs in result.table.items()
            },
        }
        print(json.dumps(output, indent=2))
    else:
        print(pivot_summary(result))


def build_pivot_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("pivot", help="Pivot records by a chosen dimension")
    p.add_argument("store", help="Path to the request store JSON file")
    p.add_argument(
        "dimension",
        choices=VALID_DIMENSIONS,
        help="Dimension to pivot on",
    )
    p.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_pivot)
