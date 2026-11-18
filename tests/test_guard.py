import json
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
    hook.write_text(ksync.expected_files(tmp_path, None)[ksync.GUARD])
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
    settings.write_text(json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}, "name": "café"}, ensure_ascii=False))
    kinit.init(tmp_path, ["ada-dev"])
    ksync.sync(tmp_path)
    data = json.loads(settings.read_text())
    assert data["permissions"] == {"allow": ["Bash(ls:*)"]}
    assert "café" in settings.read_text()
    commands = [h["command"] for e in data["hooks"]["PreToolUse"] for h in e["hooks"]]
    assert commands == [ksync.GUARD_COMMAND]
    status = subprocess.run(["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True).stdout
    assert "settings.local.json" not in status


def test_an_older_guard_entry_is_recognised_by_its_path(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    settings = tmp_path / ksync.SETTINGS_LOCAL
    settings.parent.mkdir(parents=True)
    old = {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/kanon-guard.py"'}
    settings.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [old]}]}}))
    kinit.init(tmp_path, ["ada-dev"])
    entries = json.loads(settings.read_text())["hooks"]["PreToolUse"]
    commands = [h["command"] for e in entries for h in e["hooks"]]
    assert commands == [ksync.GUARD_COMMAND]


@pytest.mark.parametrize("content", [
    "{not json", '{"hooks": []}', '{"hooks": null}', '{"hooks": {"PreToolUse": {}}}',
    '{"hooks": {"PreToolUse": ["x"]}}', "[]",
])
def test_unexpected_settings_are_left_alone_with_a_note(tmp_path, content):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ksync.SETTINGS_LOCAL).write_text(content)
    kinit.init(tmp_path, ["ada-dev"])
    assert (tmp_path / ksync.SETTINGS_LOCAL).read_text() == content
    assert any("guard hook was not registered" in n for n in ksync.sync(tmp_path).notes)
