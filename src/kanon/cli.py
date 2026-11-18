"""Command-line entry point for Kanon."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import json
from pathlib import Path

from kanon import __version__, usage, verify
from kanon import init as init_module
from kanon import profile as profiles
from kanon import sync as sync_module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kanon",
        description="Context engine for AI-assisted projects.",
    )
    parser.add_argument("--version", action="version", version=f"kanon {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="<command>")

    ini = commands.add_parser("init", help="prepare this Git repository for Kanon")
    ini.add_argument("--approver", action="append", default=[], metavar="GITHUB_USER",
                     help="GitHub username allowed to approve (repeatable; default: your profile's)")
    ini.add_argument("--non-interactive", action="store_true", help="ask nothing")

    commands.add_parser("sync", help="regenerate the agent files Kanon keeps out of Git")

    commands.add_parser("desk", help="rebuild your Desk: decisions, actions and reviews waiting on you")

    pro = commands.add_parser("profile", help="show or set your personal profile (stored outside every repository)")
    pro.add_argument("--github", help="your GitHub username")
    pro.add_argument("--name", help="your name")
    pro.add_argument("--level", choices=init_module.PERSON_LEVELS, help="technical level")
    pro.add_argument("--description", help="your background, in your own words")
    pro.add_argument("--preference", action="append", default=None, help="a working preference (repeatable; replaces the list)")
    pro.add_argument("--print-env", action="store_true", help="print the profile as a KANON_PROFILE value for cloud environments")

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
    try:
        person = profiles.load()
    except ValueError as error:
        print(f"kanon init: {error}")
        return 2
    if person is None and not args.non_interactive:
        level, description = init_module.ask_level()
        github = init_module.ask("Your GitHub username (Enter to skip): ")
        person = profiles.Profile(github=github, level=level, description=description)
        if level or github:
            print(f"Saved    {profiles.save(person)} (outside the repository)")
    approvers = args.approver or ([person.github] if person and person.github else [])
    if not approvers and not init_module.has_settings(root):
        print("kanon init: name at least one approver with --approver GITHUB_USER")
        return 2
    try:
        result = init_module.init(root, approvers)
    except (RuntimeError, ValueError) as error:
        print(f"kanon init: {error}")
        return 2
    for label, items in (("Created", result.created), ("Updated", result.updated), ("Kept", result.kept)):
        for item in items:
            print(f"{label:8} {item}")
    for warning in result.warnings:
        print(f"Note     {warning}")
    return 0


def run_sync() -> int:
    root = init_module.repo_root(Path.cwd())
    if root is None or not init_module.has_settings(root):
        print("kanon sync: Kanon is not set up here; run kanon init first")
        return 2
    result = sync_module.sync(root)
    for label, items in (("Written", result.written), ("Unchanged", result.unchanged)):
        for item in items:
            print(f"{label:9} {item}")
    for item in result.refused:
        reason = "its Kanon block is damaged (see note)" if item == ".gitignore" else "exists and was not written by Kanon"
        print(f"Refused   {item}: {reason}")
    for note in result.notes:
        print(f"Note      {note}")
    return 1 if result.refused else 0


def run_desk() -> int:
    root = init_module.repo_root(Path.cwd())
    if root is None or not init_module.has_settings(root):
        print("kanon desk: Kanon is not set up here; run kanon init first")
        return 2
    from kanon import desk as desk_module
    try:
        sync_module.ensure_gitignore(root)
    except ValueError as error:
        print(f"kanon desk: {error}")
        return 2
    result = desk_module.write(root)
    print(f"Desk for {result.person} on {result.branch}: {len(result.decisions)} decisions, "
          f"{len(result.actions)} actions, {len(result.reviews)} late reviews.")
    print("Open kanon/local/desk.html (or kanon/local/DESK.md).")
    for note in result.notes:
        print(f"Note  {note}")
    return 0


def run_profile(args) -> int:
    try:
        current = profiles.load() or profiles.Profile()
    except ValueError as error:
        print(f"kanon profile: {error}")
        return 2
    changes = {k: v for k, v in (("github", args.github), ("name", args.name), ("level", args.level),
                                 ("description", args.description)) if v is not None}
    if args.preference is not None:
        changes["preferences"] = tuple(args.preference)
    if changes:
        if current.source.startswith("KANON_PROFILE environment"):
            print("kanon profile: your profile comes from KANON_PROFILE; change the variable instead "
                  "(use --print-env to produce it)")
            return 2
        updated = profiles.Profile(**{**{f: getattr(current, f) for f in
                                         ("github", "name", "level", "description", "preferences")}, **changes})
        try:
            print(f"Saved {profiles.save(updated)} (outside the repository). Run kanon sync to apply it.")
        except ValueError as error:
            print(f"kanon profile: {error}")
            return 2
        current = updated
    print(profiles.as_env(current) if args.print_env else profiles.render(current), end="")
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
    if args.command == "sync":
        return run_sync()
    if args.command == "desk":
        return run_desk()
    if args.command == "profile":
        return run_profile(args)
    if args.command == "new":
        return run_new(args)
    if args.command == "verify":
        return run_verify()
    if args.command == "usage":
        return run_usage(args)
    return 0
