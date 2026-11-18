"""Personal profiles, kept outside every repository so they are never committed or shared.

Sources, highest precedence first:
1. the KANON_PROFILE environment variable, holding the profile as TOML (for cloud sessions);
2. the file named by KANON_PROFILE_FILE;
3. $XDG_CONFIG_HOME/kanon/profile.toml, or ~/.config/kanon/profile.toml.
With none of these, agents ask the person at first contact.
"""

from __future__ import annotations

import json
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from kanon.schema import PERSON_LEVELS, Problem
from kanon.settings import GITHUB_USER, toml_string


@dataclass(frozen=True)
class Profile:
    github: str = ""
    name: str = ""
    level: str = ""
    description: str = ""
    preferences: tuple[str, ...] = field(default_factory=tuple)
    source: str = ""


def default_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "kanon" / "profile.toml"


def profile_path() -> Path:
    return Path(os.environ["KANON_PROFILE_FILE"]) if os.environ.get("KANON_PROFILE_FILE") else default_path()


def _from_data(data: dict, source: str) -> Profile:
    prefs = data.get("preferences", [])
    return Profile(
        github=str(data.get("github", "")),
        name=str(data.get("name", "")),
        level=str(data.get("level", "")),
        description=str(data.get("description", "")),
        preferences=tuple(str(p) for p in prefs) if isinstance(prefs, list) else (),
        source=source,
    )


def load() -> Profile | None:
    """The person's profile, or None when no source exists. Raises ValueError if a source is unreadable."""
    inline = os.environ.get("KANON_PROFILE", "").strip()
    if inline:
        try:
            data = json.loads(inline) if inline.lstrip().startswith("{") else tomllib.loads(inline)
        except (json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
            raise ValueError(f"KANON_PROFILE is not valid JSON or TOML: {error}") from None
        if not isinstance(data, dict):
            raise ValueError("KANON_PROFILE must hold an object")
        return _from_data(data, "KANON_PROFILE environment variable")
    path = profile_path()
    if path.is_file():
        try:
            return _from_data(tomllib.loads(path.read_text(encoding="utf-8")), str(path))
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"{path} is not valid TOML: {error}") from None
    return None


def validate(profile: Profile) -> list[Problem]:
    problems = []
    if profile.level not in ("", *PERSON_LEVELS):
        problems.append(Problem("profile", f"level '{profile.level}' is not one of: {', '.join(PERSON_LEVELS)}"))
    if profile.github and not GITHUB_USER.match(profile.github):
        problems.append(Problem("profile", f"'{profile.github}' is not a valid GitHub username"))
    return problems


def render(profile: Profile) -> str:
    lines = [
        "# Kanon personal profile. Kept outside every repository; never commit it.",
        f"github = {toml_string(profile.github)}",
        f"name = {toml_string(profile.name)}",
        f"level = {toml_string(profile.level)}",
        f"description = {toml_string(profile.description)}",
        "preferences = [" + ", ".join(toml_string(p) for p in profile.preferences) + "]",
        "",
    ]
    return "\n".join(lines)


def as_env(profile: Profile) -> str:
    """The profile as a one-line JSON value for the KANON_PROFILE environment variable."""
    data = {"github": profile.github, "name": profile.name, "level": profile.level,
            "description": profile.description, "preferences": list(profile.preferences)}
    return json.dumps(data, ensure_ascii=False) + "\n"


def save(profile: Profile, path: Path | None = None) -> Path:
    """Write the profile file (never inside a repository's tracked files). Returns its path."""
    problems = validate(profile)
    if problems:
        raise ValueError("; ".join(p.message for p in problems))
    target = path or profile_path()
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if target.parent == default_path().parent:
        os.chmod(target.parent, 0o700)  # Kanon's own folder; a folder the person chose is left as it is
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(render(profile))
    os.chmod(target, 0o600)
    return target
