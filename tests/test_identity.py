"""AC-1: agents commit as the Kanon App (agent-commit-identity)."""

import datetime as dt
import json
import os
import subprocess
import tomllib

import pytest

from kanon import github
from kanon import init as kinit
from kanon import sync as ksync

NAME = "kanon-ada[bot]"
EMAIL = "42+kanon-ada[bot]@users.noreply.github.com"
WANTED = {"GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL, "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": EMAIL}


def git(repo, *args, env=None):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True,
                          env={**os.environ, **env} if env else None).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    kinit.init(tmp_path, ["ada-dev"], dt.date(2026, 11, 25))
    return tmp_path


def set_github(repo, body):
    path = repo / "kanon/kanon.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.rstrip("\n") + "\n\n[github]\n" + body, encoding="utf-8", newline="\n")


def env_of(repo):
    return json.loads((repo / ksync.SETTINGS_LOCAL).read_text(encoding="utf-8")).get("env")


def set_env(repo, env):
    path = repo / ksync.SETTINGS_LOCAL
    settings = json.loads(path.read_text(encoding="utf-8"))
    settings["env"] = env
    path.write_text(json.dumps(settings), encoding="utf-8")


def test_sync_writes_the_identity_keeps_other_keys_and_is_stable(repo):
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    ksync.sync(repo)
    set_env(repo, {**env_of(repo), "OTHER": "kept"})
    ksync.sync(repo)
    assert env_of(repo) == {**WANTED, "OTHER": "kept"}
    before = (repo / ksync.SETTINGS_LOCAL).read_bytes()
    assert ksync.SETTINGS_LOCAL not in ksync.sync(repo).written
    assert (repo / ksync.SETTINGS_LOCAL).read_bytes() == before


def test_the_name_follows_app_slug(repo):
    set_github(repo, 'app_id = 7\napp_slug = "other-app"\nbot_user_id = 9\n')
    ksync.sync(repo)
    assert env_of(repo)["GIT_AUTHOR_EMAIL"] == "9+other-app[bot]@users.noreply.github.com"
    assert env_of(repo)["GIT_COMMITTER_NAME"] == "other-app[bot]"


def test_removing_bot_user_id_removes_keys_in_kanons_form(repo):
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    ksync.sync(repo)
    set_env(repo, {**env_of(repo), "OTHER": "kept"})
    path = repo / "kanon/kanon.toml"
    path.write_text(path.read_text(encoding="utf-8").replace("bot_user_id = 42\n", ""), encoding="utf-8")
    notes = ksync.sync(repo).notes
    assert env_of(repo) == {"OTHER": "kept"}
    assert any("no [github] bot_user_id" in n for n in notes)


def test_a_missing_bot_user_id_prints_a_note_and_writes_nothing(repo):
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\n')
    notes = ksync.sync(repo).notes
    assert env_of(repo) is None
    assert any("no [github] bot_user_id" in n and "kanon github check" in n for n in notes)


def test_without_a_github_table_nothing_is_written_or_noted(repo):
    notes = ksync.sync(repo).notes
    assert env_of(repo) is None and not any("bot_user_id" in n for n in notes)


@pytest.mark.parametrize("owner_env", [
    {"GIT_AUTHOR_NAME": "Ada Lovelace"},
    {**WANTED, "GIT_COMMITTER_EMAIL": "ada@example.com"},  # one key owner-set, the others in Kanon's form
    {"GIT_AUTHOR_NAME": "Kanon-Ada[bot]"},  # differs from Kanon's form only in case
])
def test_an_owner_set_value_leaves_every_key_unchanged(repo, owner_env):
    ksync.sync(repo)
    set_env(repo, owner_env)
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    notes = ksync.sync(repo).notes
    assert env_of(repo) == owner_env
    assert any("holds a value Kanon did not write" in n for n in notes)


@pytest.mark.parametrize("body, problem", [
    ('app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = "42"\n', "not a positive whole number"),
    ('app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 0\n', "not a positive whole number"),
    ('app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = true\n', "not a positive whole number"),
    ('app_id = 7\nbot_user_id = 42\n', "app_slug"),
    ('app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\nbroken = \n', "could not be read"),
])
def test_an_unusable_setting_leaves_the_keys_untouched(repo, body, problem):
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    ksync.sync(repo)
    path = repo / "kanon/kanon.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text[:text.index("[github]")] + "[github]\n" + body, encoding="utf-8")
    notes = ksync.sync(repo).notes
    assert env_of(repo) == WANTED
    assert any("left as it is" in n and problem in n for n in notes)


def test_an_env_that_is_not_an_object_is_left_alone(repo):
    ksync.sync(repo)
    set_env(repo, ["not", "an", "object"])
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    notes = ksync.sync(repo).notes
    assert env_of(repo) == ["not", "an", "object"]
    assert any("'env' that is not an object" in n for n in notes)


def test_without_the_guard_hook_the_identity_is_not_set(repo):
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ksync.SETTINGS_LOCAL).write_text(json.dumps({"hooks": []}), encoding="utf-8")
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    ksync.sync(repo)
    assert env_of(repo) is None


def test_a_commit_under_the_written_variables_is_the_apps(repo):
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    ksync.sync(repo)
    git(repo, "config", "user.name", "Ada Lovelace")
    git(repo, "config", "user.email", "ada@example.com")
    git(repo, "commit", "-q", "--allow-empty", "-m", "probe", env=env_of(repo))
    assert git(repo, "log", "-1", "--format=%an <%ae>|%cn <%ce>") == f"{NAME} <{EMAIL}>|{NAME} <{EMAIL}>"


def test_commit_identity_is_empty_without_bot_user_id(repo):
    assert github.commit_identity(repo) == {}
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    assert github.commit_identity(repo) == WANTED


