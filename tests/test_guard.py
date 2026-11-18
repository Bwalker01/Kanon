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
])
def test_destructive_commands_are_blocked(command):
    assert guard.check(command, CWD, HOME, SCRATCH)


@pytest.mark.parametrize("command", [
    "rm -rf /tmp/claude-0/-home-user-project/session/scratchpad/probe",
    'D=$(mktemp -d); rm -rf "$D"', "rm src/old.py", "find /tmp -name x", "git rm -q old.md",
    "rm -rf /tmp/pytest-of-root/pytest-3", "ls /tmp", "echo hello",
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


def test_hook_registration_keeps_other_settings_and_is_idempotent(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    settings = tmp_path / ksync.SETTINGS_LOCAL
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}}))
    kinit.init(tmp_path, ["ada-dev"])
    ksync.sync(tmp_path)
    data = json.loads(settings.read_text())
    assert data["permissions"] == {"allow": ["Bash(ls:*)"]}
    commands = [h["command"] for e in data["hooks"]["PreToolUse"] for h in e["hooks"]]
    assert commands == [ksync.GUARD_COMMAND]
    status = subprocess.run(["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True).stdout
    assert "settings.local.json" not in status


def test_invalid_settings_file_is_left_alone(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ksync.SETTINGS_LOCAL).write_text("{not json")
    kinit.init(tmp_path, ["ada-dev"])
    assert (tmp_path / ksync.SETTINGS_LOCAL).read_text() == "{not json"
    assert any("not valid JSON" in n for n in ksync.sync(tmp_path).notes)
