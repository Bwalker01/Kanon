"""Document templates, rendered with string.Template placeholders."""

from __future__ import annotations

from importlib.resources import files
from string import Template

TEMPLATE_NAMES = (
    "work.md", "decision.md", "review.md", "status.md", "doc.md", "learnings.md",
    "conduct-and-writing.md", "agents-section.md",
)


def render(name: str, **values: str) -> str:
    if name not in TEMPLATE_NAMES:
        raise KeyError(f"unknown template '{name}'")
    text = files(__package__).joinpath(name).read_text(encoding="utf-8")
    return Template(text).substitute(values)
