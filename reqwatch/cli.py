"""Command-line interface for reqwatch replay."""

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.replay import replay_all, replay_request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqwatch",
        description="Lightweight HTTP request logger and replayer.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # replay command
    replay_p = sub.add_parser("replay", help="Replay recorded requests")
    replay_p.add_argument("store_file", help="Path to the JSON store file")
    replay_p.add_argument(
        "--base-url", default=None, help="Override base URL for replayed requests"
    )
    replay_p.add_argument(
        "--delay", type=float, default=0.0, help="Seconds between requests (default: 0)"
    )
    replay_p.add_argument(
        "--id", dest="record_id", default=None, help="Replay only the request with this ID"
    )
    replay_p.add_argument(
        "--json", dest="output_json", action="store_true", help="Output results as JSON"
    )

    # list command
    list_p = sub.add_parser("list", help="List recorded requests")
    list_p.add_argument("store_file", help="Path to the JSON store file")

    return parser


def cmd_replay(args: argparse.Namespace) -> int:
    store = RequestStore()
    store.load(args.store_file)

    if args.record_id:
        record = store.get(args.record_id)
        if record is None:
            print(f"No record found with id: {args.record_id}", file=sys.stderr)
            return 1
        results = [replay_request(record, base_url=args.base_url)]
    else:
        results = replay_all(store, base_url=args.base_url, delay_between=args.delay)

    if args.output_json:
        output = [
            {
                "id": r.record.id,
                "success": r.success,
                "status_code": r.status_code,
                "elapsed_ms": r.elapsed_ms,
                "error": r.error,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        for r in results:
            print(r.summary())

    failures = sum(1 for r in results if not r.success)
    return 0 if failures == 0 else 1


def cmd_list(args: argparse.Namespace) -> int:
    store = RequestStore()
    store.load(args.store_file)
    records = store.all()
    if not records:
        print("No records found.")
        return 0
    for rec in records:
        print(rec.summary())
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "replay":
        sys.exit(cmd_replay(args))
    elif args.command == "list":
        sys.exit(cmd_list(args))


if __name__ == "__main__":
    main()
