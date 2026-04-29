"""CLI sub-commands for managing record annotations."""

from __future__ import annotations

import argparse
import sys

from reqwatch.core import RequestStore
from reqwatch.annotate import (
    add_annotation,
    remove_annotation,
    get_annotations,
    annotation_summary,
)


def cmd_annotate(args: argparse.Namespace) -> None:
    store = RequestStore(args.store)
    records = store.load()

    if not records:
        print("No records found in store.", file=sys.stderr)
        return

    # Resolve target record by 1-based index
    idx = args.index - 1
    if idx < 0 or idx >= len(records):
        print(f"Index {args.index} out of range (store has {len(records)} records).", file=sys.stderr)
        sys.exit(1)

    record = records[idx]

    if args.annotate_cmd == "add":
        add_annotation(record, args.note)
        store.save(records)
        print(f"Added annotation to record {args.index}: {args.note!r}")

    elif args.annotate_cmd == "remove":
        remove_annotation(record, args.note)
        store.save(records)
        print(f"Removed annotation from record {args.index}: {args.note!r}")

    elif args.annotate_cmd == "list":
        print(annotation_summary(record))

    else:
        print(f"Unknown annotate sub-command: {args.annotate_cmd}", file=sys.stderr)
        sys.exit(1)


def build_annotate_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("annotate", help="Add, remove, or list annotations on a record")
    p.add_argument("--store", default="reqwatch.json", help="Path to the request store file")
    p.add_argument("--index", type=int, required=True, help="1-based index of the target record")

    sub = p.add_subparsers(dest="annotate_cmd", required=True)

    add_p = sub.add_parser("add", help="Attach a note to the record")
    add_p.add_argument("note", help="Annotation text")

    rm_p = sub.add_parser("remove", help="Remove a note from the record")
    rm_p.add_argument("note", help="Annotation text to remove")

    sub.add_parser("list", help="List all annotations on the record")

    p.set_defaults(func=cmd_annotate)
