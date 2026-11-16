"""P1-06 acceptance: core roles as neutral prompts with thin Claude Code wrappers."""

import re

import pytest
import yaml

from kanon.schema import split_frontmatter
from kanon.templates import CLAUDE_FILES, ROLE_FILES, render
from kanon.verify import check_document

SKILLS = {d: s for d, s in CLAUDE_FILES.items() if "/skills/" in d}
REVIEWER = ".claude/agents/kritos-reviewer.md"
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def meta(src):
    data, _ = split_frontmatter(render(src))
    return data


@pytest.mark.parametrize("dest,src", SKILLS.items())
def test_skill_names_follow_agent_skills_rules(dest, src):
    name = meta(src)["name"]
    folder = dest.split("/")[-2]
    assert name == folder
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64
    assert 0 < len(meta(src)["description"]) <= 1024


@pytest.mark.parametrize("src", list(SKILLS.values()) + [CLAUDE_FILES[REVIEWER]])
def test_wrappers_are_thin_and_point_at_their_prompt(src):
    text = render(src)
    assert len(text.splitlines()) <= 30
    pointed = re.findall(r"`(kanon/docs/roles/\w+\.md)`", text)
    assert len(pointed) == 1 and pointed[0] in ROLE_FILES
    body = split_frontmatter(text)[1]
    assert "## " not in body, "procedure must live in the role prompt, not the wrapper"


@pytest.mark.parametrize("src", SKILLS.values())
def test_every_generator_names_its_paired_reviewer(src):
    assert meta(src)["metadata"]["reviewer"] == "kritos-reviewer"
    assert "`kritos-reviewer`" in render(src)


def test_reviewer_has_no_write_tools():
    tools = {t.strip() for t in meta(CLAUDE_FILES[REVIEWER])["tools"].split(",")}
    assert tools and not tools & WRITE_TOOLS


@pytest.mark.parametrize("dest,src", ROLE_FILES.items())
def test_role_prompts_pass_kanon_checks(dest, src):
    assert check_document(dest, render(src, date="2026-11-16")) == []


@pytest.mark.parametrize("src", [s for d, s in ROLE_FILES.items() if "kritos" not in d])
def test_role_prompts_reference_the_conduct_standard_and_review(src):
    text = render(src, date="2026-11-16")
    assert "kanon/docs/conduct-and-writing.md" in text or "conduct standard" in text
    assert "Kritos" in text


def test_reviewer_is_kept_from_the_creators_conversation():
    text = render(ROLE_FILES["kanon/docs/roles/kritos.md"], date="2026-11-16")
    assert "Nothing from the creator's conversation" in text
    metis = render(ROLE_FILES["kanon/docs/roles/metis.md"], date="2026-11-16")
    assert "Never pass the creator's conversation" in metis
