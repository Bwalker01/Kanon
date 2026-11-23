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

For the reviewer subagent (`agent_type` "kritos-reviewer" in the hook input), commands that would
change the project (git writes, file writers, redirection, `sed -i`, Kanon's writing commands) are
also blocked (K-29); writes to the scratchpad and to temporary folders outside the project are allowed.

Paths follow the shell's rules (POSIX). On Windows, where Claude Code runs Bash through Git Bash,
`\\` is also a separator, Windows paths (`C:\\Users\\x`, `C:/Users/x`) are read in Git Bash form
(`/c/Users/x`), paths are compared without regard to case, and the project, home and temporary
folders are protected under both their long and 8.3 short names. Drive roots and the Windows system
folders are protected as well.

Limits: it reads command text only. It cannot see what variables hold, what scripts do, or deletions
made by other programs, and patterns with literal text (such as `/tmp/tmp*`) are allowed. On Windows,
a path that mixes long and 8.3 short folder names is not recognised.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import shlex
import sys
import tempfile

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
WINDOWS = os.name == "nt"  # read at call time, so tests can set it on any platform
DRIVE = re.compile(r"^([A-Za-z]):(?:/|$)")
GIT_BASH_DRIVE = re.compile(r"^/([a-z])(?=/|$)")
WINDOWS_SYSTEM = ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramData")
GLOB = re.compile(r"[*?\[{]")
WILDCARD_ONLY = re.compile(r"^[*?.{},\[\]!]*$")


def _posix(path: str) -> str:
    """On Windows, a path in Git Bash form: `\\` becomes `/`, and `C:/x` becomes `/c/x`. Elsewhere unchanged."""
    if not WINDOWS:
        return path
    path = path.replace("\\", "/")
    match = DRIVE.match(path)
    if not match:
        return path
    return f"/{match.group(1).lower()}/{path[match.end():]}".rstrip("/") or "/"


def _norm(path: str) -> str:
    """A path normalised by the shell's rules, folded to lower case on Windows (case-insensitive files)."""
    path = posixpath.normpath(_posix(path))
    if path.startswith("//"):
        path = "/" + path.lstrip("/")  # normpath keeps a leading `//`
    return path.lower() if WINDOWS else path


def _join(here: str, token: str) -> str:
    """The path a token names from folder `here`, normalised."""
    token = _posix(token)
    return _norm(token if token.startswith("/") else posixpath.join(here, token))


def _short_name(path: str) -> str | None:
    """The 8.3 short name Windows gives an existing path, or None."""
    try:
        import ctypes
        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.windll.kernel32.GetShortPathNameW(path, buffer, len(buffer))
    except (AttributeError, OSError, ValueError):
        return None
    return buffer.value if 0 < length < len(buffer) else None


def _forms(path: str) -> set[str]:
    """The path normalised, plus on a Windows computer its long and 8.3 short names."""
    forms = {_norm(path)}
    if WINDOWS and os.name == "nt":
        normal = _norm(path)
        native = GIT_BASH_DRIVE.sub(lambda m: m.group(1) + ":", normal) or normal
        for other in (os.path.realpath(native), _short_name(native)):
            if other:
                forms.add(_norm(other))
    return forms


_SYSTEM_CACHE: dict[bool, frozenset[str]] = {}


def _system_paths() -> frozenset[str]:
    """Shared locations that are always protected; on Windows also drive roots, system and temp folders."""
    if WINDOWS not in _SYSTEM_CACHE:
        paths = {_norm(p) for p in SYSTEM}
        if WINDOWS:
            paths |= {f"/{letter}" for letter in "abcdefghijklmnopqrstuvwxyz"}
            names = [os.environ.get(n, "") for n in WINDOWS_SYSTEM]
            names += [tempfile.gettempdir(), os.environ.get("TEMP", ""), os.environ.get("TMP", "")]
            for name in names:
                if name:
                    paths |= _forms(name)
            profile = os.environ.get("USERPROFILE", "")
            if profile:
                paths |= {posixpath.dirname(f) for f in _forms(profile)}  # the folder holding every user's home
        _SYSTEM_CACHE[WINDOWS] = frozenset(paths)
    return _SYSTEM_CACHE[WINDOWS]


def _quoted_paths(token: str) -> list[str]:
    """Absolute paths quoted inside a token, such as code passed to `python -c` (spaces allowed)."""
    drive = r"|[A-Za-z]:[\\/][^\"']*" if WINDOWS else ""
    return re.findall(rf"[\"'](/[^\"']*|~[^\"']*{drive})[\"']", token)


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
    name = posixpath.basename(_posix(token.strip("'\"\\").lstrip("\\")))
    return name[:-4] if name.lower().endswith(".exe") else name


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
    token = _posix(token)
    path = token if token.startswith("/") else posixpath.join(cwd, token)
    path = re.sub(r"^/+", "/", path)  # normpath keeps a leading `//`
    parts = path.split("/")
    for index, part in enumerate(parts):
        if GLOB.search(part):
            if not WILDCARD_ONLY.match(part):
                return None
            path = "/".join(parts[:index]) or "/"
            break
    return _norm(path)


def protected_paths(cwd: str, home: str, extra: list[str]) -> set[str]:
    paths = set(_system_paths()) | _forms(home)
    for root in [cwd, *extra]:
        if not root:
            continue
        for path in _forms(root):
            while True:
                paths.add(path)
                parent = posixpath.dirname(path)
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
            if folder in protected and not (filtered and folder in project and folder not in _system_paths()):
                return f"a deletion fed by `find {start}`, which includes {folder} itself"
            skip.add(index + 1)
    for index, token in enumerate(unit):
        if index in skip or _verb(token) in VERBS or _verb(token) == "find":
            continue
        for candidate in [token, *_quoted_paths(token)]:
            folder = resolve(candidate, cwd, home)
            if folder in protected:
                return f"a deletion that reaches the protected location {folder}"
    return None


def check(command: str, cwd: str, home: str, extra: list[str] | None = None, depth: int = 0) -> str | None:
    """Reason to block the command, or None to allow it."""
    cwd, home = _norm(cwd), _norm(home)
    extra = [_norm(e) for e in (extra or []) if e]
    protected = protected_paths(cwd, home, extra)
    project = {cwd, *extra}
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
                protected |= protected_paths(posixpath.dirname(here), home, [])  # parents only (K-265)
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


REVIEWER = "kritos-reviewer"
GIT_WRITES = {"add", "commit", "push", "reset", "checkout", "switch", "restore", "merge", "rebase", "cherry-pick",
              "revert", "tag", "rm", "mv", "clean", "apply", "am", "pull", "init", "update-ref"}
GIT_READ_FORMS = {"stash": {"list", "show"}, "branch": {"--list", "-l", "--show-current", "-a", "-r", "-v", "-vv", "--contains", "--merged", "--no-merged", "--no-contains", "--points-at"},
                  "config": {"--get", "--get-all", "--list", "-l", "--get-regexp"}, "worktree": {"add", "list", "remove", "prune"}}
FILE_WRITERS = {"cp", "mv", "rm", "rmdir", "touch", "mkdir", "chmod", "chown", "ln", "tee", "truncate", "install",
                "dd", "patch", "unlink", "shred", "rsync"}
KANON_WRITES = {"init", "sync", "new", "approve", "request-changes", "transcribe", "profile", "desk"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
CODE_WRITES = re.compile(r"\bopen\([^)]*['\"][wax]\+?b?['\"]|\.write_(?:text|bytes)\(|\bwriteFileSync\b"
                         r"|shutil\.(?:copy\w*|move)\(")
DESTINATION_ONLY = {"cp", "mv", "rsync", "install", "ln"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _inside(path: str, folders: list[str]) -> bool:
    return any(path == f or path.startswith(f.rstrip("/") + "/") for f in folders if f)


def _without_heredoc_bodies(command: str) -> str:
    """The command with heredoc bodies removed: they are data, not commands (K-341)."""
    lines, out, waiting = command.split("\n"), [], []
    for line in lines:
        if waiting:
            if line.strip() == waiting[0]:
                waiting.pop(0)
            continue
        out.append(line)
        waiting += [m.group(2) for m in HEREDOC.finditer(line)]
    return "\n".join(out)


OPERATORS = sorted(["&>>", "<<<", ">>", "&&", "||", "&>", ">|", "<>", "<<", ";;", ">", "<", "|", ";", "&", "(", ")", "\n"],
                   key=len, reverse=True)
PUNCTUATION = set("<>|;&()\n")


def _split_operators(token: str) -> list[str]:
    """`);` or `)>` as single operators (K-360)."""
    out = []
    while token:
        match = next((op for op in OPERATORS if token.startswith(op)), token[0])
        out.append(match)
        token = token[len(match):]
    return out


def _shell_words(text: str) -> list[str]:
    """Words and operators as the shell sees them: a `>` inside quotes stays part of its word (K-341)."""
    text = re.sub(r"\$\(\([^()]*\)\)", "0", text)  # arithmetic such as $((3 > 2)) holds no redirection
    lexer = shlex.shlex(text, posix=True, punctuation_chars="<>|;&()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        raw = list(lexer)
    except ValueError:
        return text.split()
    words = []
    for token in raw:
        words += _split_operators(token) if token and set(token) <= PUNCTUATION else [token]
    return words


def _git_parts(args: list[str]) -> tuple[str | None, str, list[str]]:
    """(-C folder, subcommand, its arguments), skipping git's own options and their values (K-343)."""
    folder, index = None, 0
    while index < len(args) and args[index].startswith("-"):
        option = args[index]
        if option in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") and index + 1 < len(args):
            if option == "-C":
                folder = args[index + 1]
            index += 2
            continue
        index += 1
    return folder, (args[index] if index < len(args) else ""), args[index + 1:]


WRAPPERS = {"nohup", "time", "command", "sudo", "nice", "timeout", "exec", "builtin"}


def _command(stage: list[str]) -> tuple[str, list[str]]:
    """The program a stage runs, looking through env, uv run, python -m and similar wrappers (K-344, K-367)."""
    index, word = _first(stage)
    args = stage[index + 1:]
    while True:
        if word == "env":
            while args and (args[0].startswith("-") or re.fullmatch(r"[A-Za-z_]\w*=.*", args[0])):
                args = args[2:] if args[0] in ("-u", "-C", "--unset", "--chdir", "-S") else args[1:]
        elif word in WRAPPERS or word == "xargs":
            while args and args[0].startswith("-"):
                args = args[2:] if word in ("timeout", "nice", "xargs") and args[0] in ("-n", "-s", "-k", "-P", "-I", "-L", "-d", "-a") else args[1:]
            if word == "timeout" and args and re.fullmatch(r"[\d.]+[smhd]?", args[0]):
                args = args[1:]
        elif word == "uv" and args[:1] == ["run"]:
            args = args[1:]
            while args and args[0].startswith("-"):
                args = args[2:] if args[0] in ("--directory", "--project", "--with", "--python", "-p") else args[1:]
        elif word.startswith("python") and args[:1] == ["-m"]:
            args = args[1:]
            if args and args[0] in ("kanon", "kanon.cli"):
                args = ["kanon", *args[1:]]
        else:
            return word, args
        word, args = (_verb(args[0]), args[1:]) if args else ("", [])


def reviewer_write(command: str, cwd: str, home: str, project: str, scratch: list[str]) -> str | None:
    """Reason to block a reviewer's command that would change the project (K-29), or None.

    Writes to the scratchpad and to folders outside the project are allowed: reviewers use them for
    probes. Paths held in variables are followed when assigned in the same command (`D=$(mktemp -d)`
    counts as a temporary folder) and otherwise treated as outside the project. Writes made by
    programs the command starts cannot be seen.
    """
    cwd, home = _norm(cwd), _norm(home)
    keep_out = sorted(_forms(project or cwd))
    allowed = sorted(set().union(*(_forms(p) for p in scratch if p)))
    names: dict[str, str | None] = {"CLAUDE_PROJECT_DIR": _norm(project or cwd), "PWD": cwd, "HOME": home}

    def expand(token: str) -> str | None:
        def value(match):
            known = names.get(match.group(1) or match.group(2))
            if known is None:
                raise KeyError
            return known
        try:
            expanded = re.sub(r"\$\{(\w+)\}|\$(\w+)", value, token)
        except KeyError:
            return None  # an unknown variable: its value cannot be seen
        return None if "$" in expanded or "`" in expanded else expanded

    def in_project(token: str, here: str) -> bool:
        token = expand(token.strip("'\""))
        if not token or "$(" in token or "`" in token:
            return False
        target = _join(here, token)
        return _inside(target, keep_out) and not _inside(target, allowed)

    def judge(text: str, depth: int = 0) -> str | None:
        here = cwd
        words = _shell_words(_without_heredoc_bodies(text))
        for unit in _units(words):
            for stage in _stages(unit):
                assign = [t for t in stage if re.fullmatch(r"[A-Za-z_]\w*=.*", t)]
                for token in assign:
                    name, value = token.split("=", 1)
                    names[name] = "/tmp/mktemp" if value.startswith("$(mktemp") or value.startswith("`mktemp") \
                        else expand(value)
                word, args = _command(stage)
                args = [a for i, a in enumerate(args) if a != "<" and (i == 0 or args[i - 1] != "<")]
                if "--help" in args or "-h" in args[:1]:
                    continue
                if word in SHELLS and depth < 3:
                    for inner in _inner_commands([word, *args]):
                        reason = judge(inner, depth + 1)
                        if reason:
                            return reason
                if word == "cd":
                    target = expand(args[0].strip("'\"")) if args else home
                    if target:
                        here = _join(here, target)
                    else:
                        here = _norm("/tmp/unknown")
                    continue
                if word == "find":
                    start = next((a for a in args if not a.startswith("-")), ".")
                    if any(a in ("-delete", "-fprint", "-fprint0", "-fprintf", "-fls") for a in args) and in_project(start, here):
                        return "the reviewer may not change project files (`find -delete` or `-fprint`)"
                if word == "find" and any(a in ("-exec", "-execdir", "-ok") for a in args):
                    start = next((a for a in args if not a.startswith("-")), ".")
                    position = next(i for i, a in enumerate(args) if a in ("-exec", "-execdir", "-ok"))
                    inner = args[position + 1:]
                    if inner and _verb(inner[0]) in FILE_WRITERS | {"sed", "perl"} and in_project(start, here):
                        return f"the reviewer may not change project files (`find -exec {inner[0]}`)"
                if word == "git":
                    folder, sub, rest = _git_parts(args)
                    place = folder if folder else "."
                    reads = GIT_READ_FORMS.get(sub)
                    writes = sub in GIT_WRITES or (reads is not None and sub != "worktree" and bool(rest)
                                                   and not any(r in reads for r in rest))
                    if sub == "stash" and not rest:
                        writes = True
                    if sub == "tag" and (not rest or rest[0] in ("-l", "--list", "--contains", "--points-at", "-n")):
                        writes = False  # listing tags (K-363)
                    if sub == "config" and len([r for r in rest if not r.startswith("-")]) == 1:
                        writes = False  # `git config <key>` reads one value
                    if writes and in_project(place, here):
                        return f"the reviewer may not change the repository (`git {sub}`)"
                elif word == "kanon" and args and (args[0] in KANON_WRITES or
                                                   (args[0] == "branch" and args[1:2] != ["status"])):
                    return f"the reviewer may not run `kanon {' '.join(args[:2])}`"  # branch writes too (K-384)
                elif word in ("sed", "perl") and any(re.match(r"-\w*i|--in-place", a) for a in args):
                    if any(in_project(a, here) for a in args if not a.startswith("-")):
                        return f"the reviewer may not edit project files (`{word} -i`)"
                elif word in FILE_WRITERS:
                    operands = [a for a in args if not a.startswith("-")]
                    if word in DESTINATION_ONLY:  # only the destination is written (K-361)
                        given = next((args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-t", "--target-directory")), None)
                        operands = [given] if given else operands[-1:]
                    if any(in_project(a, here) for a in operands):
                        return f"the reviewer may not change project files (`{word}`)"
                for index, token in enumerate(stage if word not in ("[[", "test", "[") else []):
                    if token in REDIRECTS and index + 1 < len(stage):
                        target = stage[index + 1]
                        if target not in ("/dev/null", "/dev/stderr", "/dev/stdout") and in_project(target, here):
                            return "the reviewer may not write project files (redirection)"
                code = next((args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-c", "-e")), None) \
                    if word.startswith(("python", "node", "ruby", "perl")) else None
                if code and CODE_WRITES.search(code):  # judge the paths the code names, not the folder (K-362)
                    literals = re.findall(r"['\"]([^'\"]+)['\"]", code)
                    if any(in_project(l, here) for l in literals if not re.fullmatch(r"[wax]\+?b?|r", l)):
                        return "the reviewer may not write project files from code"
        return None

    return judge(command)


GH_READS = {"view", "list", "status", "diff", "checks"}
GH_READ_GROUPS = {"search", "help", "version", "--version", "--help", "completion"}


def _gh_method(args: list[str]) -> str | None:
    for index, arg in enumerate(args):
        if arg in ("-X", "--method") and index + 1 < len(args):
            return args[index + 1]
        for prefix in ("--method=", "-X="):
            if arg.startswith(prefix):
                return arg[len(prefix):]
        if arg.startswith("-X") and len(arg) > 2:
            return arg[2:]
    return None


def gh_write(command: str) -> str | None:
    """Reason to block a `gh` command that is not a plain read (owner, 2026-11-19), or None.

    Kanon acts on GitHub only as its App, through `kanon github`, so an agent's `gh` may only read:
    `view`, `list`, `status`, `diff` and `checks`, `gh search`, and `gh api` with GET (K-407).
    """
    for unit in _units(_shell_words(_without_heredoc_bodies(command))):
        for stage in _stages(unit):
            word, args = _command(stage)
            if word != "gh":
                continue
            args = [a for a in args if a not in ("--repo", "-R")] if args else []
            group, action = (args[0] if args else "help"), (args[1] if len(args) > 1 else "")
            if group in GH_READ_GROUPS or (group == "auth" and action == "status"):
                continue
            if group == "api":
                method = (_gh_method(args) or "").upper()
                fields = any(a in ("-f", "-F", "--field", "--raw-field", "--input") for a in args)
                if len(args) > 1 and args[1] == "graphql":
                    if any("mutation" in a for a in args):
                        return "`gh api graphql` with a mutation would act on GitHub as you; Kanon acts only as its App"
                    continue
                if (method or ("POST" if fields else "GET")) == "GET":
                    continue
                return "`gh api` with a writing method would act on GitHub as you; Kanon acts only as its App"
            if action in GH_READS:
                continue
            return f"`gh {group} {action}`".replace(" `", "`") + " is not a read; Kanon acts on GitHub only as its App"
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
    reason = check(command, cwd, os.path.expanduser("~"), extra) or gh_write(command)
    if not reason and event.get("agent_type") == REVIEWER:
        write = reviewer_write(command, cwd, os.path.expanduser("~"), extra[0] or cwd, extra[1:])
        if write:  # its own advice (K-368)
            print(f"Blocked by the Kanon guard: {write}. The reviewer reads and probes; copy files into a "
                  "folder made with `mktemp -d` or the scratchpad to experiment.", file=sys.stderr)
            return 2
    if reason:
        print(f"Blocked by the Kanon guard: {reason}. Delete only what you created, by its exact path "
              "(for example a folder made with `mktemp -d`), and never with find or globs over shared folders.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
