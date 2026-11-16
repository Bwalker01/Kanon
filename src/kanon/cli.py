"""Command-line entry point for Kanon."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from kanon import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kanon",
        description="Context engine for AI-assisted projects.",
    )
    parser.add_argument("--version", action="version", version=f"kanon {__version__}")
    parser.add_subparsers(dest="command", metavar="<command>")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return 0
