import datetime as dt
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

import pytest

from kanon import init as kinit
from kanon import profile as profiles
from kanon import sync as ksync
from kanon.cli import main
from kanon.schema import validate
from kanon.settings import render_settings, validate_settings
from kanon.templates import ROLE_FILES, render

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 11, 16)
APPROVERS = ["ada-dev"]
COMMITTED = sorted([
    "kanon/REVIEW.md", "kanon/STATUS.md", "kanon/kanon.toml", "kanon/sources.md",
    "kanon/docs/conduct-and-writing.md", "kanon/docs/learnings.md",
    "kanon/decisions/.gitkeep", "kanon/work/.gitkeep", "kanon/archive/.gitkeep",
    *ROLE_FILES, ".gitignore",
])


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    return tmp_path


def files_in(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)


def snapshot(root):
    return {f: (root / f).read_bytes() for f in files_in(root)}


def untracked_or_changed(repo):
    return [l[3:] for l in git(repo, "status", "--porcelain", "--untracked-files=all").splitlines()]


def test_init_writes_shared_files_and_generated_files(repo):
    kinit.init(repo, APPROVERS, TODAY)
    assert sorted(set(files_in(repo)) - set(ksync.GENERATED)) == COMMITTED
    assert set(ksync.GENERATED) <= set(files_in(repo))


def test_generated_files_never_show_in_git_status(repo):
    kinit.init(repo, APPROVERS, TODAY)
    assert sorted(untracked_or_changed(repo)) == COMMITTED


def test_init_never_creates_agents_claude_or_claude_local(repo):
    kinit.init(repo, APPROVERS, TODAY)
    for name in ("AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"):
        assert not (repo / name).exists()


def test_existing_agents_and_claude_files_are_byte_identical(repo):
    (repo / "AGENTS.md").write_text("# Team agents\nKeep.\n")
    (repo / "CLAUDE.md").write_text("@AGENTS.md\n")
    before = {n: hashlib.sha256((repo / n).read_bytes()).hexdigest() for n in ("AGENTS.md", "CLAUDE.md")}
    kinit.init(repo, APPROVERS, TODAY)
    ksync.sync(repo)
    assert {n: hashlib.sha256((repo / n).read_bytes()).hexdigest() for n in before} == before


def test_every_committed_document_is_valid(repo):
    kinit.init(repo, APPROVERS, TODAY)
    for doc in (repo / "kanon").rglob("*.md"):
        assert validate(doc.read_text()) == [], doc
    assert validate_settings((repo / "kanon/kanon.toml").read_text()) == []


def test_second_run_changes_nothing(repo):
    kinit.init(repo, APPROVERS, TODAY)
    before = snapshot(repo)
    result = kinit.init(repo, ["someone-else"], dt.date(2027, 1, 1))
    assert snapshot(repo) == before
    assert result.created == [] and result.updated == []


def test_existing_files_are_never_overwritten(repo):
    (repo / "kanon").mkdir()
    (repo / "kanon/STATUS.md").write_text("mine")
    (repo / ".claude/rules").mkdir(parents=True)
    (repo / ".claude/rules/kanon.md").write_text("my own rules")
    result = kinit.init(repo, APPROVERS, TODAY)
    assert (repo / "kanon/STATUS.md").read_text() == "mine"
    assert (repo / ".claude/rules/kanon.md").read_text() == "my own rules"
    assert any("not written by Kanon" in w for w in result.warnings)


def test_gitignore_block_is_added_once_and_keeps_other_lines(repo):
    (repo / ".gitignore").write_text("node_modules/\n")
    kinit.init(repo, APPROVERS, TODAY)
    ksync.sync(repo)
    text = (repo / ".gitignore").read_text()
    assert text.startswith("node_modules/\n") and text.count(ksync.IGNORE_START) == 1
    assert all(f"/{p}" in text for p in ksync.GENERATED)


def test_fresh_clone_plus_sync_reproduces_generated_files(repo, tmp_path_factory):
    kinit.init(repo, APPROVERS, TODAY)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--no-verify", "-m", "init")
    clone = tmp_path_factory.mktemp("clone") / "c"
    subprocess.run(["git", "clone", "-q", str(repo), str(clone)], check=True)
    assert not any((clone / p).exists() for p in ksync.GENERATED)
    ksync.sync(clone)
    for rel in ksync.GENERATED:
        assert (clone / rel).read_bytes() == (repo / rel).read_bytes(), rel


