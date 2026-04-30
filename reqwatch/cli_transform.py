"""CLI commands for transforming stored request records."""

import argparse
import json

from reqwatch.core import RequestStore
from reqwatch.transform import (
    apply_transforms,
    replace_host,
    set_request_header,
    remove_request_header,
    transform_summary,
)


def cmd_transform(args: argparse.Namespace) -> None:
    store = RequestStore(args.store)
    records = store.load()

    if not records:
        print("No records found.")
        return

    transforms = []

    if args.replace_host:
        try:
            old_host, new_host = args.replace_host.split(",", 1)
        except ValueError:
            print("Error: --replace-host requires 'old,new' format.")
            return
        transforms.append(lambda rec, o=old_host, n=new_host: replace_host(rec, o, n))

    if args.set_header:
        for item in args.set_header:
            try:
                key, value = item.split(":", 1)
            except ValueError:
                print(f"Error: --set-header requires 'Key:Value' format, got: {item}")
                return
            transforms.append(
                lambda rec, k=key.strip(), v=value.strip(): set_request_header(rec, k, v)
            )

    if args.remove_header:
        for key in args.remove_header:
            transforms.append(lambda rec, k=key: remove_request_header(rec, k))

    if not transforms:
        print("No transforms specified. Use --replace-host, --set-header, or --remove-header.")
        return

    transformed = apply_transforms(records, transforms)
    summary = transform_summary(records, transformed)

    if args.dry_run:
        print("[dry-run] " + summary)
        for rec in transformed:
            print(" ", rec.to_dict().get("url"), rec.to_dict().get("request_headers"))
    else:
        store.save(transformed)
        print(summary)


def build_transform_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Transform request records in a store file."
    if subparsers is not None:
        parser = subparsers.add_parser("transform", help=description)
    else:
        parser = argparse.ArgumentParser(prog="reqwatch transform", description=description)

    parser.add_argument("store", help="Path to the request store JSON file.")
    parser.add_argument(
        "--replace-host",
        metavar="OLD,NEW",
        help="Replace OLD host with NEW host in all URLs.",
    )
    parser.add_argument(
        "--set-header",
        metavar="Key:Value",
        action="append",
        help="Set a request header (repeatable).",
    )
    parser.add_argument(
        "--remove-header",
        metavar="KEY",
        action="append",
        help="Remove a request header by name (repeatable).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to the store.",
    )
    parser.set_defaults(func=cmd_transform)
    return parser
