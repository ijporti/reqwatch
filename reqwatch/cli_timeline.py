"""CLI subcommand: timeline — display requests in chronological order."""

import argparse
from reqwatch.core import RequestStore
from reqwatch.timeline import timeline_summary, time_range


def cmd_timeline(args: argparse.Namespace) -> None:
    store = RequestStore(args.store)
    records = store.load()

    if not records:
        print("No records found.")
        return

    limit = args.limit if args.limit and args.limit > 0 else None
    lines = timeline_summary(records, limit=limit)

    earliest, latest = time_range(records)
    print(f"Timeline ({len(records)} total records)")
    print(f"  From : {earliest}")
    print(f"  To   : {latest}")
    print(f"  Showing: {len(lines)} record(s)")
    print("-" * 60)
    for line in lines:
        print(line)


def build_timeline_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "timeline",
        help="Display requests in chronological order",
    )
    parser.add_argument(
        "--store",
        default="reqwatch.json",
        help="Path to the request store file (default: reqwatch.json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of records to display",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Show most recent requests first",
    )
    parser.set_defaults(func=cmd_timeline)
