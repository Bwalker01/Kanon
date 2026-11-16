import datetime as dt
import subprocess
import tomllib
from pathlib import Path

import pytest

from kanon import init as kinit
from kanon.cli import main
from kanon.schema import validate
from kanon.settings import Person, render_settings, validate_settings
from kanon.templates import render

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 11, 16)
PERSON = Person("owner", "Ada", "developer", "Writes Python daily.", "owner@laptop")
EXPECTED = sorted([
    "AGENTS.md", "CLAUDE.md", "kanon/REVIEW.md", "kanon/STATUS.md", "kanon/kanon.toml",
    "kanon/docs/conduct-and-writing.md", "kanon/docs/learnings.md",
    "kanon/decisions/.gitkeep", "kanon/work/.gitkeep", "kanon/archive/.gitkeep", "kanon/sources.md",
])


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def files_in(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)


def snapshot(root):
    return {f: (root / f).read_bytes() for f in files_in(root)}


def test_init_creates_exactly_the_expected_files(repo):
    result = kinit.init(repo, PERSON, TODAY)
    assert files_in(repo) == EXPECTED
    assert sorted(result.created) == sorted(EXPECTED + [".git/hooks/pre-commit"])
    assert (repo / ".git/hooks/pre-commit").stat().st_mode & 0o111


def test_every_created_document_is_valid(repo):
    kinit.init(repo, PERSON, TODAY)
    for doc in (repo / "kanon").rglob("*.md"):
        assert validate(doc.read_text()) == [], doc
    assert validate_settings((repo / "kanon/kanon.toml").read_text()) == []


def test_second_run_changes_nothing(repo):
    kinit.init(repo, PERSON, TODAY)
    before = snapshot(repo)
    result = kinit.init(repo, PERSON, dt.date(2027, 1, 1))
    assert snapshot(repo) == before
    assert result.created == [] and result.updated == []


def test_existing_files_are_never_overwritten(repo):
    (repo / "kanon").mkdir()
    (repo / "kanon/STATUS.md").write_text("mine")
    (repo / "AGENTS.md").write_text("# My agents\n\nKeep this exactly.\n")
    (repo / "CLAUDE.md").write_text("# Mine\n")
    result = kinit.init(repo, PERSON, TODAY)
    assert (repo / "kanon/STATUS.md").read_text() == "mine"
    agents = (repo / "AGENTS.md").read_text()
    assert agents.startswith("# My agents\n\nKeep this exactly.\n")
    assert kinit.START in agents and kinit.END in agents
    assert (repo / "CLAUDE.md").read_text().startswith("# Mine\n")
    assert "@AGENTS.md" in (repo / "CLAUDE.md").read_text()
    assert "kanon/STATUS.md" in result.kept
    assert set(result.updated) == {"AGENTS.md", "CLAUDE.md"}


def test_refuses_a_directory_that_is_not_a_git_repository(tmp_path):
    with pytest.raises(RuntimeError, match="not inside a Git repository"):
        kinit.init(tmp_path, PERSON, TODAY)
    assert files_in(tmp_path) == []


def test_level_question_answers():
    answers = iter(["3", "Mostly backend work."])
    assert kinit.ask_level(lambda _: next(answers)) == ("developer", "Mostly backend work.")
    assert kinit.ask_level(lambda _: "") == ("", "")
    assert kinit.ask_level(lambda _: "9") == ("", "")


@pytest.mark.parametrize("name", ['Ann "Al" O\'Neil', "back\\slash", "line\nbreak", "naïve"])
def test_settings_escape_awkward_values(name):
    text = render_settings(Person("owner", name, "", name, "owner@laptop"))
    assert tomllib.loads(text)["people"]["owner"]["name"] == name
    assert validate_settings(text) == []


def test_settings_reject_bad_values():
    good = render_settings(PERSON)
    assert any("level" in str(p) for p in validate_settings(good.replace('"developer"', '"wizard"')))
    assert any("role@host" in str(p) for p in validate_settings(good.replace('"owner@laptop"', '"just me"')))
    assert any("review_round_limit" in str(p) for p in validate_settings(good.replace("= 3", "= 0")))
    assert any("not valid TOML" in str(p) for p in validate_settings("[kanon"))
    with pytest.raises(ValueError):
        render_settings(Person("bad id"))


def test_this_repository_uses_the_packaged_standard():
    """The instance copy of the conduct standard must not drift from the template."""
    instance = (ROOT / "kanon/docs/conduct-and-writing.md").read_text()
    date = next(l.split(": ")[1] for l in instance.splitlines() if l.startswith("updated:"))
    assert instance == render("conduct-and-writing.md", date=date)


def test_cli_non_interactive(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    assert main(["init", "--non-interactive", "--name", "Ada", "--approver", "owner@laptop"]) == 0
    out = capsys.readouterr().out
    assert "Created  kanon/REVIEW.md" in out
    assert "Technical level not set" in out
    settings = tomllib.loads((repo / "kanon/kanon.toml").read_text())
    assert settings["people"]["owner"]["level"] == ""


def test_no_placeholder_in_a_folder_that_already_has_content(repo):
    (repo / "kanon/decisions").mkdir(parents=True)
    (repo / "kanon/decisions/001-x.md").write_text("x")
    kinit.init(repo, PERSON, TODAY)
    assert not (repo / "kanon/decisions/.gitkeep").exists()


def test_run_from_a_subdirectory_lays_out_the_repository_root(repo):
    (repo / "sub").mkdir()
    kinit.init(repo / "sub", PERSON, TODAY)
    assert (repo / "kanon/kanon.toml").exists() and (repo / "AGENTS.md").exists()
    assert not (repo / "sub/kanon").exists() and not (repo / "sub/AGENTS.md").exists()


def test_incomplete_agents_section_is_reported_not_ignored(repo):
    (repo / "AGENTS.md").write_text(f"# Mine\n{kinit.START}\n")
    result = kinit.init(repo, PERSON, TODAY)
    assert (repo / "AGENTS.md").read_text() == f"# Mine\n{kinit.START}\n"
    assert result.warnings and "incomplete Kanon section" in result.warnings[0]


def test_invalid_approver_is_refused_before_writing(repo):
    with pytest.raises(ValueError, match="role@host"):
        kinit.init(repo, Person("owner", "Ada", "", "", "just me"), TODAY)
    assert files_in(repo) == []


def test_level_question_treats_closed_input_as_skip():
    def closed(_):
        raise EOFError
    assert kinit.ask_level(closed) == ("", "")


def test_cli_does_not_ask_outside_a_repository(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("asked a question"))
    assert main(["init"]) == 2
    assert "not inside a Git repository" in capsys.readouterr().out


def test_cli_keeps_an_existing_profile_without_asking(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    assert main(["init", "--non-interactive", "--approver", "owner@laptop"]) == 0
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("asked a question"))
    assert main(["init", "--approver", "owner@laptop"]) == 0
    assert "Profile kept" in capsys.readouterr().out
