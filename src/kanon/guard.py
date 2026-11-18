"""Kanon guard: a Claude Code PreToolUse hook that blocks deletions of shared locations.

Standalone (standard library only) so `kanon sync` can copy it into `.claude/hooks/` and it runs
even where Kanon is not installed. Reads the hook's JSON on stdin; exits 2 to block, 0 to allow.

Written after 2026-11-18, when a reviewer's cleanup loop deleted every result of
`find /tmp -maxdepth 1 -name 'tmp*'`. `find` includes its starting folder, `/tmp` matched `tmp*`,
and all of `/tmp` was deleted, including the session's commit-signing helper (learning L-004).

How it decides: the command is split into units at `;`, `&&`, `||` and `&` (a pipeline stays one
unit). A unit that deletes (rm, rmdir, unlink, shred, find -delete or -exec rm, Python deletion calls,
git clean) is blocked when one of its paths is a protected location or a pattern covering all of
one. Loops, command substitution and xargs move data between units, so when they appear with a
deletion the whole command is treated as one unit. Text after `bash -c`, `sh -c` and `eval` is
checked as a command of its own.

Limits: it reads command text only. It cannot see what variables hold, what scripts do, or deletions
made by other programs, and patterns with literal text (such as `/tmp/tmp*`) are allowed.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

VERBS = {"rm", "rmdir", "unlink", "shred"}
SEPARATORS = {";", "&&", "||", "&", "\n"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
DATA_FLOW = re.compile(r"\$\(|`|\bxargs\b|(?:^|[\s;])(?:for|while|until)\s")
CODE_DELETION = re.compile(r"shutil\.rmtree|os\.(?:remove|rmdir|unlink|removedirs)|fs\.(?:rm|rmdir|unlink)")
SYSTEM = {"/", "/tmp", "/private/tmp", "/home", "/root", "/etc", "/usr", "/var", "/opt", "/srv", "/mnt",
          "/bin", "/sbin", "/lib", "/boot", "/dev", "/proc", "/sys", "/Users", "/Volumes"}
GLOB = re.compile(r"[*?\[{]")
WILDCARD_ONLY = re.compile(r"^[*?.{},\[\]!]*$")


def _tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def _units(tokens: list[str]) -> list[list[str]]:
    units, current = [], []
    for token in tokens:
        if token in SEPARATORS:
            units.append(current)
            current = []
        else:
            current.append(token)
    units.append(current)
    return [u for u in units if u]


def _verb(token: str) -> str:
    return os.path.basename(token.strip("'\"\\").lstrip("\\"))


def _deletes(unit: list[str], raw: str) -> bool:
    words = [_verb(t) for t in unit]
    if words and words[0] == "git":
        return "clean" in words and any(re.fullmatch(r"-\w*[fx]\w*", t) for t in unit)
    if any(w in VERBS for w in words) or "-delete" in unit:
        return True
    return bool(CODE_DELETION.search(raw))


def resolve(token: str, cwd: str, home: str) -> str | None:
    """The folder a path token reaches, or None when the token is not a usable path.

    A pattern whose first wildcard component is only wildcards (`*`, `?*`, `.*`, `{*,.*}`) reaches
    the folder above it. A pattern with literal text in that component (`*.pyc`) reaches neither.
    """
    token = token.strip("'\"")
    if not token or token.startswith("-") or token in ("{}", "+", ";", "\\;"):
        return None
    for prefix in ("$HOME", "${HOME}", "~"):
        if token == prefix or token.startswith(prefix + "/"):
            token = home + token[len(prefix):]
    if "$" in token or "`" in token:
        return None
    path = token if token.startswith("/") else os.path.join(cwd, token)
    parts = path.split("/")
    for index, part in enumerate(parts):
        if GLOB.search(part):
            if not WILDCARD_ONLY.match(part):
                return None
            path = "/".join(parts[:index]) or "/"
            break
    return os.path.normpath(path)


def protected_paths(cwd: str, home: str, extra: list[str]) -> set[str]:
    paths = set(SYSTEM) | {os.path.normpath(home)}
    for path in [cwd, *extra]:
        if not path:
            continue
        path = os.path.normpath(path)
        while True:
            paths.add(path)
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent
    return paths


def _find_starts(unit: list[str]) -> list[tuple[str, bool]]:
    """Each `find` start folder in the unit, with whether the find has a name or path filter."""
    starts = []
    for index, token in enumerate(unit):
        if _verb(token) == "find" and index + 1 < len(unit) and not unit[index + 1].startswith("-"):
            filtered = any(t in ("-name", "-iname", "-path", "-ipath", "-regex", "-iregex") for t in unit[index:])
            starts.append((unit[index + 1], filtered))
    return starts


def _check_unit(unit: list[str], raw: str, cwd: str, home: str, protected: set[str], project: set[str],
                depth: int) -> str | None:
    for index, token in enumerate(unit):
        word = _verb(token)
        inner = None
        if word in SHELLS and index + 2 < len(unit) and unit[index + 1] == "-c":
            inner = unit[index + 2]
        elif word == "eval" and index + 1 < len(unit):
            inner = " ".join(unit[index + 1:])
        if inner and depth < 3:
            reason = check(inner, cwd, home, sorted(project), depth + 1)
            if reason:
                return reason
    if not _deletes(unit, raw):
        return None
    judged = set()
    for start, filtered in _find_starts(unit):
        folder = resolve(start, cwd, home)
        if folder in protected and not (filtered and folder in project and folder not in SYSTEM):
            return f"a deletion fed by `find {start}`, which includes {folder} itself"
        judged.add(start)
    quoted = re.findall(r"[\"'](/[^\"'\s]*|~[^\"'\s]*)[\"']", raw)
    for token in unit + quoted:
        if _verb(token) in VERBS or token in ("-c", "eval") or _verb(token) == "find" or token in judged:
            continue
        folder = resolve(token, cwd, home)
        if folder in protected:
            return f"a deletion that reaches the protected location {folder}"
    return None


def check(command: str, cwd: str, home: str, extra: list[str] | None = None, depth: int = 0) -> str | None:
    """Reason to block the command, or None to allow it."""
    extra = [e for e in (extra or []) if e]
    protected = protected_paths(cwd, home, extra)
    project = {os.path.normpath(p) for p in [cwd, *extra]}
    tokens = _tokens(command)
    units = [tokens] if DATA_FLOW.search(command) else _units(tokens)
    for unit in units:
        raw = command if len(units) == 1 else " ".join(unit)
        reason = _check_unit(unit, raw, cwd, home, protected, project, depth)
        if reason:
            return reason
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
