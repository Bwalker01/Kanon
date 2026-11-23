import json
import os
import shutil
import subprocess
import sys

import pytest

from kanon import guard
from kanon import init as kinit
from kanon import sync as ksync

CWD, HOME = "/home/user/project", "/root"
SCRATCH = ["/tmp/claude-0/-home-user-project/session/scratchpad"]
# The command that deleted /tmp on 2026-11-18 (learning L-004).
INCIDENT = ("rm -f /tmp/claude-0/x/scratchpad/probe.py; for d in $(find /tmp -maxdepth 1 -name 'tmp*' "
            "-type d -mmin -30); do rm -rf \"$d\"; done")


@pytest.mark.parametrize("command", [
    INCIDENT, "rm -rf /tmp", "rm -rf /tmp/*", "rm -rf ~", "rm -rf $HOME/", "rm -rf / --no-preserve-root",
    "find / -name x -delete", "rm -rf /home/user/project", "rm -rf .", "rm -rf *",
    "rm -rf /tmp/claude-0", "rm -rf /tmp/claude-0/-home-user-project/session/scratchpad",
    "python3 -c 'import shutil; shutil.rmtree(\"/tmp\")'",
    # K-101: other ways to name rm
    "/bin/rm -rf /tmp", "\\rm -rf /tmp", "'rm' -rf /tmp",
    "find /tmp -maxdepth 1 -name 'tmp*' -print0 | xargs -0 /bin/rm -rf",
    # K-102: inner shells, substitution and globs
    "bash -c 'rm -rf /tmp'", "sh -c \"rm -rf /tmp/*\"", "eval 'rm -rf /tmp'", "rm -rf $(echo /tmp)",
    "rm -rf /tmp/?*", "rm -rf /tmp/**", "rm -rf /tmp/{*,.*}",
    "for d in /tmp/*/; do rm -rf \"$d\"; done", "ls -d /tmp/*/ | xargs rm -rf",
    # K-103: relative paths and parents of the project
    "rm -rf ..", "rm -rf ../..", "rm -rf /home/user", "rm -rf /home/user/", "rm -rf /opt",
    "find . -delete",
    # K-110: a git command in front must not hide the deletion
    "git status; " + INCIDENT, "git status && rm -rf $(echo /tmp)",
    "git log -1 && for d in /tmp/*/; do rm -rf \"$d\"; done",
    # K-111: combined or earlier shell flags
    "bash -lc 'rm -rf /tmp'", "bash -e -c 'rm -rf /tmp'", "sh -xc \"rm -rf /tmp/*\"",
    # K-113: the find start text reused as a deletion target
    "find . -name x -print | xargs rm -rf .",
    # K-114: following cd, and pathlib deletions
    "cd / && rm -rf tmp", "cd /tmp && rm -rf claude-0",
    "python3 -c 'import pathlib; pathlib.Path(\"/tmp\").rmdir()'",
    # K-260: a newline separates commands
    "cd /home/user/project\n" + INCIDENT, "cd /tmp\nrm -rf claude-0", "echo start\nrm -rf /tmp",
    "cd /home/user/project && ls\nrm -rf /tmp", "ls |\nxargs rm -rf /tmp",
    # K-261: commands that run other programs are judged
    "uv run rm -rf /tmp", "uv run rm -rf /tmp/claude-0", "make -C /tmp clean && rm -rf /tmp",
    "uv run python - <<'EOF'\nimport shutil\nshutil.rmtree('/tmp')\nEOF",
    # K-262: a git stage in a pipeline hides nothing
    "git status | rm -rf /tmp", "git log -1 | xargs rm -rf /tmp", "git ls-files | xargs rm -rf /home/user/project",
    "bash -c 'git status | rm -rf /tmp'",
    # K-263: long options and option arguments before -c
    "bash -o pipefail -c 'rm -rf /tmp'", "bash --norc -c 'rm -rf /tmp'",
    # K-264: cd inside a subshell or brace group
    "(cd /tmp && rm -rf claude-0)", "{ cd /tmp && rm -rf claude-0; }",
    # K-266 and K-267: a doubled slash; git clean with long flags
    "rm -rf //tmp", "git clean --force -d /tmp",
])
def test_destructive_commands_are_blocked(command):
    assert guard.check(command, CWD, HOME, SCRATCH)


