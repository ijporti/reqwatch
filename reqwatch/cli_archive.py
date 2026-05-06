"""CLI commands for archiving and restoring request stores."""

import argparse
import json
import sys

from reqwatch.archive import archive_store, restore_store, archive_summary
from reqwatch.core import RequestStore, to_dict


def _load_store(path: str) -> RequestStore:
    store = RequestStore()
    try:
        with open(path) as fh:
            records_data = json.load(fh)
        from reqwatch.core import from_dict
        for d in records_data:
            store.add(from_dict(d))
    except FileNotFoundError:
        pass
    return store


def cmd_archive(args: argparse.Namespace) -> None:
    store = _load_store(args.store)
    result = archive_store(store, args.output)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "path": result.path,
                    "record_count": result.record_count,
                    "size_bytes": result.size_bytes,
                    "succeeded": result.succeeded,
                    "error": result.error,
                }
            )
        )
    else:
        print(archive_summary(result))

    if not result.succeeded:
        sys.exit(1)


def cmd_restore(args: argparse.Namespace) -> None:
    try:
        records = restore_store(args.input)
    except Exception as exc:  # noqa: BLE001
        print(f"Restore failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps([to_dict(r) for r in records], indent=2))
    else:
        if not records:
            print("No records found in archive.")
        else:
            for r in records:
                print(f"[{r.method}] {r.url} -> {r.response_status}")
            print(f"\nRestored {len(records)} record(s) from '{args.input}'.")


def build_archive_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p_archive = subparsers.add_parser("archive", help="Archive a store to a .gz file")
    p_archive.add_argument("store", help="Path to the request store JSON file")
    p_archive.add_argument("output", help="Destination .gz archive path")
    p_archive.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    p_archive.set_defaults(func=cmd_archive)

    p_restore = subparsers.add_parser(
        "restore", help="Restore records from a .gz archive"
    )
    p_restore.add_argument("input", help="Path to the .gz archive file")
    p_restore.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    p_restore.set_defaults(func=cmd_restore)
