"""CLI command for computing a store digest."""
from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.digest import compute_digest
from reqwatch.filter import apply_filters


def _load_store(path: str) -> RequestStore:
    store = RequestStore(path)
    store.load()
    return store


def cmd_digest(args: argparse.Namespace) -> None:
    try:
        store = _load_store(args.store)
    except FileNotFoundError:
        print(f"Store not found: {args.store}", file=sys.stderr)
        sys.exit(1)

    records = store.records

    filters = []
    if getattr(args, "method", None):
        from reqwatch.filter import filter_by_method
        filters.append(filter_by_method(args.method))
    if getattr(args, "status", None):
        from reqwatch.filter import filter_by_status
        filters.append(filter_by_status(int(args.status)))

    if filters:
        records = apply_filters(records, filters)

    result = compute_digest(records)

    if args.format == "json":
        print(json.dumps({
            "digest": result.digest,
            "total": result.total,
            "method_counts": result.method_counts,
            "status_counts": result.status_counts,
            "error": result.error,
        }, indent=2))
    else:
        print(result.summary())


def build_digest_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("digest", help="Compute a content digest of the request store")
    p.add_argument("store", help="Path to the request store JSON file")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--method", help="Filter by HTTP method before digesting")
    p.add_argument("--status", help="Filter by status code before digesting")
    p.set_defaults(func=cmd_digest)
