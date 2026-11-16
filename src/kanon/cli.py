"""Command-line entry point for Kanon."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import json
from pathlib import Path

import getpass
import socket

from kanon import __version__, usage, verify
from kanon import init as init_module
from kanon.settings import Person


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kanon",
        description="Context engine for AI-assisted projects.",
    )
    parser.add_argument("--version", action="version", version=f"kanon {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="<command>")

    ini = commands.add_parser("init", help="prepare this Git repository for Kanon")
    ini.add_argument("--person-id", default="owner", help="profile id (default: owner)")
    ini.add_argument("--name", default="", help="the person's name")
    ini.add_argument("--approver", help="approver identity, role@host (default: owner@<this machine>)")
    ini.add_argument("--level", choices=init_module.PERSON_LEVELS, help="technical level (skips the question)")
    ini.add_argument("--description", default="", help="background in the person's own words")
    ini.add_argument("--non-interactive", action="store_true", help="ask nothing; level stays unset")

    commands.add_parser("verify", help="run Kanon's mechanical checks on this repository")

    new = commands.add_parser("new", help="create a work file from the template")
    new.add_argument("topic", help="short topic, used in the file name and title")

    use = commands.add_parser("usage", help="token usage and estimated cost for a time window")
    use.add_argument("--since", help="start: ISO timestamp or git reference (commit time)")
    use.add_argument("--until", help="end: ISO timestamp or git reference (commit time)")
    use.add_argument("--logs", type=Path, help="Claude Code log folder (default: this project's)")
    use.add_argument("--json", action="store_true", help="print JSON")
    use.add_argument("--record", type=Path, metavar="WORK_FILE", help="append a row to this work file's Cost section")
    use.add_argument("--label", help="row label used with --record")
    return parser


def run_init(args) -> int:
    root = init_module.repo_root(Path.cwd())
    if root is None:
        print("kanon init: not inside a Git repository; run 'git init' first")
        return 2
    level, description = args.level or "", args.description
    existing = init_module.has_settings(root)
    if not existing and not args.level and not args.non_interactive:
        level, description = init_module.ask_level()
    approver = args.approver or f"owner@{socket.gethostname().split('.')[0]}"
    person = Person(args.person_id, args.name or getpass.getuser(), level, description, approver)
    try:
        result = init_module.init(root, person)
    except (RuntimeError, ValueError) as error:
        print(f"kanon init: {error}")
        return 2
    for label, items in (("Created", result.created), ("Updated", result.updated), ("Kept", result.kept)):
        for item in items:
            print(f"{label:8} {item}")
    for warning in result.warnings:
        print(f"Warning  {warning}")
    if existing:
        print("Profile kept; change it in kanon/kanon.toml.")
    elif not level:
        print("Technical level not set; agents will ask at first contact.")
    return 0


def run_new(args) -> int:
    try:
        target = init_module.new_work(Path.cwd(), args.topic)
    except (RuntimeError, ValueError, FileExistsError) as error:
        print(f"kanon new: {error}")
        return 2
    print(f"Created  {target.relative_to(init_module.repo_root(Path.cwd()))}")
    return 0


def run_verify() -> int:
    root = init_module.repo_root(Path.cwd())
    if root is None:
        print("kanon verify: not inside a Git repository")
        return 2
    findings, covered = verify.verify_with_exceptions(root)
    for finding in findings:
        print(finding)
    for finding, exception in covered:
        print(f"accepted exception: {finding} (reason: {exception.reason})")
    print(f"kanon verify: {len(findings)} problem(s)" if findings else "kanon verify: all checks passed")
    return 1 if findings else 0


def run_usage(args) -> int:
    repo = init_module.repo_root(Path.cwd()) or Path.cwd()
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
    if args.command == "init":
        return run_init(args)
    if args.command == "new":
        return run_new(args)
    if args.command == "verify":
        return run_verify()
    if args.command == "usage":
        return run_usage(args)
    return 0