@pytest.mark.parametrize("command", [
    "rm -rf /tmp/claude-0/-home-user-project/session/scratchpad/probe",
    'D=$(mktemp -d); rm -rf "$D"', "rm src/old.py", "find /tmp -name x", "git rm -q old.md",
    "rm -rf /tmp/pytest-of-root/pytest-3", "ls /tmp", "echo hello",
    # K-106: ordinary work that must not be blocked
    "find . -name __pycache__ -exec rm -rf {} +", "find . -name '*.pyc' -delete",
    "cd /home/user/project && rm -rf dist", "rm -f build.log && ls /tmp",
    "rm -rf build && pip install -e .", "git -C /home/user/project rm -q old.md",
    "rm -f /tmp/claude-0/-home-user-project/session/scratchpad/x && ls -d /tmp",
    "for f in *.pyc; do rm \"$f\"; done",
    # K-112: cd into the project with substitution or loops elsewhere in the command
    "cd /home/user/project && git rm -q old.md && git commit -m \"$(cat <<'EOF'\nMODIFIED: x\nEOF\n)\"",
    "cd /home/user/project && rm -rf dist && echo $(date)",
    "cd /home/user/project && for f in *.pyc; do rm -f \"$f\"; done",
    "cd /home/user/project && git ls-files -d | xargs git rm -q",
    'D=$(mktemp -d) && rm -rf "$D" && ls /tmp',
    # A commit message holding deletion words inside quotes
    "git commit -m 'REMOVED: rm -rf /tmp from the docs'",
    # K-260: quoted newlines stay inside their argument
    "git commit -m \"line one\nrm -rf /tmp is described here\"",
    # K-265: a folder reached by cd is not protected itself
    "cd build && rm -rf *", "cd /home/user/project/dist && rm -rf ./*",
])
def test_ordinary_commands_are_allowed(command):
    assert guard.check(command, CWD, HOME, SCRATCH) is None


def run_hook(path, command, cwd=CWD):
    event = {"tool_name": "Bash", "cwd": cwd, "tool_input": {"command": command}}
    return subprocess.run([sys.executable, str(path)], input=json.dumps(event), capture_output=True, text=True)


def test_generated_hook_blocks_the_incident_and_allows_normal_work(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    kinit.init(tmp_path, ["ada-dev"])
    hook = tmp_path / ksync.GUARD
    blocked = run_hook(hook, INCIDENT, str(tmp_path))
    assert blocked.returncode == 2 and "Kanon guard" in blocked.stderr
    assert run_hook(hook, "ls -la", str(tmp_path)).returncode == 0


def test_non_bash_tools_and_bad_input_are_allowed(tmp_path):
    hook = tmp_path / "guard.py"
    hook.write_text(ksync.expected_files(tmp_path, None)[ksync.GUARD], encoding="utf-8")
    write = {"tool_name": "Write", "tool_input": {"file_path": "/tmp/x", "content": "rm -rf /tmp"}}
    assert subprocess.run([sys.executable, str(hook)], input=json.dumps(write), text=True).returncode == 0
    assert subprocess.run([sys.executable, str(hook)], input="not json", text=True).returncode == 0


def test_registered_command_allows_everything_when_the_script_is_missing(tmp_path):
    """K-104: a missing hook script must not block every command."""
    event = json.dumps({"tool_name": "Bash", "cwd": str(tmp_path), "tool_input": {"command": "ls"}})
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"}
    result = subprocess.run(["sh", "-c", ksync.GUARD_COMMAND], input=event, text=True, env=env)
    assert result.returncode == 0
    no_dir = subprocess.run(["sh", "-c", ksync.GUARD_COMMAND], input=event, text=True, env={"PATH": "/usr/bin:/bin"})
    assert no_dir.returncode == 0


def test_hook_registration_keeps_other_settings_and_is_idempotent(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    settings = tmp_path / ksync.SETTINGS_LOCAL
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}, "name": "café"}, ensure_ascii=False), encoding="utf-8")
    kinit.init(tmp_path, ["ada-dev"])
    ksync.sync(tmp_path)
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data["permissions"]["allow"] == ["Bash(ls:*)"]
    assert data["permissions"]["deny"] == ksync.deny_rules(tmp_path)
    assert "café" in settings.read_text(encoding="utf-8")
    commands = [h["command"] for e in data["hooks"]["PreToolUse"] for h in e["hooks"]]
    assert commands == [ksync.GUARD_COMMAND]
    status = subprocess.run(["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True).stdout
    assert "settings.local.json" not in status


def test_an_older_guard_entry_is_recognised_by_its_path(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    settings = tmp_path / ksync.SETTINGS_LOCAL
    settings.parent.mkdir(parents=True)
    old = {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/kanon-guard.py"'}
    settings.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [old]}]}}), encoding="utf-8")
    kinit.init(tmp_path, ["ada-dev"])
    entries = json.loads(settings.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    commands = [h["command"] for e in entries for h in e["hooks"]]
    assert commands == [ksync.GUARD_COMMAND]


@pytest.mark.parametrize("content", [
    "{not json", '{"hooks": []}', '{"hooks": null}', '{"hooks": {"PreToolUse": {}}}',
    '{"hooks": {"PreToolUse": ["x"]}}', "[]",
])
def test_unexpected_settings_are_left_alone_with_a_note(tmp_path, content):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ksync.SETTINGS_LOCAL).write_text(content, encoding="utf-8")
    kinit.init(tmp_path, ["ada-dev"])
    assert (tmp_path / ksync.SETTINGS_LOCAL).read_text(encoding="utf-8") == content
    assert any("guard hook was not registered" in n for n in ksync.sync(tmp_path).notes)


