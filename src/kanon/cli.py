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

    sta = commands.add_parser("status", help="print the project's open work and what waits on whom (writes nothing)")
    sta.add_argument("--json", action="store_true", help="print JSON")

    pro = commands.add_parser("profile", help="show or set your personal profile (stored outside every repository)")
    pro.add_argument("--github", help="your GitHub username")
    pro.add_argument("--name", help="your name")
    pro.add_argument("--level", choices=init_module.PERSON_LEVELS, help="technical level")
    pro.add_argument("--description", help="your background, in your own words")
    pro.add_argument("--preference", action="append", default=None, help="a working preference (repeatable; replaces the list)")
    pro.add_argument("--print-env", action="store_true", help="print the profile as a KANON_PROFILE value for cloud environments")

    commands.add_parser("verify", help="run Kanon's mechanical checks on this repository")

    app = commands.add_parser("approve", help="approve a work file's plan or result (run by the approver)")
    app.add_argument("work", help="work file name without its date, or its path")
    app.add_argument("--item", help="one item of a work file with several, such as P1-05; the status stays as it is")
    app.add_argument("--plan", action="store_true", help="approve the plan; the build may start")
    req = commands.add_parser("request-changes", help="request changes to a work file (run by the approver)")
    req.add_argument("work", help="work file name without its date, or its path")
    req.add_argument("changes", help="what must change")
    req.add_argument("--item", help="one item of a work file with several, such as P1-05; the status stays as it is")
    req.add_argument("--plan", action="store_true", help="the changes concern the plan")
    bra = commands.add_parser("branch", help="item and plan branches: start, merge after review, status")
    actions = bra.add_subparsers(dest="branch_command", metavar="<action>", required=True)
    b_start = actions.add_parser("start", help="create and switch to the item branch (and the plan branch if missing)")
    b_start.add_argument("work", help="work file name without its date")
    b_start.add_argument("item", nargs="?", help="item ID such as P1-09; omit to switch to the plan branch")
    b_merge = actions.add_parser("merge", help="merge a reviewed item into the plan branch (merge commit, no rewrite)")
    b_merge.add_argument("work", help="work file name without its date")
    b_merge.add_argument("item", help="item ID such as P1-09")
    b_status = actions.add_parser("status", help="list items, their branches, review state and merges")
    b_status.add_argument("work", help="work file name without its date")
    actions.add_parser("check-merge", help="used by the pre-merge-commit hook")

    gh = commands.add_parser("github", help="GitHub mode: Kanon acts only as its own GitHub App")
    gh_actions = gh.add_subparsers(dest="github_command", metavar="<action>", required=True)
    g_setup = gh_actions.add_parser("setup", help="create the App with GitHub's manifest flow (on your own computer)")
    g_setup.add_argument("--org", help="create the App for this organisation instead of your account")
    gh_actions.add_parser("check", help="sign in as the App and report its installation and permissions")
    g_pr = gh_actions.add_parser("pr", help="push the plan branch and open its pull request as a draft, or update it")
    g_pr.add_argument("work", help="work file name without its date")
    g_pr.add_argument("--base", default="main", help="branch to merge into (default main)")
    for action, text in (("ready", "mark the work's pull request ready for review, as the App (the check runs)"),
                         ("draft", "return the work's pull request to draft, as the App")):
        g_state = gh_actions.add_parser(action, help=text)
        g_state.add_argument("work", help="work file name without its date")
    g_notes = gh_actions.add_parser("notes", help="post reviewer notes on the pull request as a comment-only review")
    g_notes.add_argument("work", help="work file name without its date")
    g_notes.add_argument("file", type=Path, help="text file holding the notes")
    g_sync = gh_actions.add_parser("sync", help="read the pull request back: merged, closed or changes requested")
    g_sync.add_argument("work", help="work file name without its date")
    gh_actions.add_parser("protect", help="require a code owner's review on main (run by you, with your own gh login)")

    tra = commands.add_parser("transcribe", help="record an approver's decision given in chat, in their exact words")
    tra.add_argument("work", help="work file name without its date, or its path")
    tra.add_argument("--quote", required=True, help="the approver's exact words")
    tra.add_argument("--changes", help="the requested changes, when the reply asks for changes")
    tra.add_argument("--item", help="one item of a work file with several, such as P1-05; the status stays as it is")
    tra.add_argument("--plan", action="store_true", help="the decision concerns the plan")

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


def run_status(args: argparse.Namespace) -> int:
    root = init_module.repo_root(Path.cwd())
    if root is None or not init_module.has_settings(root):
        print("kanon status: Kanon is not set up here (no kanon/kanon.toml); run kanon init first")
        return 2
    from kanon import desk as desk_module
    result = desk_module.build(root, everyone=True)
    if args.json:
        print(json.dumps(desk_module.status_data(result), indent=2))  # ASCII by default
        return 0
    import sys
    # A piped stdout on Windows uses the ANSI code page (cp1252), which cannot encode every title.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    print(desk_module.render_terminal(result), end="")
    return 0


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


