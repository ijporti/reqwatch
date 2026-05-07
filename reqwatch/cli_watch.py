"""CLI sub-command: watch — tail a store file and print new records live."""

from __future__ import annotations

import argparse
import sys

from reqwatch.core import RequestRecord
from reqwatch.watch import watch_store


def _print_record(record: RequestRecord, fmt: str) -> None:
    if fmt == "json":
        import json
        print(json.dumps(record.to_dict()))
    else:
        print(record.summary())


def cmd_watch(args: argparse.Namespace) -> None:
    fmt = getattr(args, "format", "text")
    poll = getattr(args, "poll", 0.5)
    timeout = getattr(args, "timeout", None)
    max_records = getattr(args, "max_records", None)

    if fmt == "text":
        print(f"Watching {args.store} …  (Ctrl-C to stop)", file=sys.stderr)

    try:
        result = watch_store(
            path=args.store,
            on_record=lambda r: _print_record(r, fmt),
            poll_interval=poll,
            max_records=max_records,
            timeout=timeout,
        )
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return

    if fmt == "text":
        print(result.summary(), file=sys.stderr)


def build_watch_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:
    p = sub.add_parser("watch", help="Tail a store file and print new records as they arrive")
    p.add_argument("store", help="Path to the .json store file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--poll",
        type=float,
        default=0.5,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 0.5)",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Stop watching after this many seconds",
    )
    p.add_argument(
        "--max-records",
        type=int,
        default=None,
        dest="max_records",
        metavar="N",
        help="Stop after N new records have been printed",
    )
    p.set_defaults(func=cmd_watch)
    return p