PROJECT = "/home/user/project"


@pytest.mark.parametrize("command", [  # K-29: the reviewer may not change the project
    "git commit -m x", "git add -A", "git -C /home/user/project reset --hard", "cd src && git stash",
    "echo x > notes.md", "echo x >> /home/user/project/README.md", "sed -i 's/a/b/' src/x.py",
    "cp /tmp/x src/x.py", "rm tests/test_x.py", "touch kanon/work/new.md", "tee out.txt < /dev/null",
    "kanon approve plan", "kanon transcribe plan --quote ok", "uv run kanon sync",
    "python3 -c \"open('x.md', 'w').write('y')\"", "bash -c 'git commit -m x'",
])
def test_reviewer_writes_to_the_project_are_blocked(command):
    assert guard.reviewer_write(command, PROJECT, HOME, PROJECT, SCRATCH)


@pytest.mark.parametrize("command", [
    "git status", "git log -5 --oneline", "git diff HEAD~1", "git show bb29241:src/kanon/guard.py",
    "git worktree add /tmp/tmp.abc/wt HEAD", "uv run pytest -q", "kanon verify", "grep -rn x src",
    "echo x > /tmp/claude-0/-home-user-project/session/scratchpad/probe.py", "echo x > /dev/null",
    "D=$(mktemp -d); cp -r src \"$D\"", "cd /tmp/tmp.abc && git commit -m probe",
    "python3 -I /tmp/claude-0/-home-user-project/session/scratchpad/probe.py",
])
def test_reviewer_reads_and_scratch_writes_are_allowed(command):
    assert guard.reviewer_write(command, PROJECT, HOME, PROJECT, SCRATCH) is None


