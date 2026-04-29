"""CLI command for comparing two request store files."""

import argparse
import json
from reqwatch.core import RequestStore, from_dict
from reqwatch.compare import compare_stores


def _load_store(path: str):
    store = RequestStore(path)
    return store.load_all()


def cmd_compare(args: argparse.Namespace) -> None:
    baseline_records = _load_store(args.baseline)
    current_records = _load_store(args.current)

    result = compare_stores(baseline_records, current_records)

    if args.format == "json":
        output = {
            "added": [r.to_dict() for r in result.added],
            "removed": [r.to_dict() for r in result.removed],
            "changed": [
                {"baseline": a.to_dict(), "current": b.to_dict()}
                for a, b in result.changed
            ],
            "unchanged_count": len(result.unchanged),
        }
        print(json.dumps(output, indent=2))
        return

    print(f"Comparing: {args.baseline} → {args.current}")
    print()
    print(result.summary())

    if args.verbose:
        if result.added:
            print("\n[Added]")
            for r in result.added:
                print(f"  + {r.method.upper()} {r.url}")

        if result.removed:
            print("\n[Removed]")
            for r in result.removed:
                print(f"  - {r.method.upper()} {r.url}")

        if result.changed:
            print("\n[Changed]")
            for base, curr in result.changed:
                print(f"  ~ {curr.method.upper()} {curr.url}")
                if base.response_status != curr.response_status:
                    print(f"    status: {base.response_status} → {curr.response_status}")


def build_compare_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "compare",
        help="Compare two request store files for differences",
    )
    parser.add_argument("baseline", help="Path to baseline store file")
    parser.add_argument("current", help="Path to current store file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show details of each change",
    )
    parser.set_defaults(func=cmd_compare)
