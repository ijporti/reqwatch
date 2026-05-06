"""CLI command for clustering request records."""
from __future__ import annotations

import argparse
import json
import sys

from reqwatch.cluster import cluster, cluster_summary
from reqwatch.core import RequestStore


def _load_store(path: str) -> RequestStore:
    store = RequestStore(path)
    store.load()
    return store


def cmd_cluster(args: argparse.Namespace) -> None:
    store = _load_store(args.store)
    records = store.all()

    clusters = cluster(records, by=args.by)

    # Surface any strategy error immediately
    if "__error__" in clusters:
        print(clusters["__error__"].error, file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = {
            key: {
                "key": result.key,
                "size": result.size,
                "records": [
                    {"method": r.method, "url": r.url, "status": r.response_status}
                    for r in result.records
                ],
            }
            for key, result in clusters.items()
        }
        print(json.dumps(output, indent=2))
    else:
        print(cluster_summary(clusters))


def build_cluster_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "cluster",
        help="Cluster request records by URL pattern and/or method.",
    )
    p.add_argument("store", help="Path to the request store JSON file.")
    p.add_argument(
        "--by",
        choices=["method+template", "template", "method"],
        default="method+template",
        help="Clustering strategy (default: method+template).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_cluster)
