"""CLI subcommand for retrying failed requests from a store file."""

from __future__ import annotations

import argparse
import sys

from reqwatch.core import RequestStore
from reqwatch.retry import retry_all, retry_summary


def cmd_retry(args: argparse.Namespace) -> None:
    store = RequestStore(args.store)
    records = store.load()

    if not records:
        print("No records found in store.")
        return

    # Optionally filter to only previously-failed records by status
    if args.failed_only:
        records = [
            r for r in records
            if r.response_status is None or r.response_status >= 400
        ]
        if not records:
            print("No failed records to retry.")
            return

    print(
        f"Retrying {len(records)} request(s) "
        f"(max_retries={args.max_retries}, backoff={args.backoff}s)..."
    )

    results = retry_all(
        records,
        max_retries=args.max_retries,
        backoff=args.backoff,
    )

    for res in results:
        print(f"  {res.summary()}")

    print()
    print(retry_summary(results))

    if args.fail_on_error and any(not r.succeeded for r in results):
        sys.exit(1)


def build_retry_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "retry",
        help="Retry requests from a store file, with configurable backoff",
    )
    parser.add_argument(
        "store",
        help="Path to the request store JSON file",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        dest="max_retries",
        help="Maximum number of attempts per request (default: 3)",
    )
    parser.add_argument(
        "--backoff",
        type=float,
        default=0.5,
        help="Base backoff in seconds between retries (default: 0.5)",
    )
    parser.add_argument(
        "--failed-only",
        action="store_true",
        dest="failed_only",
        help="Only retry requests with 4xx/5xx response status",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        dest="fail_on_error",
        help="Exit with code 1 if any request ultimately fails",
    )
    parser.set_defaults(func=cmd_retry)
