import datetime as dt
import hashlib
import json
import os
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
# Windows os.chmod sets only the read-only flag; the profile folder relies on the user profile's ACL there.
POSIX_MODES = os.name != "nt"
TODAY = dt.date(2026, 11, 16)
APPROVERS = ["ada-dev"]
COMMITTED = sorted([
    "kanon/docs/roadmap.md", "kanon/kanon.toml", "kanon/sources.md",
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
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)


def committed_and_generated(root):
    return [f for f in files_in(root) if not f.startswith("kanon/local/")]


def snapshot(root):
    return {f: (root / f).read_bytes() for f in committed_and_generated(root)}


def untracked_or_changed(repo):
    return [l[3:] for l in git(repo, "status", "--porcelain", "--untracked-files=all").splitlines()]


def test_init_writes_shared_files_and_generated_files(repo):
    kinit.init(repo, APPROVERS, TODAY)
    assert sorted(set(committed_and_generated(repo)) - set(ksync.GENERATED) - set(ksync.PERSONAL)) == COMMITTED
    assert all((repo / p).exists() for p in ("kanon/local/DESK.md", "kanon/local/desk.html", "kanon/local/STATUS.md"))
    assert set(ksync.GENERATED) <= set(files_in(repo))


def test_generated_files_never_show_in_git_status(repo):
    kinit.init(repo, APPROVERS, TODAY)
    assert sorted(untracked_or_changed(repo)) == COMMITTED


def test_init_never_creates_agents_claude_or_claude_local(repo):
    kinit.init(repo, APPROVERS, TODAY)
    for name in ("AGENTS.md", "CLAUDE.md", "CLAUDE.local.md"):
        assert not (repo / name).exists()


def test_existing_agents_and_claude_files_are_byte_identical(repo):
    (repo / "AGENTS.md").write_text("# Team agents\nKeep.\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    before = {n: hashlib.sha256((repo / n).read_bytes()).hexdigest() for n in ("AGENTS.md", "CLAUDE.md")}
    kinit.init(repo, APPROVERS, TODAY)
    ksync.sync(repo)
    assert {n: hashlib.sha256((repo / n).read_bytes()).hexdigest() for n in before} == before


def test_every_committed_document_is_valid(repo):
    kinit.init(repo, APPROVERS, TODAY)
    for doc in (repo / "kanon").rglob("*.md"):
        if "local" not in doc.parts:
            assert validate(doc.read_text(encoding="utf-8")) == [], doc
    assert validate_settings((repo / "kanon/kanon.toml").read_text(encoding="utf-8")) == []


def test_second_run_changes_nothing(repo):
    kinit.init(repo, APPROVERS, TODAY)
    before = snapshot(repo)
    result = kinit.init(repo, ["someone-else"], dt.date(2027, 1, 1))
    assert snapshot(repo) == before
    assert result.created == [] and result.updated == []


def test_existing_files_are_never_overwritten(repo):
    (repo / "kanon").mkdir()
    (repo / "kanon/STATUS.md").write_text("mine", encoding="utf-8")
    (repo / ".claude/rules").mkdir(parents=True)
    (repo / ".claude/rules/kanon.md").write_text("my own rules", encoding="utf-8")
    result = kinit.init(repo, APPROVERS, TODAY)
    assert (repo / "kanon/STATUS.md").read_text(encoding="utf-8") == "mine"
    assert (repo / ".claude/rules/kanon.md").read_text(encoding="utf-8") == "my own rules"
    assert any("not written by Kanon" in w for w in result.warnings)


def test_gitignore_block_is_added_once_and_keeps_other_lines(repo):
    (repo / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    kinit.init(repo, APPROVERS, TODAY)
    ksync.sync(repo)
    text = (repo / ".gitignore").read_text(encoding="utf-8")
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
        (clone / f"kanon/work/{who}.txt").write_text(who, encoding="utf-8")
        git(clone, "add", "-A")
        git(clone, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--no-verify", "-m", who)
        clones.append(clone)
    a, b = clones
    git(b, "-c", "user.name=t", "-c", "user.email=t@t", "pull", "-q", "--no-rebase", "--no-edit", str(a))
    assert "Ada secret" not in git(b, "log", "-p", "--all") and "Bo secret" not in git(b, "log", "-p", "--all")
    assert "Bo secret" in (b / ".claude/rules/kanon-person.md").read_text(encoding="utf-8")


def test_profile_sources_and_precedence(tmp_path, monkeypatch):
    assert profiles.load() is None
    saved = profiles.save(profiles.Profile(github="file-user", level="developer"))
    assert not POSIX_MODES or saved.stat().st_mode & 0o077 == 0
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
    assert "At first contact, ask" in (repo / ".claude/rules/kanon-person.md").read_text(encoding="utf-8")


def test_profile_reaches_the_person_rules(repo, monkeypatch):
    monkeypatch.setenv("KANON_PROFILE", json.dumps(
        {"github": "ada-dev", "name": "Ada", "level": "developer", "preferences": ["Keep chat short."]}))
    kinit.init(repo, APPROVERS, TODAY)
    text = (repo / ".claude/rules/kanon-person.md").read_text(encoding="utf-8")
    assert "# Working With Ada" in text and "Keep chat short." in text and "precise technical language" in text


def test_kanon_rules_embed_the_projects_conduct_standard(repo):
    kinit.init(repo, APPROVERS, TODAY)
    path = repo / "kanon/docs/conduct-and-writing.md"
    path.write_text(path.read_text(encoding="utf-8").replace("## 1. Working with People", "## 1. Working with People Here"), encoding="utf-8")
    ksync.sync(repo)
    assert "### 1. Working with People Here" in (repo / ".claude/rules/kanon.md").read_text(encoding="utf-8")


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
    assert tomllib.loads((repo / "kanon/kanon.toml").read_text(encoding="utf-8"))["kanon"]["approvers"] == ["ada-dev"]


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
        text = (ROOT / dest).read_text(encoding="utf-8")
        date = next(l.split(": ")[1] for l in text.splitlines() if l.startswith("updated:"))
        assert text == render(src, date=date), dest
    conduct = (ROOT / "kanon/docs/conduct-and-writing.md").read_text(encoding="utf-8")
    date = next(l.split(": ")[1] for l in conduct.splitlines() if l.startswith("updated:"))
    assert conduct == render("conduct-and-writing.md", date=date)


def test_marker_elsewhere_in_a_file_does_not_make_it_generated(repo):
    kinit.init(repo, APPROVERS, TODAY)
    (repo / ".claude/rules/team.md").write_text(f"# Team\n\nA seamless note.\n{ksync.MARKER}\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text(f"# Mine\n\nA robust plan.\n{ksync.MARKER}\n", encoding="utf-8")
    from kanon import verify as kv
    found = [(f.path, f.rule) for f in kv.verify(repo)]
    assert (".claude/rules/team.md", "writing") in found and ("CLAUDE.md", "writing") in found
    (repo / ".claude/rules/kanon.md").write_text(f"# Quoted\n\n{ksync.MARKER}\n", encoding="utf-8")
    assert ".claude/rules/kanon.md" in ksync.sync(repo).refused


def test_damaged_gitignore_block_is_refused_not_rewritten(repo):
    (repo / ".gitignore").write_text(f"foo\n{ksync.IGNORE_START}\n/x\n", encoding="utf-8")
    result = ksync.sync(repo)
    assert ".gitignore" in result.refused
    assert (repo / ".gitignore").read_text(encoding="utf-8") == f"foo\n{ksync.IGNORE_START}\n/x\n"


def test_profile_problems_are_reported_and_blank_env_is_unset(repo, monkeypatch):
    monkeypatch.setenv("KANON_PROFILE", '{"level": "wizard", "github": "x y"}')
    notes = ksync.sync(repo).notes
    assert any("level 'wizard'" in n for n in notes) and any("GitHub username" in n for n in notes)
    monkeypatch.setenv("KANON_PROFILE", "   ")
    assert profiles.load() is None


@pytest.mark.skipif(not POSIX_MODES, reason="POSIX permission bits do not apply on Windows")
def test_profile_folder_is_private():
    profiles.default_path().parent.mkdir(mode=0o755, parents=True)
    os.chmod(profiles.default_path().parent, 0o755)
    path = profiles.save(profiles.Profile(github="ada-dev"))
    assert path.parent.stat().st_mode & 0o077 == 0 and path.stat().st_mode & 0o077 == 0


@pytest.mark.skipif(not POSIX_MODES, reason="POSIX permission bits do not apply on Windows")
def test_a_chosen_profile_folder_keeps_its_permissions(monkeypatch, tmp_path):
    shared = tmp_path / "shared"
    shared.mkdir()
    os.chmod(shared, 0o755)
    monkeypatch.setenv("KANON_PROFILE_FILE", str(shared / "p.toml"))
    path = profiles.save(profiles.Profile(github="ada-dev"))
    assert shared.stat().st_mode & 0o777 == 0o755 and path.stat().st_mode & 0o077 == 0


def test_sync_explains_a_damaged_ignore_block(repo, monkeypatch, capsys):
    from kanon.cli import main
    from kanon.sync import IGNORE_START
    kinit.init(repo, APPROVERS, TODAY)
    (repo / ".gitignore").write_text(IGNORE_START + "\n/.claude/rules/kanon.md\n", encoding="utf-8")
    monkeypatch.chdir(repo)
    assert main(["sync"]) == 1
    out = capsys.readouterr().out
    assert "Refused   .gitignore: its Kanon block is damaged (see note)" in out
    assert "not written by Kanon" not in out.split("Refused   .gitignore")[1].splitlines()[0]


def test_a_committed_generated_file_is_a_finding(repo):
    kinit.init(repo, APPROVERS, TODAY)
    git(repo, "add", "-f", ".claude/rules/kanon-person.md")
    from kanon import verify as kv
    assert any(f.rule == "privacy" and f.path == ".claude/rules/kanon-person.md" for f in kv.verify(repo))


def test_a_marker_on_line_one_outside_generated_paths_is_still_checked(repo):
    kinit.init(repo, APPROVERS, TODAY)
    (repo / ".claude/rules/team.md").write_text(f"{ksync.MARKER}\n# Team\n\nA seamless note.\n", encoding="utf-8")
    from kanon import verify as kv
    assert (".claude/rules/team.md", "writing") in [(f.path, f.rule) for f in kv.verify(repo)]


def test_role_templates_never_send_agents_to_kanon_toml_for_profiles():
    roles = Path(kinit.__file__).parent / "templates" / "roles"
    for template in roles.glob("*.md"):
        for line in template.read_text(encoding="utf-8").splitlines():
            if "kanon.toml" in line:
                assert not any(w in line.lower() for w in ("profile", "level", "preference")), (template.name, line)


def test_a_stale_install_in_kanons_own_repository_is_reported(tmp_path, monkeypatch):
    import shutil
    from importlib.resources import files as package_files
    root = tmp_path / "engine"
    shutil.copytree(Path(str(package_files("kanon"))), root / "src" / "kanon",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (root / "pyproject.toml").write_text('[project]\nname = "kanon-engine"\n')
    assert ksync.stale_install(root) is None
    (root / "src" / "kanon" / "guard.py").write_text("# changed\n")
    assert "uv tool install --force ." in ksync.stale_install(root)
    (root / "src" / "kanon" / "guard.py").write_bytes((Path(str(package_files("kanon"))) / "guard.py").read_bytes())  # bytes: write_text adds CR on Windows
    extra = root / "src" / "kanon" / "extra.py"
    extra.write_text("x = 1\n")  # an added file
    assert ksync.stale_install(root)
    extra.rename(root / "extra.py")
    (root / "pyproject.toml").write_text('[project]\nname="kanon-engine"\n')  # other spacing
    assert ksync.stale_install(root) is None
    (root / "pyproject.toml").write_text('[project]\nname = "other"\n')
    assert ksync.stale_install(root) is None


def test_an_editable_install_is_never_stale(tmp_path, monkeypatch):
    import importlib.resources
    import shutil
    from importlib.resources import files as package_files
    root = tmp_path / "engine"
    shutil.copytree(Path(str(package_files("kanon"))), root / "src" / "kanon", ignore=shutil.ignore_patterns("__pycache__"))
    (root / "pyproject.toml").write_text('[project]\nname = "kanon-engine"\n')
    (root / "src" / "kanon" / "guard.py").write_text("# edited in the working tree\n")
    monkeypatch.setattr(importlib.resources, "files", lambda name: root / "src" / "kanon")
    assert ksync.stale_install(root) is None  # the running package is the working tree


def test_a_malformed_pyproject_is_not_reported(tmp_path):
    (tmp_path / "src" / "kanon").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project\nname = ")
    assert ksync.stale_install(tmp_path) is None
