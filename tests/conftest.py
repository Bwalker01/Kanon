import pytest


@pytest.fixture(autouse=True)
def isolated_profile(tmp_path_factory, monkeypatch):
    """Keep every test's profile out of the real home folder and environment."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))
    monkeypatch.delenv("KANON_PROFILE", raising=False)
    monkeypatch.delenv("KANON_PROFILE_FILE", raising=False)


@pytest.fixture(autouse=True)
def isolated_git(tmp_path_factory, monkeypatch):
    """Give test repositories a clean Git configuration: no signing, hooks or user settings."""
    config = tmp_path_factory.mktemp("git") / "gitconfig"
    config.write_text("[user]\n\tname = Test\n\temail = test@example.com\n[init]\n\tdefaultBranch = main\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
