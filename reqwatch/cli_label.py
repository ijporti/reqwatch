"""CLI commands for managing record labels."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.label import add_label, filter_by_label, label_summary, remove_label


def _load_store(path: str) -> RequestStore:
    store = RequestStore(path)
    store.load()
    return store


def cmd_label(args: argparse.Namespace) -> None:
    store = _load_store(args.store)
    records = store.records

    if args.action == "add":
        key, _, value = args.label.partition("=")
        if not key or not value:
            print("error: --label must be in KEY=VALUE format", file=sys.stderr)
            sys.exit(1)
        updated = [add_label(r, key.strip(), value.strip()) for r in records]
        store.records = updated
        store.save()
        if args.format == "json":
            print(json.dumps({"action": "add", "key": key, "value": value, "count": len(updated)}))
        else:
            print(f"Added label {key}={value} to {len(updated)} record(s).")

    elif args.action == "remove":
        updated = [remove_label(r, args.key) for r in records]
        store.records = updated
        store.save()
        if args.format == "json":
            print(json.dumps({"action": "remove", "key": args.key, "count": len(updated)}))
        else:
            print(f"Removed label '{args.key}' from {len(updated)} record(s).")

    elif args.action == "filter":
        key, _, value = args.label.partition("=")
        value = value.strip() or None
        matched = filter_by_label(records, key.strip(), value)
        if args.format == "json":
            print(json.dumps([{"id": r.id, "url": r.url} for r in matched], indent=2))
        else:
            if not matched:
                print("No records matched.")
            else:
                for r in matched:
                    print(f"  {r.method} {r.url}")

    elif args.action == "summary":
        out = label_summary(records)
        if args.format == "json":
            summary_lines = [ln.strip() for ln in out.splitlines()]
            print(json.dumps({"summary": summary_lines}))
        else:
            print(out)


def build_label_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("label", help="Manage record labels")
    p.add_argument("store", help="Path to the request store file")
    p.add_argument(
        "action",
        choices=["add", "remove", "filter", "summary"],
        help="Label action to perform",
    )
    p.add_argument("--label", default="", help="KEY=VALUE label (for add/filter)")
    p.add_argument("--key", default="", help="Label key (for remove)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_label)