def test_the_hook_applies_reviewer_rules_only_to_the_reviewer(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    kinit.init(tmp_path, ["ada-dev"])
    hook = tmp_path / ksync.GUARD

    def run(agent):
        event = {"tool_name": "Bash", "cwd": str(tmp_path), "tool_input": {"command": "git commit -m x"}}
        if agent:
            event["agent_type"] = agent
        return subprocess.run([sys.executable, str(hook)], input=json.dumps(event), capture_output=True, text=True,
                              env={"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"}).returncode
    assert run("kritos-reviewer") == 2
    assert run(None) == 0 and run("general-purpose") == 0


@pytest.mark.parametrize("command", [  # K-341, K-345: ordinary review commands
    'grep -n "->" src/kanon/guard.py', "awk '$3 > 5' f", 'python3 -c "print(1>2)"', "git log --format='%h > %s'",
    'echo "a=>b"', "cat > /tmp/claude-0/-home-user-project/session/scratchpad/t.py <<'E'\nfoo > README.md\ngit init\nE",
    "git stash list", "git branch --show-current", "git config --get user.name",
    "d=$(mktemp -d) && cd \"$d\" && git init -q && touch a", "cd \"$(mktemp -d)\" && git init",
    "S=/tmp/claude-0/-home-user-project/session/scratchpad; cat > $S/g.py <<'E'\nprint(1)\nE",
])
def test_reviewer_review_commands_are_not_blocked(command):
    assert guard.reviewer_write(command, PROJECT, HOME, PROJECT, SCRATCH) is None


@pytest.mark.parametrize("command", [  # K-343, K-344, K-351: misses
    "cd /tmp && git -C /home/user/project commit -m x", "git -c user.name=x commit -m y",
    "cd /tmp && git -C /home/user/project reset --hard", "sed --in-place=.bak 's/a/b/' README.md",
    "perl -pi -e 's/a/b/' README.md", "env cp /tmp/x README.md", "find . -name x -exec touch {} \\;",
    "rsync /tmp/x README.md", "python3 -c \"import shutil; shutil.copy('/tmp/x', 'README.md')\"",
    "python3 -m kanon.cli sync", "uv run --directory . kanon sync", "uv run -q kanon desk",
    "git branch -D old", "git config user.name x", "git stash",
])
def test_reviewer_misses_are_now_blocked(command):
    assert guard.reviewer_write(command, PROJECT, HOME, PROJECT, SCRATCH)


@pytest.mark.parametrize("command", [  # K-360 to K-363: false blocks found in round C2
    "T=$(mktemp -d); cd $T && echo x > a", "echo $(date); cd /tmp && echo x > a",
    "D=$(mktemp -d) && cp -r /home/user/project/src $D/", "cp README.md /tmp/claude-0/-home-user-project/session/scratchpad/r",
    "rsync -a /home/user/project/ /tmp/k/", "tee /tmp/claude-0/-home-user-project/session/scratchpad/o < README.md",
    "grep -c 'open(.*\"w\")' src/kanon/*.py", "git grep -n 'shutil.copy('",
    "python3 -c \"open('/tmp/claude-0/-home-user-project/session/scratchpad/a','w').write('x')\"",
    "git tag --list", "git tag -l", "git tag", "git branch --contains HEAD", "git branch --merged",
    "git config user.name", "kanon desk --help", "kanon sync --help", "[[ 3 > 2 ]] && echo y", "echo $((3 > 2))",
])
def test_reviewer_probe_commands_from_round_c2_are_allowed(command):
    assert guard.reviewer_write(command, PROJECT, HOME, PROJECT, SCRATCH) is None


@pytest.mark.parametrize("command", [  # K-360, K-362, K-367: misses found in round C2
    "cd /tmp && X=$(pwd); cd /home/user/project && echo x > README.md", "(echo x)>README.md",
    "cd /tmp && python3 -c \"open('/home/user/project/README.md','w').write('x')\"",
    'echo x > "$CLAUDE_PROJECT_DIR/README.md"', "find . -name x -delete", "find . -fprint README.md",
    "env -u X cp /tmp/x README.md", "nohup cp /tmp/x README.md", "xargs cp -t src < list",
])
def test_reviewer_misses_from_round_c2_are_blocked(command):
    assert guard.reviewer_write(command, PROJECT, HOME, PROJECT, SCRATCH)


@pytest.mark.parametrize("command,blocked", [  # K-384
    ("kanon branch merge phase-1-plan P1-09", True), ("kanon branch start phase-1-plan P1-09", True),
    ("uv run kanon branch start phase-1-plan P1-09", True), ("kanon branch status phase-1-plan", False),
])
def test_reviewer_branch_commands(command, blocked):
    assert bool(guard.reviewer_write(command, PROJECT, HOME, PROJECT, SCRATCH)) is blocked


@pytest.mark.parametrize("command,blocked", [  # P1-10: agents never act on GitHub as the person
    ("gh pr merge 3", True), ("gh pr review 3 --approve", True), ("gh pr comment 3 -b hi", True),
    ("gh api -X PUT repos/o/r/pulls/3/merge", True), ("gh api repos/o/r/issues/3/comments -f body=x", True),
    ("gh api --method=POST repos/o/r/pulls", True), ("gh issue create -t x", True),
    ("gh pr view 3", False), ("gh pr list", False), ("gh api repos/o/r/pulls", False),
    ("gh api -X GET search/code -f q=x", False), ("echo 'gh pr merge 3'", False),
    # K-407: further writes, and a graphql read
    ("gh api -XPOST repos/o/r/pulls", True), ("gh api -X=POST repos/o/r/pulls", True), ("gh ssh-key add k", True),
    ("gh repo deploy-key add k", True), ("gh auth token", True), ("gh alias set m 'pr merge'", True),
    ("gh pr update-branch 3", True), ("gh pr revert 3", True), ("gh secret set X", True), ("gh run rerun 1", True),
    ("gh repo sync", True), ("gh gist create f", True), ("gh issue pin 3", True),
    ("gh api graphql -f query='mutation{x}'", True), ("gh api graphql -f query='query{viewer{login}}'", False),
    ("gh search code x", False), ("gh auth status", False), ("gh run list", False),
])
def test_gh_writes_are_blocked_for_every_agent(command, blocked):
    assert bool(guard.gh_write(command)) is blocked


# Windows: Claude Code runs Bash through Git Bash, and the hook receives Windows paths. These tests
# set the guard's WINDOWS flag, so they run on every platform (the 8.3 lookups run only on Windows).
WIN_CWD, WIN_HOME = "C:\\Users\\ada\\project", "C:\\Users\\ada"
WIN_SCRATCH = ["C:\\Users\\ada\\AppData\\Local\\Temp\\claude\\s\\scratchpad"]


@pytest.fixture
def windows(monkeypatch):
    monkeypatch.setattr(guard, "WINDOWS", True)
    monkeypatch.setattr(guard, "_SYSTEM_CACHE", {})
    monkeypatch.setenv("TEMP", "C:\\Users\\ada\\AppData\\Local\\Temp")
    monkeypatch.setenv("SystemRoot", "C:\\Windows")
    monkeypatch.setenv("ProgramFiles", "C:\\Program Files")
    monkeypatch.setenv("USERPROFILE", WIN_HOME)


def test_windows_paths_are_read_in_git_bash_form(windows):
    assert guard._posix("C:\\Users\\ada") == "/c/Users/ada"
    assert guard._posix("C:/Users/ada/") == "/c/Users/ada"
    assert guard._posix("D:") == "/d"
    assert guard._posix("..\\src") == "../src"
    assert guard._posix("src/x.py") == "src/x.py" and guard._posix("/tmp") == "/tmp"
    assert guard._verb("rm.exe") == "rm" and guard._verb("/usr/bin/rm.EXE") == "rm"


@pytest.mark.parametrize("command", [
    "rm -rf /c/Users/ada", "rm -rf 'C:\\Users\\ada'", "rm -rf C:/Users/ada/project", "rm -rf .",
    "rm.exe -rf /c/Users/ada/project", "rm -rf /c", "rm -rf /d", "rm -rf ..",
    "rm -rf '..\\'", "rm -rf '.\\'", "rm -rf '..\\..'", "rm -rf 'src\\..\\..'",
    "rm -rf /C/USERS/ADA", "rm -rf C:/Windows", "rm -rf 'C:/Program Files'", "rm -rf /c/users",
    "find C:/Users/ada/AppData/Local/Temp -maxdepth 1 -name 'tmp*' -delete",
    "python -c \"import shutil; shutil.rmtree('C:/Users/ada')\"",
    "python -c \"import shutil; shutil.rmtree('/c/Users/ada/my project/..')\"",
])
def test_windows_deletions_of_protected_locations_are_blocked(windows, command):
    assert guard.check(command, WIN_CWD, WIN_HOME, [WIN_CWD])


@pytest.mark.parametrize("command", [
    "rm -rf '\\Users\\ada'", "rm -rf '\\Users\\ada\\project'", "rm -rf '\\Windows'", "rm -rf '\\Program Files'",
    "find '\\Users\\ada\\AppData\\Local\\Temp' -maxdepth 1 -name 'tmp*' -delete",
    "cd /tmp && rm -rf '\\Users\\ada'", "rm -f a.txt '\\'",
])
def test_windows_paths_from_the_drive_root_are_blocked(windows, command):
    """Git Bash reads a single leading backslash as the current drive's root (review round 4, F1)."""
    assert guard.check(command, WIN_CWD, WIN_HOME, [WIN_CWD])


def test_windows_reviewer_writes_from_the_drive_root_are_blocked(windows):
    assert guard.reviewer_write("echo x > '\\Users\\ada\\project\\a.md'", WIN_CWD, WIN_HOME, WIN_CWD, WIN_SCRATCH)


@pytest.mark.parametrize("command", [
    "xargs -d '\\n' rm -f < list.txt", "rm -fv a.txt | tr '\\n' ','", "rm -f a | tr -d '\\r'",
])
def test_windows_escape_arguments_beside_a_deletion_are_allowed(windows, command):
    r"""Review round 4, F2: `'\n'` is an argument, not the drive root `/n`."""
    assert guard.check(command, WIN_CWD, WIN_HOME, [WIN_CWD]) is None


def test_windows_8_3_short_names_are_protected(windows, monkeypatch):
    """Windows names one folder twice; both names are protected (review round 4, F3)."""
    shorts = {"c:/users/ada": "C:\\Users\\ADA~1", "c:/users/ada/project": "C:\\Users\\ADA~1\\PROJEC~1",
              "c:/users/ada/appdata/local/temp": "C:\\Users\\ADA~1\\AppData\\Local\\Temp"}
    monkeypatch.setattr(guard.os, "name", "nt")
    monkeypatch.setattr(guard.os.path, "realpath", lambda path: path)
    monkeypatch.setattr(guard, "_short_name", lambda path: shorts.get(path.replace("\\", "/").lower()))
    for command in ["rm -rf C:/Users/ADA~1", "rm -rf /c/Users/ADA~1/PROJEC~1",
                    "find C:/Users/ADA~1/AppData/Local/Temp -maxdepth 1 -name 'tmp*' -delete"]:
        assert guard.check(command, WIN_CWD, WIN_HOME, [WIN_CWD]), command
    assert guard.check("rm -rf /c/Users/ADA~1/PROJEC~1/build", WIN_CWD, WIN_HOME, [WIN_CWD]) is None


def test_a_unc_project_protects_its_parents(windows):
    assert guard.check("rm -rf ..", "\\\\server\\share\\proj", WIN_HOME, [])


@pytest.mark.parametrize("command", ["rm -rf build", "rm -f /c/Users/ada/project/x.pyc", "rm -rf src/__pycache__",
                                     "rm -rf 'build\\out'"])
def test_windows_ordinary_cleanups_are_allowed(windows, command):
    assert guard.check(command, WIN_CWD, WIN_HOME, [WIN_CWD, *WIN_SCRATCH]) is None


def test_windows_reviewer_writes_are_judged_against_the_project(windows):
    assert guard.reviewer_write("echo x > README.md", WIN_CWD, WIN_HOME, WIN_CWD, WIN_SCRATCH)
    assert guard.reviewer_write("echo x > readme.MD", WIN_CWD, WIN_HOME, "c:\\users\\ADA\\Project", WIN_SCRATCH)
    assert guard.reviewer_write("cp /tmp/x C:/Users/ada/project/src/x.py", WIN_CWD, WIN_HOME, WIN_CWD, WIN_SCRATCH)
    assert guard.reviewer_write("cd .. && echo x > 'project\\a'", WIN_CWD, WIN_HOME, WIN_CWD, WIN_SCRATCH)
    scratch_file = "/c/Users/ada/AppData/Local/Temp/claude/s/scratchpad/probe.txt"
    assert guard.reviewer_write(f"echo x > {scratch_file}", WIN_CWD, WIN_HOME, WIN_CWD, WIN_SCRATCH) is None


def test_drive_letters_and_backslashes_keep_their_posix_meaning_elsewhere(monkeypatch):
    """On Linux and macOS `C:/x` is a relative path and `\\` is not a separator (review B3)."""
    monkeypatch.setattr(guard, "WINDOWS", False)
    assert guard._posix("C:\\Users") == "C:\\Users"
    assert guard.reviewer_write("echo x > C:", PROJECT, HOME, PROJECT, SCRATCH)
    assert guard.reviewer_write("echo x > D:/", PROJECT, HOME, PROJECT, SCRATCH)
    assert guard.check("rm -rf C:/../..", CWD, HOME, SCRATCH)


@pytest.mark.skipif(shutil.which("sh") is None, reason="needs a POSIX shell")
def test_registered_command_skips_a_python3_that_does_not_run(tmp_path):
    """On Windows `python3` may be the Microsoft Store stub: it exists but runs nothing."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "python3"
    stub.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8", newline="\n")
    stub.chmod(0o755)
    real = bin_dir / "python"
    real.write_text(f"#!/bin/sh\nexec \"{pathlib_posix(sys.executable)}\" \"$@\"\n", encoding="utf-8", newline="\n")
    real.chmod(0o755)
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "kanon-guard.py").write_text(ksync.expected_files(tmp_path, None)[ksync.GUARD], encoding="utf-8")
    event = json.dumps({"tool_name": "Bash", "cwd": str(tmp_path), "tool_input": {"command": "rm -rf /tmp"}})
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path),
           "PATH": f"{pathlib_posix(str(bin_dir))}:/usr/bin:/bin"}
    result = subprocess.run(["sh", "-c", ksync.GUARD_COMMAND], input=event, text=True, env=env,
                            capture_output=True)
    assert result.returncode == 2 and "Kanon guard" in result.stderr


def pathlib_posix(path: str) -> str:
    """A path as a POSIX shell on this platform reads it (Git Bash form on Windows)."""
    return guard._posix(path) if os.name == "nt" else path

