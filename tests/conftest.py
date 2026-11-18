import pytest


@pytest.fixture(autouse=True)
def isolated_profile(tmp_path_factory, monkeypatch):
    """Keep every test's profile out of the real home folder and environment."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))
    monkeypatch.delenv("KANON_PROFILE", raising=False)
    monkeypatch.delenv("KANON_PROFILE_FILE", raising=False)
