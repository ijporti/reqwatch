"""CLI entry point for reqwatch."""

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.replay import replay_all
from reqwatch.stats import compute_stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqwatch",
        description="Lightweight HTTP request logger and replayer.",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    list_p = sub.add_parser("list", help="List recorded requests")
    list_p.add_argument("store", help="Path to request store JSON file")
    list_p.add_argument("--method", help="Filter by HTTP method")

    # replay
    replay_p = sub.add_parser("replay", help="Replay recorded requests")
    replay_p.add_argument("store", help="Path to request store JSON file")
    replay_p.add_argument("--base-url", dest="base_url", help="Override base URL")

    # stats
    stats_p = sub.add_parser("stats", help="Show statistics for recorded requests")
    stats_p.add_argument("store", help="Path to request store JSON file")
    stats_p.add_argument("--json", dest="as_json", action="store_true",
                         help="Output stats as JSON")

    return parser


def cmd_replay(args: argparse.Namespace) -> None:
    store = RequestStore.load(args.store)
    results = replay_all(store.records, base_url=getattr(args, "base_url", None))
    for result in results:
        print(result.summary())


def cmd_list(args: argparse.Namespace) -> None:
    store = RequestStore.load(args.store)
    records = store.records
    if args.method:
        records = [r for r in records if r.method.upper() == args.method.upper()]
    if not records:
        print("No records found.")
        return
    for rec in records:
        print(rec.summary())


def cmd_stats(args: argparse.Namespace) -> None:
    store = RequestStore.load(args.store)
    stats = compute_stats(store.records)
    if args.as_json:
        data = {
            "total": stats.total,
            "success_count": stats.success_count,
            "error_count": stats.error_count,
            "by_method": stats.by_method,
            "by_status": {str(k): v for k, v in stats.by_status.items()},
        }
        print(json.dumps(data, indent=2))
    else:
        print(stats.summary())


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "list":
        cmd_list(args)
    elif args.command == "replay":
        cmd_replay(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
