"""CLI sub-command: patch — modify fields on stored records."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.patch import patch_all, patch_summary


def _load_store(path: str) -> RequestStore:
    store = RequestStore(path)
    store.load()
    return store


def cmd_patch(args: argparse.Namespace) -> None:
    store = _load_store(args.store)
    records = store.all()

    if not records:
        print("No records found.")
        return

    # Build the updates dict from --set key=value pairs
    updates: dict = {}
    for pair in args.set or []:
        if "=" not in pair:
            print(f"Invalid --set value (expected key=value): {pair}", file=sys.stderr)
            sys.exit(1)
        key, _, value = pair.partition("=")
        # Attempt JSON decode so callers can pass numbers / booleans / dicts
        try:
            updates[key.strip()] = json.loads(value)
        except json.JSONDecodeError:
            updates[key.strip()] = value

    if not updates:
        print("Nothing to patch — supply at least one --set key=value.", file=sys.stderr)
        sys.exit(1)

    results = patch_all(records, updates)

    if args.format == "json":
        output = [
            {
                "id": r.record_id,
                "succeeded": r.succeeded(),
                "applied": r.applied,
                "skipped": r.skipped,
                "error": r.error,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        for r in results:
            print(r.summary())
        print()
        print(patch_summary(results))

    # Persist changes only when all patches succeeded (or --force supplied)
    failed = [r for r in results if not r.succeeded()]
    if failed and not getattr(args, "force", False):
        print(
            f"{len(failed)} patch(es) failed — store NOT saved. Use --force to save anyway.",
            file=sys.stderr,
        )
        sys.exit(1)

    store.save()


def build_patch_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("patch", help="Modify fields on stored records")
    p.add_argument("store", help="Path to the request store file")
    p.add_argument(
        "--set",
        metavar="KEY=VALUE",
        action="append",
        help="Field to update (repeatable). VALUE is parsed as JSON when possible.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Save store even when some patches failed",
    )
    p.set_defaults(func=cmd_patch)