def _work_path(root: Path, work: str) -> str:
    candidate = Path(work)
    if candidate.suffix == ".md" and (root / candidate).is_file():
        return candidate.as_posix()
    matches = sorted((root / "kanon" / "work").glob(f"????-??-??-{work}.md"))
    if len(matches) != 1:
        raise ValueError(f"no single work file named '{work}' in kanon/work")
    return matches[0].relative_to(root).as_posix()


def run_decision(args) -> int:
    import tomllib
    from kanon import approve
    name = args.command
    if name in ("approve", "request-changes") and approve.in_assistant():
        print(f"kanon {name}: refused inside an assistant session; the approver runs it in their own terminal, "
              "or the assistant records their words with kanon transcribe")
        return 2
    root = init_module.repo_root(Path.cwd())
    if root is None or not init_module.has_settings(root):
        print(f"kanon {name}: Kanon is not set up here; run kanon init first")
        return 2
    try:
        person = profiles.load()
    except ValueError as error:
        print(f"kanon {name}: {error}")
        return 2
    if person is None or not person.github:
        print(f"kanon {name}: no profile with a GitHub username; run kanon profile --github <username>")
        return 2
    settings = tomllib.loads((root / "kanon" / "kanon.toml").read_text(encoding="utf-8"))
    approvers = settings.get("kanon", {}).get("approvers", [])
    changes = args.changes if name in ("request-changes", "transcribe") else None
    quote = args.quote if name == "transcribe" else None
    try:
        rel = _work_path(root, args.work)
        row = approve.record(root, rel, person.github, approvers, changes=changes, plan=args.plan, quote=quote,
                             item=args.item)
    except (ValueError, PermissionError) as error:
        print(f"kanon {name}: {error}")
        return 2
    print(f"Recorded in {rel}:\n{row}")
    return 0


def run_branch(args) -> int:
    from kanon import branch
    root = init_module.repo_root(Path.cwd())
    if root is None:
        print("kanon branch: not inside a Git repository")
        return 2
    try:
        if args.branch_command == "start":
            print(f"On branch {branch.start(root, args.work, args.item)}")
        elif args.branch_command == "merge":
            commit = branch.merge(root, args.work, args.item)
            print(f"Merged {args.item} into {branch.plan_branch(args.work)} ({commit})")
        elif args.branch_command == "status":
            for row in branch.status(root, args.work):
                state = "merged" if row.merged else (row.branch or "no branch")
                print(f"{row.item:8} {state:40} {row.review}")
        else:
            reason = branch.check_merge(root)
            if reason:
                print(f"Refused by Kanon: {reason}. Review the item, record it on the plan branch, then merge.")
                return 1
    except branch.BranchError as error:
        print(f"kanon branch: {error}")
        return 2
    return 0


def run_github(args) -> int:
    from kanon import approve, github
    name = args.github_command
    if name in ("setup", "protect") and approve.in_assistant():
        print(f"kanon github {name}: refused inside an assistant session; run it yourself in your own terminal")
        return 2
    root = init_module.repo_root(Path.cwd())
    if root is None or not init_module.has_settings(root):
        print(f"kanon github {name}: Kanon is not set up here; run kanon init first")
        return 2
    try:
        if name == "setup":
            app = github.setup(root, args.org)
            print(f"Created {app['slug']} (ID {app['id']}); key saved to {app['key']}; kanon/kanon.toml updated.")
            print("Install the App on this repository in the page that opened, then run kanon github check.")
        elif name == "check":
            print("\n".join(github.check(root)))
        elif name == "pr":
            pull = github.open_pull_request(root, args.work, args.base)
            print(f"Pull request #{pull['number']}: {pull['html_url']}")
        elif name in ("ready", "draft"):
            session = github.sign_in(root)
            print(github.set_draft(session, github.find_pull(root, session, args.work), name == "draft"))
        elif name == "notes":
            entry = github.read_cache(root).get(args.work)
            if not entry:
                raise github.GitHubError(f"no pull request recorded for {args.work}; run kanon github pr first")
            github.comment_review(github.sign_in(root), entry["number"], args.file.read_text(encoding="utf-8"))
            print(f"Notes posted on pull request #{entry['number']}")
        elif name == "sync":
            print("\n".join(github.sync(root, args.work)) or "nothing new")
        else:
            import tomllib
            approvers = tomllib.loads((root / "kanon/kanon.toml").read_text(encoding="utf-8"))["kanon"]["approvers"]
            print("\n".join(github.protect(root, approvers)))
    except (github.GitHubError, OSError, ValueError) as error:
        print(f"kanon github {name}: {error}")
        return 2
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
    if args.command == "status":
        return run_status(args)
    if args.command == "profile":
        return run_profile(args)
    if args.command == "new":
        return run_new(args)
    if args.command == "verify":
        return run_verify()
    if args.command == "usage":
        return run_usage(args)
    if args.command == "github":
        return run_github(args)
    if args.command == "branch":
        return run_branch(args)
    if args.command in ("approve", "request-changes", "transcribe"):
        return run_decision(args)
    return 0
