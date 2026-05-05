"""CLI commands for throttle-controlled replay."""

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.throttle import ThrottleConfig, throttle_records, throttle_summary


def _run_throttle(store_path: str, rps: float, burst: int, max_records: int, fmt: str) -> None:
    store = RequestStore(store_path)
    records = store.all()

    if not records:
        print("No records found.")
        return

    config = ThrottleConfig(
        requests_per_second=rps,
        burst=burst,
    )

    result = throttle_records(
        records,
        config,
        max_records=max_records if max_records > 0 else None,
    )

    if fmt == "json":
        print(
            json.dumps(
                {
                    "total": result.total,
                    "dispatched": result.dispatched,
                    "dropped": result.dropped,
                    "elapsed": round(result.elapsed, 4),
                    "actual_rps": round(result.actual_rps, 4),
                    "config": throttle_summary(config),
                },
                indent=2,
            )
        )
    else:
        print(throttle_summary(config))
        print(result.summary())


def cmd_throttle(args: argparse.Namespace) -> None:
    _run_throttle(
        store_path=args.store,
        rps=args.rps,
        burst=args.burst,
        max_records=args.max_records,
        fmt=args.format,
    )


def build_throttle_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "throttle",
        help="Replay requests at a controlled rate",
    )
    p.add_argument("store", help="Path to the request store file")
    p.add_argument(
        "--rps",
        type=float,
        default=10.0,
        help="Target requests per second (default: 10)",
    )
    p.add_argument(
        "--burst",
        type=int,
        default=1,
        help="Number of requests to send without delay at the start (default: 1)",
    )
    p.add_argument(
        "--max-records",
        type=int,
        default=0,
        dest="max_records",
        help="Maximum number of records to dispatch (0 = all)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_throttle)
    return p
