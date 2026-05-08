"""CLI commands for the audit log."""
from __future__ import annotations

import argparse
import json
import sys

from reqwatch.audit import audit_summary, load_audit_log

_DEFAULT_AUDIT_PATH = ".reqwatch_audit.json"


def cmd_audit(args: argparse.Namespace) -> None:
    log = load_audit_log(args.audit_file)

    if args.format == "json":
        data = [
            {
                "operation": e.operation,
                "timestamp": e.timestamp,
                "details": e.details,
            }
            for e in log.entries
        ]
        print(json.dumps(data, indent=2))
        return

    # text mode
    if not log.entries:
        print("audit log: no entries")
        return

    if args.tail:
        entries = log.entries[-args.tail :]
    else:
        entries = log.entries

    for e in entries:
        detail_str = f"  {e.details}" if e.details else ""
        print(f"[{e.timestamp}] {e.operation}{detail_str}")

    print()
    print(audit_summary(log))


def build_audit_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("audit", help="Show the audit log for a store")
    p.add_argument(
        "--audit-file",
        default=_DEFAULT_AUDIT_PATH,
        help="Path to the audit log JSON file (default: .reqwatch_audit.json)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.add_argument(
        "--tail",
        type=int,
        default=0,
        metavar="N",
        help="Show only the last N entries",
    )
    p.set_defaults(func=cmd_audit)
