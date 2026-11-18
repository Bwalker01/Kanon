"""Kanon guard: a Claude Code PreToolUse hook that blocks deletions of shared locations.

Standalone (standard library only) so `kanon sync` can copy it into `.claude/hooks/` and it runs
even where Kanon is not installed. Reads the hook's JSON on stdin; exits 2 to block, 0 to allow.

Written after 2026-11-18, when a reviewer's cleanup loop ran `find /tmp -maxdepth 1 -name 'tmp*'`
and deleted every result. `find` includes its starting folder, and `/tmp` matched `tmp*`, so the
loop deleted all of `/tmp`, including the session's commit-signing helper.

This is a guard against mistakes, not a sandbox: it inspects the command text and cannot see
through variables, scripts or other programs.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

DELETION = re.compile(
    r"(?:^|[\s;&|(`$])(?:rm|rmdir|unlink|shred)(?=\s|$)|\s-delete\b|shutil\.rmtree|os\.(?:remove|rmdir|unlink)"
    r"|\bgit\s+clean\s+-\w*[fx]"
)
FIND = re.compile(r"(?:^|[\s;&|(`$])find\s+([^\s;&|)`]+)")


def _normalise(token: str, cwd: str, home: str) -> str | None:
    """A literal path from a command token, or None when the token is not a resolvable path."""
    token = token.strip("'\"")
    for prefix in ("$HOME", "${HOME}", "~"):
        if token == prefix or token.startswith(prefix + "/"):
            token = home + token[len(prefix):]
    if "$" in token or "`" in token:
        return None
    if token in (".", "./", "*", "./*", ".*"):
        token = cwd
    elif not token.startswith("/"):
        return None
    token = re.sub(r"(/\*|/\.\*|/\.)+$", "", token)
    return os.path.normpath(token) if token else "/"


def protected_paths(cwd: str, home: str, extra: list[str]) -> set[str]:
    paths = {"/", "/tmp", "/home", "/root", "/etc", "/usr", "/var", home}
    for path in [cwd, *extra]:
        if not path:
            continue
        paths.add(os.path.normpath(path))
        if path.startswith("/tmp/"):
            parts = os.path.normpath(path).split("/")
            paths.update("/".join(parts[:i]) for i in range(3, len(parts)))
    return {p for p in paths if p}


def check(command: str, cwd: str, home: str, extra: list[str] | None = None) -> str | None:
    """Reason to block the command, or None to allow it."""
    if not DELETION.search(command):
        return None
    protected = protected_paths(cwd, home, extra or [])
    for match in FIND.finditer(command):
        start = _normalise(match.group(1), cwd, home)
        if start in protected:
            return (f"a deletion fed by `find {match.group(1)}`, which includes {start} itself "
                    "and everything under it")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    quoted = re.findall(r"[\"'](/[^\"'\s]*|~[^\"'\s]*)[\"']", command)
    for token in tokens + quoted:
        path = _normalise(token, cwd, home)
        if path in protected:
            return f"a deletion that reaches the protected location {path}"
    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    command = str((event.get("tool_input") or {}).get("command", ""))
    cwd = str(event.get("cwd") or os.getcwd())
    extra = [os.environ.get("CLAUDE_PROJECT_DIR", ""), str(event.get("scratchpad_dir") or "")]
    reason = check(command, cwd, os.path.expanduser("~"), extra)
    if reason:
        print(f"Blocked by the Kanon guard: {reason}. Delete only what you created, by its exact path "
              "(for example a folder made with `mktemp -d`), and never with find or globs over shared folders.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
