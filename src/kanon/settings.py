"""Shared project settings in `kanon/kanon.toml`: committed, and holding nothing personal."""

from __future__ import annotations

import json
import re
import tomllib

from kanon.schema import Problem

GITHUB_USER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")


def toml_string(value: str) -> str:
    """A TOML basic string. JSON string escapes are a subset TOML accepts."""
    return json.dumps(value, ensure_ascii=False)


def render_settings(approvers: list[str], review_round_limit: int = 3) -> str:
    listed = ", ".join(toml_string(a) for a in approvers)
    return "\n".join([
        "# Kanon shared settings. Committed: holds nothing personal.",
        "# Personal profiles live outside the repository (see `kanon profile --help`).",
        "",
        "[kanon]",
        "format = 2",
        f"review_round_limit = {review_round_limit}",
        "",
        "# GitHub usernames of the people who may approve major outputs.",
        f"approvers = [{listed}]",
        "",
    ])


def validate_settings(text: str) -> list[Problem]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return [Problem("settings", f"kanon.toml is not valid TOML: {error}")]
    problems: list[Problem] = []
    kanon = data.get("kanon", {})
    limit = kanon.get("review_round_limit")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        problems.append(Problem("settings", "kanon.review_round_limit must be a whole number of at least 1"))
    approvers = kanon.get("approvers")
    if not isinstance(approvers, list) or not approvers:
        problems.append(Problem("settings", "kanon.approvers must list at least one GitHub username"))
    else:
        for approver in approvers:
            if not (isinstance(approver, str) and GITHUB_USER.match(approver)):
                problems.append(Problem("settings", f"approver '{approver}' is not a valid GitHub username"))
    if "people" in data:
        problems.append(Problem("settings", "personal profiles must not be committed; move [people] to a profile "
                                            "(kanon profile) and remove it from kanon.toml"))
    return problems
