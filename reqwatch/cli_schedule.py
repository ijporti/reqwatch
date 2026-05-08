"""CLI commands for the schedule feature."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.schedule import run_schedule


def _load_store(path: str) -> RequestStore:
    store = RequestStore()
    store.load(path)
    return store


def cmd_schedule(args: argparse.Namespace) -> None:
    try:
        store = _load_store(args.store)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading store: {exc}", file=sys.stderr)
        sys.exit(1)

    records = store.records
    if not records:
        print("No records found in store.", file=sys.stderr)
        sys.exit(1)

    result = run_schedule(
        records,
        runs=args.runs,
        interval_seconds=args.interval,
        dry_run=args.dry_run,
    )

    if args.format == "json":
        output = {
            "runs": result.runs,
            "total_requests": len(result.results),
            "succeeded": sum(1 for r in result.results if r.success()),
            "failed": sum(1 for r in result.results if not r.success()),
            "error": result.error,
        }
        print(json.dumps(output, indent=2))
    else:
        print(result.summary())
        if not result.succeeded():
            sys.exit(1)


def build_schedule_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "schedule",
        help="Replay requests on a scheduled interval",
    )
    p.add_argument("store", help="Path to the request store file")
    p.add_argument(
        "--runs", type=int, default=1, help="Number of replay runs (default: 1)"
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between runs (default: 1.0)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simulate replay without making real HTTP requests",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_schedule)
