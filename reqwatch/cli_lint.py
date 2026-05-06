"""CLI command for linting request records."""

import argparse
import json
import sys

from reqwatch.core import RequestStore
from reqwatch.lint import lint_all, lint_summary, LINT_RULES


def cmd_lint(args: argparse.Namespace) -> None:
    store = RequestStore.load(args.store)
    records = store.records

    rules = args.rules.split(",") if args.rules else None

    results = lint_all(records, rules=rules)

    if args.only_warnings:
        results = [r for r in results if not r.is_clean]

    if args.format == "json":
        output = [
            {
                "method": r.record.method,
                "url": r.record.url,
                "is_clean": r.is_clean,
                "warnings": r.warnings,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        for r in results:
            print(r.summary())
        print()
        print(lint_summary(results))

    if args.fail_on_warnings and any(not r.is_clean for r in results):
        sys.exit(1)


def build_lint_parser(subparsers) -> None:
    p = subparsers.add_parser("lint", help="Lint request records for common issues")
    p.add_argument("store", help="Path to the request store JSON file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--rules",
        default=None,
        help=(
            "Comma-separated list of rules to apply. "
            f"Available: {', '.join(LINT_RULES)}"
        ),
    )
    p.add_argument(
        "--only-warnings",
        action="store_true",
        default=False,
        help="Only show records with warnings",
    )
    p.add_argument(
        "--fail-on-warnings",
        action="store_true",
        default=False,
        help="Exit with code 1 if any warnings are found",
    )
    p.set_defaults(func=cmd_lint)
