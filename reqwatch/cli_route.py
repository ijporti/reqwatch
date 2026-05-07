"""CLI command for grouping records by route template."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.route import route_records


def _load_store(path: str) -> RequestStore:
    store = RequestStore()
    store.load(path)
    return store


def cmd_route(args: argparse.Namespace) -> None:
    try:
        store = _load_store(args.store)
    except FileNotFoundError:
        print(f"store not found: {args.store}", file=sys.stderr)
        sys.exit(1)

    templates: list[str] = args.routes
    if not templates:
        print("no route templates provided", file=sys.stderr)
        sys.exit(1)

    result = route_records(store.records, templates)

    if result.has_error:
        print(f"error: {result.error}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = {
            template: [r.to_dict() for r in records]
            for template, records in result.groups.items()
        }
        print(json.dumps(output, indent=2))
    else:
        print(result.summary())
        for template, records in result.groups.items():
            if records:
                print(f"\n[{template}]")
                for r in records:
                    print(f"  {r.summary()}")


def build_route_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("route", help="group requests by route template")
    p.add_argument("store", help="path to the request store (JSON)")
    p.add_argument(
        "routes",
        nargs="+",
        help="route templates, e.g. /users/{id}",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="output format (default: text)",
    )
    p.set_defaults(func=cmd_route)
