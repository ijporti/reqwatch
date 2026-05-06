"""CLI sub-commands for checkpoint management."""

from __future__ import annotations

import argparse
import sys

from reqwatch.checkpoint import (
    checkpoint_summary,
    delete_checkpoint,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)
from reqwatch.core import RequestStore, from_dict
import json
import os


def _load_store(path: str) -> RequestStore:
    from reqwatch.core import RequestStore, from_dict
    store = RequestStore()
    if not os.path.exists(path):
        return store
    with open(path, "r", encoding="utf-8") as fh:
        for raw in json.load(fh):
            store.add(from_dict(raw))
    return store


def cmd_checkpoint(args: argparse.Namespace) -> None:
    checkpoint_dir = getattr(args, "checkpoint_dir", ".")

    if args.checkpoint_action == "save":
        store = _load_store(args.store)
        path = save_checkpoint(store, args.checkpoint_name, directory=checkpoint_dir)
        print(checkpoint_summary(args.checkpoint_name, store))
        print(f"Saved to {path}")

    elif args.checkpoint_action == "load":
        store = load_checkpoint(args.checkpoint_name, directory=checkpoint_dir)
        print(checkpoint_summary(args.checkpoint_name, store))

    elif args.checkpoint_action == "list":
        names = list_checkpoints(checkpoint_dir)
        if not names:
            print("No checkpoints found.")
        else:
            for name in names:
                try:
                    s = load_checkpoint(name, directory=checkpoint_dir)
                    print(checkpoint_summary(name, s))
                except Exception:
                    print(f"  {name} (unreadable)")

    elif args.checkpoint_action == "delete":
        removed = delete_checkpoint(args.checkpoint_name, directory=checkpoint_dir)
        if removed:
            print(f"Deleted checkpoint '{args.checkpoint_name}'.")
        else:
            print(f"Checkpoint '{args.checkpoint_name}' not found.", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown action: {args.checkpoint_action}", file=sys.stderr)
        sys.exit(1)


def build_checkpoint_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("checkpoint", help="Save, load, list, or delete request store checkpoints")
    p.add_argument("checkpoint_action", choices=["save", "load", "list", "delete"], help="Action to perform")
    p.add_argument("--name", dest="checkpoint_name", default="default", help="Checkpoint name")
    p.add_argument("--store", default="requests.json", help="Path to the request store (for save)")
    p.add_argument("--dir", dest="checkpoint_dir", default=".", help="Directory for checkpoint files")
    p.set_defaults(func=cmd_checkpoint)
