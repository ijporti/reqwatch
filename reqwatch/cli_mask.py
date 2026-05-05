"""CLI command for masking sensitive data in a stored request log."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.mask import mask_record, mask_summary


def cmd_mask(args: argparse.Namespace) -> None:
    store = RequestStore.load(args.store)
    records = store.all()

    if not records:
        print("No records found.")
        return

    header_keys: list[str] = args.header or []
    body_patterns: list[str] = args.body_pattern or []
    mask_str: str = args.mask

    masked_records = []
    for rec in records:
        masked = mask_record(rec, header_keys=header_keys, body_patterns=body_patterns, mask=mask_str)
        masked_records.append(masked)
        if args.verbose:
            print(f"[{rec.id}] {mask_summary(rec, masked)}")

    if args.output:
        out_store = RequestStore()
        for r in masked_records:
            out_store.add(r)
        out_store.save(args.output)
        print(f"Masked {len(masked_records)} record(s) written to {args.output}")
    elif args.format == "json":
        from reqwatch.export import to_json
        print(to_json(masked_records))
    else:
        for r in masked_records:
            print(f"{r.id}  {r.method}  {r.url}  {r.status_code}")


def build_mask_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("mask", help="Mask sensitive values in a request store")
    p.add_argument("store", help="Path to the request store file")
    p.add_argument(
        "--header",
        action="append",
        metavar="KEY",
        help="Additional header key to mask (repeatable)",
    )
    p.add_argument(
        "--body-pattern",
        action="append",
        metavar="REGEX",
        help="Regex pattern to mask in request/response bodies (repeatable)",
    )
    p.add_argument(
        "--mask",
        default="***",
        help="Replacement string for masked values (default: ***)",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        help="Write masked records to this store file instead of printing",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format when not writing to a file",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-record masking summary",
    )
    p.set_defaults(func=cmd_mask)
