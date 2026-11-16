"""Document types Kanon manages, and the rules each must satisfy (ADR-009)."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

import yaml

REQUIRED_FRONTMATTER = ("type", "status", "updated")


@dataclass(frozen=True)
class DocType:
    name: str
    statuses: tuple[str, ...]
    summary_marker: str = "> **Summary:**"
    sections: tuple[str, ...] = field(default_factory=tuple)


DOC_TYPES: dict[str, DocType] = {
    t.name: t
    for t in (
        DocType(
            "work",
            ("planning", "in-progress", "awaiting-approval", "complete", "parked"),
            sections=("Plan", "Questions", "Review", "Decision", "Cost"),
        ),
        DocType(
            "decision",
            ("proposed", "accepted", "superseded"),
            summary_marker="> **Decision:**",
            sections=("Context", "Decision", "Basis", "Consequences"),
        ),
        DocType("review-list", ("current",)),
        DocType("status", ("current",)),
        DocType("standard", ("proposed", "accepted", "superseded")),
        DocType("learnings", ("current",)),
        DocType("doc", ("draft", "current", "superseded")),
        DocType("sources", ("reference",)),
        DocType("archive", ("superseded",), summary_marker="> **Archived"),
    )
}

PERSON_LEVELS = ("new-to-software", "some-experience", "developer", "specialist")

_FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
_HEADING = re.compile(r"^## (?:\d+\.\s+)?(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Problem:
    rule: str
    message: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.message}"


def normalise(text: str) -> str:
    """Strip a UTF-8 byte order mark and convert CRLF and CR line endings to LF."""
    return text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")


_FENCE = re.compile(r"^[ \t]*(```|~~~)")


def strip_fences(lines: list[str]) -> tuple[list[str], int | None]:
    """Blank fenced code blocks (``` or ~~~). Returns the lines and the index of an unclosed fence."""
    out, opener, opened_at = [], None, None
    for index, line in enumerate(lines):
        match = _FENCE.match(line)
        if opener is None and match:
            opener, opened_at = match.group(1), index
            out.append("")
        elif opener is not None:
            if match and match.group(1) == opener:
                opener = None
            out.append("")
        else:
            out.append(line)
    return out, (opened_at if opener is not None else None)


def _without_fences(body: str) -> str:
    """Body text with fenced code blocks blanked, so their contents are not read as structure."""
    return "\n".join(strip_fences(body.split("\n"))[0])


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter, body). Frontmatter is None when absent, unparseable or not a mapping."""
    text = normalise(text)
    match = _FRONTMATTER.match(text)
    if not match:
        return None, text
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except (yaml.YAMLError, ValueError, RecursionError):
        return None, text[match.end():]
    return (data if isinstance(data, dict) else None), text[match.end():]


def validate(text: str) -> list[Problem]:
    """Return every rule the document breaks; an empty list means it is valid."""
    meta, body = split_frontmatter(text)
    if meta is None:
        return [Problem("frontmatter", "missing or unreadable frontmatter block")]

    problems = [
        Problem("frontmatter", f"missing required field '{key}'")
        for key in REQUIRED_FRONTMATTER
        if key not in meta
    ]
    raw_type = meta.get("type")
    doc_type = DOC_TYPES.get(raw_type) if isinstance(raw_type, str) else None
    if "type" in meta and doc_type is None:
        shown = raw_type if isinstance(raw_type, str) else f"<{type(raw_type).__name__}>"
        problems.append(Problem("frontmatter", f"unknown type '{shown[:60]}'"))
    updated = meta.get("updated")
    if "updated" in meta and (not isinstance(updated, dt.date) or isinstance(updated, dt.datetime)):
        problems.append(Problem("frontmatter", "field 'updated' must be a date (YYYY-MM-DD)"))
    if doc_type is None:
        return problems

    status = meta.get("status")
    if "status" in meta and (not isinstance(status, str) or status not in doc_type.statuses):
        allowed = ", ".join(doc_type.statuses)
        shown = status if isinstance(status, str) else f"<{type(status).__name__}>"
        problems.append(Problem("frontmatter", f"status '{shown[:60]}' is not one of: {allowed}"))
    body = _without_fences(body)
    if doc_type.summary_marker not in body:
        problems.append(Problem("summary", f"missing summary block starting '{doc_type.summary_marker}'"))

    headings = [h.strip() for h in _HEADING.findall(body)]
    position = -1
    for section in doc_type.sections:
        if section not in headings:
            problems.append(Problem("sections", f"missing section '{section}'"))
            continue
        index = headings.index(section)
        if index < position:
            problems.append(Problem("sections", f"section '{section}' is out of order"))
        position = max(position, index)
    return problems
