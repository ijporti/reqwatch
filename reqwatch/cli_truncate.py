"""CLI helpers for the *truncate* sub-command.

Allows users to preview how a stored request body would look after
truncation without modifying the underlying store.

Usage examples::

    reqwatch truncate --id <record-id> --max-bytes 256
    reqwatch truncate --id <record-id> --headers
"""

from __future__ import annotations

import argparse
import sys

from reqwatch.core import RequestStore
from reqwatch.truncate import (
    DEFAULT_MAX_BYTES,
    truncate_body,
    truncate_headers,
    truncation_summary,
)


def cmd_truncate(args: argparse.Namespace) -> None:
    """Entry-point for the *truncate* sub-command."""
    store = RequestStore(args.store)
    records = store.load()

    match = [r for r in records if r.id == args.id]
    if not match:
        print(f"No record found with id '{args.id}'", file=sys.stderr)
        sys.exit(1)

    record = match[0]
    max_bytes: int = args.max_bytes

    print(f"Record : {record.id}")
    print(f"Method : {record.method}  URL: {record.url}")
    print()

    if args.headers:
        truncated_hdrs = truncate_headers(
            record.headers or {}, max_value_length=args.max_header_value
        )
        print("--- Headers (truncated) ---")
        for k, v in truncated_hdrs.items():
            print(f"  {k}: {v}")
        print()

    req_summary = truncation_summary(record.body, max_bytes=max_bytes)
    print(f"Request  {req_summary}")
    print(truncate_body(record.body, max_bytes=max_bytes))
    print()

    resp_body = (record.response or {}).get("body")
    resp_summary = truncation_summary(resp_body, max_bytes=max_bytes)
    print(f"Response {resp_summary}")
    print(truncate_body(resp_body, max_bytes=max_bytes))


def build_truncate_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *truncate* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "truncate",
        help="Preview request/response bodies after truncation",
    )
    p.add_argument("--id", required=True, help="Record ID to inspect")
    p.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        dest="max_bytes",
        help=f"Maximum body length (default: {DEFAULT_MAX_BYTES})",
    )
    p.add_argument(
        "--headers",
        action="store_true",
        default=False,
        help="Also truncate and display headers",
    )
    p.add_argument(
        "--max-header-value",
        type=int,
        default=128,
        dest="max_header_value",
        help="Maximum header value length when --headers is set (default: 128)",
    )
    p.add_argument(
        "--store",
        default="reqwatch.json",
        help="Path to the request store file",
    )
    p.set_defaults(func=cmd_truncate)