def test_two_people_with_different_profiles_merge_cleanly_and_publish_nothing(repo, tmp_path_factory, monkeypatch):
    kinit.init(repo, ["ada-dev", "bo-dev"], TODAY)
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--no-verify", "-m", "init")
    clones = []
    for who, secret in (("ada-dev", "Ada secret background"), ("bo-dev", "Bo secret background")):
        clone = tmp_path_factory.mktemp(who) / "c"
        subprocess.run(["git", "clone", "-q", str(repo), str(clone)], check=True)
        monkeypatch.setenv("KANON_PROFILE", json.dumps({"github": who, "level": "developer", "description": secret}))
        ksync.sync(clone)
        (clone / "kanon/work").mkdir(exist_ok=True)
        (clone / f"kanon/work/{who}.txt").write_text(who)
        git(clone, "add", "-A")
        git(clone, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--no-verify", "-m", who)
        clones.append(clone)
    a, b = clones
    git(b, "pull", "-q", "--no-rebase", "--no-edit", str(a))
    assert "Ada secret" not in git(b, "log", "-p", "--all") and "Bo secret" not in git(b, "log", "-p", "--all")
    assert "Bo secret" in (b / ".claude/rules/kanon-person.md").read_text()


def test_profile_sources_and_precedence(tmp_path, monkeypatch):
    assert profiles.load() is None
    saved = profiles.save(profiles.Profile(github="file-user", level="developer"))
    assert saved.stat().st_mode & 0o077 == 0
    assert profiles.load().github == "file-user"
    other = tmp_path / "p.toml"
    profiles.save(profiles.Profile(github="pointed-user"), other)
    monkeypatch.setenv("KANON_PROFILE_FILE", str(other))
    assert profiles.load().github == "pointed-user"
    monkeypatch.setenv("KANON_PROFILE", '{"github": "env-user", "level": "specialist"}')
    assert profiles.load().github == "env-user"
    monkeypatch.setenv("KANON_PROFILE", "{not json")
    with pytest.raises(ValueError):
        profiles.load()


def test_without_a_profile_agents_are_told_to_ask(repo):
    kinit.init(repo, APPROVERS, TODAY)
    assert "At first contact, ask" in (repo / ".claude/rules/kanon-person.md").read_text()


def test_profile_reaches_the_person_rules(repo, monkeypatch):
    monkeypatch.setenv("KANON_PROFILE", json.dumps(
        {"github": "ada-dev", "name": "Ada", "level": "developer", "preferences": ["Keep chat short."]}))
    kinit.init(repo, APPROVERS, TODAY)
    text = (repo / ".claude/rules/kanon-person.md").read_text()
    assert "# Working With Ada" in text and "Keep chat short." in text and "precise technical language" in text


def test_kanon_rules_embed_the_projects_conduct_standard(repo):
    kinit.init(repo, APPROVERS, TODAY)
    path = repo / "kanon/docs/conduct-and-writing.md"
    path.write_text(path.read_text().replace("## 1. Working with People", "## 1. Working with People Here"))
    ksync.sync(repo)
    assert "### 1. Working with People Here" in (repo / ".claude/rules/kanon.md").read_text()


def test_settings_hold_no_profiles():
    text = render_settings(APPROVERS)
    assert validate_settings(text) == []
    assert any("must not be committed" in str(p) for p in validate_settings(text + '\n[people.owner]\nlevel = "developer"\n'))
    assert any("GitHub username" in str(p) for p in validate_settings(render_settings(["not valid!"])))
    assert any("at least one" in str(p) for p in validate_settings(render_settings([])))


def test_run_from_a_subdirectory_lays_out_the_repository_root(repo):
    (repo / "sub").mkdir()
    kinit.init(repo / "sub", APPROVERS, TODAY)
    assert (repo / "kanon/kanon.toml").exists() and not (repo / "sub/kanon").exists()


def test_refuses_a_directory_that_is_not_a_git_repository(tmp_path):
    with pytest.raises(RuntimeError, match="not inside a Git repository"):
        kinit.init(tmp_path, APPROVERS, TODAY)
    assert files_in(tmp_path) == []


def test_invalid_approver_is_refused_before_writing(repo):
    with pytest.raises(ValueError, match="GitHub username"):
        kinit.init(repo, ["just me"], TODAY)
    assert files_in(repo) == []


def test_level_question_answers():
    answers = iter(["3", "Mostly backend work."])
    assert kinit.ask_level(lambda _: next(answers)) == ("developer", "Mostly backend work.")
    assert kinit.ask_level(lambda _: "") == ("", "")

    def closed(_):
        raise EOFError
    assert kinit.ask_level(closed) == ("", "") and kinit.ask("x", closed) == ""


def test_cli_init_without_profile_or_approver_is_refused(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    assert main(["init", "--non-interactive"]) == 2
    assert "--approver" in capsys.readouterr().out


def test_cli_init_asks_and_saves_the_profile_outside_the_repository(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    answers = iter(["3", "Backend.", "ada-dev"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert main(["init"]) == 0
    assert profiles.load().github == "ada-dev"
    assert not str(profiles.profile_path()).startswith(str(repo))
    assert tomllib.loads((repo / "kanon/kanon.toml").read_text())["kanon"]["approvers"] == ["ada-dev"]


def test_cli_profile_print_env_round_trips(monkeypatch, capsys):
    assert main(["profile", "--github", "ada-dev", "--level", "developer", "--preference", "Short chat."]) == 0
    capsys.readouterr()
    assert main(["profile", "--print-env"]) == 0
    value = capsys.readouterr().out.strip()
    monkeypatch.setenv("KANON_PROFILE", value)
    assert profiles.load().preferences == ("Short chat.",)
    assert main(["profile", "--name", "x"]) == 2


def test_this_repository_matches_its_templates():
    """Committed instance copies of the role prompts and conduct standard must not drift."""
    for dest, src in ROLE_FILES.items():
        text = (ROOT / dest).read_text()
        date = next(l.split(": ")[1] for l in text.splitlines() if l.startswith("updated:"))
        assert text == render(src, date=date), dest
    conduct = (ROOT / "kanon/docs/conduct-and-writing.md").read_text()
    date = next(l.split(": ")[1] for l in conduct.splitlines() if l.startswith("updated:"))
    assert conduct == render("conduct-and-writing.md", date=date)


def test_marker_elsewhere_in_a_file_does_not_make_it_generated(repo):
    kinit.init(repo, APPROVERS, TODAY)
    (repo / ".claude/rules/team.md").write_text(f"# Team\n\nA seamless note.\n{ksync.MARKER}\n")
    (repo / "CLAUDE.md").write_text(f"# Mine\n\nA robust plan.\n{ksync.MARKER}\n")
    from kanon import verify as kv
    found = [(f.path, f.rule) for f in kv.verify(repo)]
    assert (".claude/rules/team.md", "writing") in found and ("CLAUDE.md", "writing") in found
    (repo / ".claude/rules/kanon.md").write_text(f"# Quoted\n\n{ksync.MARKER}\n")
    assert ".claude/rules/kanon.md" in ksync.sync(repo).refused


def test_damaged_gitignore_block_is_refused_not_rewritten(repo):
    (repo / ".gitignore").write_text(f"foo\n{ksync.IGNORE_START}\n/x\n")
    result = ksync.sync(repo)
    assert ".gitignore" in result.refused
    assert (repo / ".gitignore").read_text() == f"foo\n{ksync.IGNORE_START}\n/x\n"


def test_profile_problems_are_reported_and_blank_env_is_unset(repo, monkeypatch):
    monkeypatch.setenv("KANON_PROFILE", '{"level": "wizard", "github": "x y"}')
    notes = ksync.sync(repo).notes
    assert any("level 'wizard'" in n for n in notes) and any("GitHub username" in n for n in notes)
    monkeypatch.setenv("KANON_PROFILE", "   ")
    assert profiles.load() is None


def test_profile_folder_is_private():
    path = profiles.save(profiles.Profile(github="ada-dev"))
    assert path.parent.stat().st_mode & 0o077 == 0 and path.stat().st_mode & 0o077 == 0


def test_a_committed_generated_file_is_a_finding(repo):
    kinit.init(repo, APPROVERS, TODAY)
    git(repo, "add", "-f", ".claude/rules/kanon-person.md")
    from kanon import verify as kv
    assert any(f.rule == "privacy" and f.path == ".claude/rules/kanon-person.md" for f in kv.verify(repo))
