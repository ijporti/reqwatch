"""CLI subcommand: reqwatch group — display records grouped by a dimension."""

import argparse
import sys
from reqwatch.core import RequestStore
from reqwatch.group import (
    group_by_method,
    group_by_status,
    group_by_host,
    group_summary,
)

DIMENSIONS = {
    "method": group_by_method,
    "status": group_by_status,
    "host": group_by_host,
}


def cmd_group(args: argparse.Namespace, out=sys.stdout) -> None:
    """Handle the 'group' subcommand."""
    store = RequestStore(args.store)
    records = store.load()

    if not records:
        out.write("No records found.\n")
        return

    dimension = args.dimension
    if dimension not in DIMENSIONS:
        out.write(f"Unknown dimension '{dimension}'. "
                  f"Choose from: {', '.join(DIMENSIONS)}.\n")
        return

    groups = DIMENSIONS[dimension](records)
    summary = group_summary(groups)

    out.write(f"Grouped by {dimension} ({len(records)} total records):\n")
    for key, count in sorted(summary.items(), key=lambda x: -x[1]):
        out.write(f"  {key:<30} {count} request(s)\n")


def build_group_parser(subparsers) -> None:
    """Register the 'group' subcommand on an existing subparsers object."""
    p = subparsers.add_parser(
        "group",
        help="Group requests by method, status, or host",
    )
    p.add_argument(
        "dimension",
        choices=list(DIMENSIONS.keys()),
        help="Dimension to group by",
    )
    p.add_argument(
        "--store",
        default="reqwatch.json",
        help="Path to the request store file (default: reqwatch.json)",
    )
    p.set_defaults(func=cmd_group)
