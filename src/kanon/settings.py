"""Reading, writing and validating `kanon/kanon.toml`."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass

from kanon.schema import PERSON_LEVELS, Problem

ACTOR = re.compile(r"^[A-Za-z0-9._-]+@[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class Person:
    id: str
    name: str = ""
    level: str = ""
    description: str = ""
    approver: str = ""


def toml_string(value: str) -> str:
    """A TOML basic string. JSON string escapes are a subset TOML accepts."""
    return json.dumps(value, ensure_ascii=False)


def render_settings(person: Person, review_round_limit: int = 3) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", person.id):
        raise ValueError(f"person id '{person.id}' may only contain letters, digits, '-' and '_'")
    return "\n".join([
        "# Kanon settings. See kanon/docs/conduct-and-writing.md for how profiles are used.",
        "",
        "[kanon]",
        "format = 1",
        f"review_round_limit = {review_round_limit}",
        "",
        "# One table per person. level: " + ", ".join(PERSON_LEVELS) + " (empty until asked).",
        f"[people.{person.id}]",
        f"name = {toml_string(person.name)}",
        f"level = {toml_string(person.level)}",
        f"description = {toml_string(person.description)}",
        f"approver = {toml_string(person.approver)}",
        "",
    ])


def validate_settings(text: str) -> list[Problem]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return [Problem("settings", f"kanon.toml is not valid TOML: {error}")]
    problems: list[Problem] = []
    limit = data.get("kanon", {}).get("review_round_limit")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        problems.append(Problem("settings", "kanon.review_round_limit must be a whole number of at least 1"))
    people = data.get("people")
    if not isinstance(people, dict) or not people:
        problems.append(Problem("settings", "at least one [people.<id>] table is required"))
        return problems
    for pid, person in people.items():
        if not isinstance(person, dict):
            problems.append(Problem("settings", f"people.{pid} must be a table"))
            continue
        level = person.get("level", "")
        if level not in ("", *PERSON_LEVELS):
            problems.append(Problem("settings", f"people.{pid}.level '{level}' is not one of: {', '.join(PERSON_LEVELS)}"))
        approver = person.get("approver", "")
        if approver and not (isinstance(approver, str) and ACTOR.match(approver)):
            problems.append(Problem("settings", f"people.{pid}.approver must be written role@host"))
    return problems