# ---------------------------------------------------------------- check and setup

APP = {"id": 7, "slug": "kanon-ada", "name": "Kanon (ada)"}


def fake_check(monkeypatch, repo, bot=42):
    monkeypatch.setattr(github, "sign_in", lambda root: github.Session("ada-dev/project", "t", {"id": 9}, APP, {}))

    def call(method, path, token=None, body=None, kind="token"):
        if path == "/users/kanon-ada%5Bbot%5D" and bot is not None:
            return {"id": bot}
        raise github.GitHubError(f"GitHub {method} {path}: 404 Not Found")
    monkeypatch.setattr(github, "call", call)


def test_check_prints_bot_user_id_alone_when_only_it_is_missing(repo, monkeypatch):
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\n')
    fake_check(monkeypatch, repo)
    lines = github.check(repo)
    assert lines[-1] == "bot_user_id = 42" and "under [github]" in lines[-3]
    assert "[github]" not in lines


def test_check_says_replace_the_table_when_the_app_differs(repo, monkeypatch):
    set_github(repo, 'app_id = 5\napp_slug = "old-app"\n')
    fake_check(monkeypatch, repo)
    lines = github.check(repo)
    lead = next(l for l in lines if "[github] table" in l)
    block = "\n".join(lines[lines.index("[github]"):])
    assert lead.startswith("Replace the [github] table")
    assert tomllib.loads(block) == {"github": {"app_id": 7, "app_slug": "kanon-ada", "bot_user_id": 42}}


def test_check_prints_nothing_when_all_match(repo, monkeypatch):
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\nbot_user_id = 42\n')
    fake_check(monkeypatch, repo)
    lines = github.check(repo)
    assert not any("bot_user_id" in l or "[github]" in l for l in lines)


def test_check_reports_a_failed_lookup(repo, monkeypatch):
    set_github(repo, 'app_id = 7\napp_slug = "kanon-ada"\n')
    fake_check(monkeypatch, repo, bot=None)
    assert any(l.startswith("Bot user ID: could not be read") for l in github.check(repo))


def test_the_github_table_is_rewritten_keeping_other_keys():
    text = 'name = "x"\n\n[github]\napp_id = 5\nnote = "kept"\napp_slug = "old"\nbot_user_id = 1\n\n[other]\na = 1\n'
    new = github.github_table(text, 7, "kanon-ada", 42)
    assert tomllib.loads(new) == {"name": "x", "github": {"app_id": 7, "note": "kept", "app_slug": "kanon-ada",
                                                          "bot_user_id": 42}, "other": {"a": 1}}


def test_a_failed_lookup_removes_the_earlier_apps_bot_user_id():
    text = '[github]\napp_id = 5\napp_slug = "old"\nbot_user_id = 1\nnote = "kept"\n'
    assert tomllib.loads(github.github_table(text, 7, "kanon-ada", None)) == {
        "github": {"app_id": 7, "app_slug": "kanon-ada", "note": "kept"}}


def test_a_missing_table_is_added_with_the_bot_user_id():
    new = github.github_table('name = "x"\n', 7, "kanon-ada", 42)
    assert tomllib.loads(new) == {"name": "x", "github": {"app_id": 7, "app_slug": "kanon-ada", "bot_user_id": 42}}


def test_a_commented_or_spaced_header_is_updated_in_place():  # D-1
    for header in ("[github] # the App", "[ github ]"):
        new = github.github_table(f'{header}\napp_id = 5\napp_slug = "old"\n', 7, "kanon-ada", 42)
        assert tomllib.loads(new) == {"github": {"app_id": 7, "app_slug": "kanon-ada", "bot_user_id": 42}}


@pytest.mark.parametrize("text", [
    'github = { app_id = 5, app_slug = "old" }\n',
    'github.app_id = 5\ngithub.app_slug = "old"\n',
    '[github]\n"app_id" = 5\napp_slug = "old"\n',
])
def test_an_unusual_layout_is_refused_rather_than_duplicated(text):  # D-1
    with pytest.raises(ValueError, match="could not be updated safely"):
        github.github_table(text, 7, "kanon-ada", 42)


def test_crlf_text_is_updated_in_place():  # D-3
    new = github.github_table('[github]\r\napp_id = 5\r\napp_slug = "old"\r\n', 7, "kanon-ada", 42)
    assert tomllib.loads(new) == {"github": {"app_id": 7, "app_slug": "kanon-ada", "bot_user_id": 42}}


def test_check_says_replace_for_an_inline_github_table(repo, monkeypatch):  # D-1
    path = repo / "kanon/kanon.toml"
    path.write_text('github = { app_id = 5 }\n' + path.read_text(encoding="utf-8"), encoding="utf-8")  # a root key
    fake_check(monkeypatch, repo)
    assert any(l.startswith("Replace the [github] table") for l in github.check(repo))


def test_check_skips_the_lookup_without_a_slug(repo, monkeypatch):  # D-5
    fake_check(monkeypatch, repo)
    monkeypatch.setattr(github, "sign_in", lambda root: github.Session("ada-dev/project", "t", {"id": 9}, {"id": 7}, {}))
    lines = github.check(repo)
    assert any("no App slug" in l for l in lines) and not any("None%5Bbot" in l for l in lines)


@pytest.mark.parametrize("value", ['"42"', "0", "-1", "true"])
def test_settings_refuse_a_bad_bot_user_id(value):  # D-4
    from kanon.settings import validate_settings
    problems = validate_settings(f'[github]\napp_id = 7\napp_slug = "kanon-ada"\nbot_user_id = {value}\n')
    assert any("bot_user_id" in p.message for p in problems)
