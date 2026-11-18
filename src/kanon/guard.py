"""Kanon guard: a Claude Code PreToolUse hook that blocks deletions of shared locations.

Standalone (standard library only) so `kanon sync` can copy it into `.claude/hooks/` and it runs
even where Kanon is not installed. Reads the hook's JSON on stdin; exits 2 to block, 0 to allow.

Written after 2026-11-18, when a reviewer's cleanup loop deleted every result of
`find /tmp -maxdepth 1 -name 'tmp*'`. `find` includes its starting folder, `/tmp` matched `tmp*`,
and all of `/tmp` was deleted, including the session's commit-signing helper (learning L-004).

How it decides: the command is split into units at `;`, `&&`, `||`, `&` and newlines (a pipeline
stays one unit, and each of its stages is checked), following `cd` from unit to unit. Units that only read (`ls`, `echo`, `git` other than
`git clean`, and similar) are ignored. A unit that deletes (rm, rmdir, unlink, shred, find -delete or
-exec rm, Python deletion calls, git clean) is blocked when one of its paths is a protected location
or a pattern covering all of one. When loops, command substitution or xargs carry paths between
units, the paths of every non-reading unit are judged. Text run by `bash -c` (any flags) or `eval`
is checked as a command of its own.

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
CODE_DELETION = re.compile(r"shutil\.rmtree|os\.(?:remove|rmdir|unlink|removedirs)|fs\.(?:rm|rmdir|unlink)"
                           r"|\.rmdir\(|\.unlink\(|\brmtree\b")
# Commands that only read or change folder: their arguments are never deletion targets.
# Never list a command that runs other programs (uv, make, pip, pytest): `uv run rm` must be judged.
PASSIVE = {"cd", "ls", "echo", "printf", "pwd", "cat", "grep", "head", "tail", "wc", "date",
           "mkdir", "touch", "test", "[", "true", "false", "sleep"}
SYSTEM = {"/", "/tmp", "/private/tmp", "/home", "/root", "/etc", "/usr", "/var", "/opt", "/srv", "/mnt",
          "/bin", "/sbin", "/lib", "/boot", "/dev", "/proc", "/sys", "/Users", "/Volumes"}
GLOB = re.compile(r"[*?\[{]")
WILDCARD_ONLY = re.compile(r"^[*?.{},\[\]!]*$")


def _tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"  # a newline outside quotes separates commands, as in the shell
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        raw = list(lexer)
    except ValueError:
        return command.replace("\n", " \n ").split(" ")
    tokens = []
    for token in raw:
        if "\n" in token and not token.strip(";&|()\n"):
            rest = token.replace("\n", "")
            if rest:
                tokens.append(rest)
            if rest != "|":  # `a |` followed by a newline continues the pipeline
                tokens.append("\n")
        else:
            tokens.append(token)
    return [t for t in tokens if t]


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


def _stages(unit: list[str]) -> list[list[str]]:
    stages, current = [], []
    for token in unit:
        if token == "|":
            stages.append(current)
            current = []
        else:
            current.append(token)
    stages.append(current)
    return stages


def _deletes(unit: list[str], raw: str = "") -> bool:
    """True when any stage of the unit's pipeline deletes (K-262: a git stage hides nothing)."""
    for stage in _stages(unit):
        _, word = _first(stage)
        words = [_verb(t) for t in stage]
        if word == "git":
            if "clean" in words and any(re.fullmatch(r"-\w*[fx]\w*", t) or t == "--force" for t in stage):
                return True
            continue
        if any(w in VERBS for w in words) or "-delete" in stage or CODE_DELETION.search(" ".join(stage)):
            return True
    return False


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
    path = re.sub(r"^/+", "/", path)  # normpath keeps a leading `//`
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


def _first(unit: list[str]) -> tuple[int, str]:
    """Index and name of the unit's command, skipping `(`, `{` and leading VAR=value assignments."""
    for index, token in enumerate(unit):
        if token not in ("(", "{") and not re.fullmatch(r"[A-Za-z_]\w*=.*", token):
            return index, _verb(token)
    return len(unit), ""


def _passive(unit: list[str]) -> bool:
    """True when every stage of the unit's pipeline only reads, so none of its paths is deleted."""
    for stage in _stages(unit):
        _, word = _first(stage)
        if word == "git":
            if _deletes(stage):
                return False
        elif word not in PASSIVE:
            return False
    return True


def _inner_commands(unit: list[str]) -> list[str]:
    """Command text run by `bash -c` (with any combined flags such as -lc) or `eval`."""
    inner = []
    for index, token in enumerate(unit):
        word = _verb(token)
        if word in SHELLS:
            j = index + 1
            while j < len(unit) - 1 and unit[j].startswith(("-", "+")):
                flag = unit[j]
                if flag.startswith("--"):
                    j += 1  # a long option such as --norc (K-263)
                    continue
                if "c" in flag[1:]:
                    inner.append(unit[j + 1])
                    break
                j += 2 if flag[-1] in "oO" else 1  # -o and -O take an argument
        elif word == "eval" and index + 1 < len(unit):
            inner.append(" ".join(unit[index + 1:]))
    return inner


def _path_reason(unit: list[str], cwd: str, home: str, protected: set[str], project: set[str]) -> str | None:
    skip = set()
    for index, token in enumerate(unit):
        if _verb(token) == "find" and index + 1 < len(unit) and not unit[index + 1].startswith("-"):
            start = unit[index + 1]
            filtered = any(t in ("-name", "-iname", "-path", "-ipath", "-regex", "-iregex") for t in unit[index:])
            folder = resolve(start, cwd, home)
            if folder in protected and not (filtered and folder in project and folder not in SYSTEM):
                return f"a deletion fed by `find {start}`, which includes {folder} itself"
            skip.add(index + 1)
    for index, token in enumerate(unit):
        if index in skip or _verb(token) in VERBS or _verb(token) == "find":
            continue
        for candidate in [token, *re.findall(r"[\"'](/[^\"'\s]*|~[^\"'\s]*)[\"']", token)]:
            folder = resolve(candidate, cwd, home)
            if folder in protected:
                return f"a deletion that reaches the protected location {folder}"
    return None


def check(command: str, cwd: str, home: str, extra: list[str] | None = None, depth: int = 0) -> str | None:
    """Reason to block the command, or None to allow it."""
    extra = [e for e in (extra or []) if e]
    protected = protected_paths(cwd, home, extra)
    project = {os.path.normpath(p) for p in [cwd, *extra]}
    units = _units(_tokens(command))
    for unit in units:
        for inner in _inner_commands(unit):
            if depth < 3:
                reason = check(inner, cwd, home, extra, depth + 1)
                if reason:
                    return reason
    # Follow `cd` between units; ignore units that only read; note which units delete.
    active, here = [], cwd
    for unit in units:
        index, word = _first(unit)
        if word == "cd":
            target = resolve(unit[index + 1], here, home) if index + 1 < len(unit) else home
            if target:
                here = target
                protected |= protected_paths(os.path.dirname(here), home, [])  # parents only (K-265)
            continue
        if not _passive(unit):
            active.append((unit, here))
    deleting = [(u, c) for u, c in active if _deletes(u, " ".join(u))]
    if not deleting:
        return None
    # Loops, substitution and xargs carry paths between units, so every active unit is judged.
    targets = active if DATA_FLOW.search(command) else deleting
    for unit, here in targets:
        reason = _path_reason(unit, here, home, protected, project)
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
