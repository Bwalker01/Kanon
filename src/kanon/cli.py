"""Command-line entry point for Kanon."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import json
from pathlib import Path

from kanon import __version__, usage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kanon",
        description="Context engine for AI-assisted projects.",
    )
    parser.add_argument("--version", action="version", version=f"kanon {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="<command>")

    use = commands.add_parser("usage", help="token usage and estimated cost for a time window")
    use.add_argument("--since", help="start: ISO timestamp or git reference (commit time)")
    use.add_argument("--until", help="end: ISO timestamp or git reference (commit time)")
    use.add_argument("--logs", type=Path, help="Claude Code log folder (default: this project's)")
    use.add_argument("--json", action="store_true", help="print JSON")
    use.add_argument("--record", type=Path, metavar="WORK_FILE", help="append a row to this work file's Cost section")
    use.add_argument("--label", help="row label used with --record")
    return parser


def run_usage(args) -> int:
    repo = Path.cwd()
    try:
        since = usage.parse_time(args.since, repo) if args.since else None
        until = usage.parse_time(args.until, repo) if args.until else None
    except ValueError as error:
        print(f"kanon usage: {error}")
        return 2
    rep = usage.report(args.logs or usage.default_log_dir(repo), since, until)
    print(json.dumps(rep.as_dict(), indent=2) if args.json else usage.format_report(rep))
    if args.record:
        if not args.label:
            print("kanon usage: --record needs --label")
            return 2
        usage.record(rep, args.record, args.label)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "usage":
        return run_usage(args)
    return 0
