"""Document templates, rendered with string.Template placeholders."""

from __future__ import annotations

from importlib.resources import files
from string import Template

TEMPLATE_NAMES = (
    "work.md", "decision.md", "review.md", "status.md", "doc.md", "learnings.md",
    "conduct-and-writing.md", "rules-kanon.md", "rules-person.md", "sources.md",
    "roles/metis.md", "roles/kritos.md", "roles/clio.md", "roles/mnemon.md",
    "claude/skills/kanon-metis/SKILL.md", "claude/skills/kanon-clio/SKILL.md",
    "claude/skills/kanon-mnemon/SKILL.md", "claude/agents/kritos-reviewer.md",
)
ROLE_FILES = {f"kanon/docs/roles/{r}.md": f"roles/{r}.md" for r in ("metis", "kritos", "clio", "mnemon")}
CLAUDE_FILES = {
    ".claude/skills/kanon-metis/SKILL.md": "claude/skills/kanon-metis/SKILL.md",
    ".claude/skills/kanon-clio/SKILL.md": "claude/skills/kanon-clio/SKILL.md",
    ".claude/skills/kanon-mnemon/SKILL.md": "claude/skills/kanon-mnemon/SKILL.md",
    ".claude/agents/kritos-reviewer.md": "claude/agents/kritos-reviewer.md",
}


def render(name: str, **values: str) -> str:
    if name not in TEMPLATE_NAMES:
        raise KeyError(f"unknown template '{name}'")
    resource = files(__package__)
    for part in name.split("/"):
        resource = resource.joinpath(part)
    text = resource.read_text(encoding="utf-8")
    return Template(text).substitute(values)
