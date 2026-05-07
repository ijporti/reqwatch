"""CLI interface for the chain command."""

from __future__ import annotations

import argparse
import json
from typing import List

from reqwatch.core import RequestStore
from reqwatch.chain import build_chain, run_chain, chain_summary


def _load_store(path: str) -> RequestStore:
    store = RequestStore()
    store.load(path)
    return store


def cmd_chain(args: argparse.Namespace) -> None:
    store = _load_store(args.store)
    records = store.all()

    if not records:
        print("No records found in store.")
        return

    # Optionally limit to first N records
    if hasattr(args, "limit") and args.limit and args.limit > 0:
        records = records[: args.limit]

    steps = build_chain(records)
    result = run_chain(steps)

    if args.format == "json":
        out = {
            "succeeded": result.succeeded,
            "length": result.length,
            "outputs": len(result.outputs),
            "error": result.error,
            "summary": result.summary(),
        }
        print(json.dumps(out, indent=2))
    else:
        print(chain_summary(result))
        for i, record in enumerate(result.outputs, 1):
            print(f"  [{i}] {record.method} {record.url} -> {record.status_code}")


def build_chain_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("chain", help="Run a sequential chain of request records")
    p.add_argument("store", help="Path to the request store JSON file")
    p.add_argument("--limit", type=int, default=0, help="Maximum number of records to chain (0 = all)")
    p.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p.set_defaults(func=cmd_chain)
