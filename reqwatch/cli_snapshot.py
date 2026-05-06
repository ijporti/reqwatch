"""CLI sub-commands for snapshot management."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.snapshot import (
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
    snapshot_summary,
)

_DEFAULT_DIR = ".reqwatch_snapshots"


def _load_store(path: str) -> RequestStore:
    """Load a RequestStore from *path*, exiting with an error on failure."""
    store = RequestStore()
    try:
        store.load(path)
    except FileNotFoundError:
        print(f"Store file '{path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load store '{path}': {exc}", file=sys.stderr)
        sys.exit(1)
    return store


def cmd_snapshot(args: argparse.Namespace) -> None:
    action = args.snapshot_action

    if action == "save":
        store = _load_store(args.store)
        result = save_snapshot(store, args.name, directory=args.dir)
        if args.format == "json":
            print(
                json.dumps(
                    {
                        "name": result.name,
                        "record_count": result.record_count,
                        "path": result.path,
                        "error": result.error,
                        "succeeded": result.succeeded(),
                    }
                )
            )
        else:
            print(result.summary())
        if not result.succeeded():
            sys.exit(1)

    elif action == "restore":
        loaded = load_snapshot(args.name, directory=args.dir)
        if loaded is None:
            print(f"Snapshot '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)
        loaded.save(args.store)
        if args.format == "json":
            print(json.dumps({"restored": args.name, "records": len(loaded.all())}))
        else:
            print(
                f"Restored snapshot '{args.name}' "
                f"({len(loaded.all())} record(s)) to {args.store}"
            )

    elif action == "list":
        names = list_snapshots(directory=args.dir)
        if args.format == "json":
            print(json.dumps(names))
        else:
            print(snapshot_summary(names))

    elif action == "delete":
        ok = delete_snapshot(args.name, directory=args.dir)
        if args.format == "json":
            print(json.dumps({"deleted": ok, "name": args.name}))
        else:
            if ok:
                print(f"Deleted snapshot '{args.name}'.")
            else:
                print(f"Snapshot '{args.name}' not found.", file=sys.stderr)
                sys.exit(1)


def build_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("snapshot", help="Manage named store snapshots")
    p.add_argument("--dir", default=_DEFAULT_DIR, help="Snapshot storage directory")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--store", default="reqwatch.json", help="Store file path")

    sub = p.add_subparsers(dest="snapshot_action", required=True)

    sv = sub.add_parser("save", help="Save current store as a named snapshot")
    sv.add_argument("name", help="Snapshot name")

    rs = sub.add_parser("restore", help="Restore a snapshot into the store")
    rs.add_argument("name", help="Snapshot name")

    sub.add_parser("list", help="List available snapshots")

    dl = sub.add_parser("delete", help="Delete a named snapshot")
    dl.add_argument("name", help="Snapshot name")
