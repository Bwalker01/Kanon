"""`kanon init`: lay out a repository for Kanon without overwriting anything (P1-03)."""

from __future__ import annotations

import datetime as dt
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from kanon.schema import PERSON_LEVELS
from kanon.settings import Person, render_settings
from kanon.templates import render

START, END = "<!-- kanon:start -->", "<!-- kanon:end -->"

LEVEL_QUESTION = """How would you describe your technical background?
  1. New to software: has not used Git or a terminal
  2. Some experience: uses Git and an editor, not a developer
  3. Developer: writes and reviews code
  4. Specialist: deep expertise in this project's field
Choose 1-4 (Enter to skip): """


@dataclass
class InitResult:
    created: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)


def is_git_repo(root: Path) -> bool:
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root,
                            capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() == "true"


def ask_level(read: Callable[[str], str] = input) -> tuple[str, str]:
    """Ask the technical-level question. Returns (level, description in the person's words)."""
    answer = read(LEVEL_QUESTION).strip()
    if answer not in {"1", "2", "3", "4"}:
        return "", ""
    level = PERSON_LEVELS[int(answer) - 1]
    description = read("Anything to add about your background (Enter to skip): ").strip()
    return level, description


def _write_new(root: Path, rel: str, content: str, result: InitResult) -> None:
    path = root / rel
    if path.exists():
        result.kept.append(rel)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    result.created.append(rel)


def _ensure_agents(root: Path, result: InitResult) -> None:
    path = root / "AGENTS.md"
    section = render("agents-section.md")
    if not path.exists():
        path.write_text(f"# Agent Instructions\n\n{section}", encoding="utf-8")
        result.created.append("AGENTS.md")
    elif START in path.read_text(encoding="utf-8"):
        result.kept.append("AGENTS.md")
    else:
        existing = path.read_text(encoding="utf-8")
        path.write_text(existing.rstrip("\n") + "\n\n" + section, encoding="utf-8")
        result.updated.append("AGENTS.md")


def _ensure_claude(root: Path, result: InitResult) -> None:
    path = root / "CLAUDE.md"
    if not path.exists():
        path.write_text("@AGENTS.md\n", encoding="utf-8")
        result.created.append("CLAUDE.md")
    elif "@AGENTS.md" in path.read_text(encoding="utf-8").split():
        result.kept.append("CLAUDE.md")
    else:
        existing = path.read_text(encoding="utf-8")
        path.write_text(existing.rstrip("\n") + "\n\n@AGENTS.md\n", encoding="utf-8")
        result.updated.append("CLAUDE.md")


def init(root: Path, person: Person, today: dt.date | None = None) -> InitResult:
    if not is_git_repo(root):
        raise RuntimeError(f"{root} is not a Git repository; run 'git init' first")
    date = (today or dt.date.today()).isoformat()
    result = InitResult()
    files = {
        "kanon/REVIEW.md": render("review.md", date=date),
        "kanon/STATUS.md": render("status.md", date=date),
        "kanon/docs/conduct-and-writing.md": render("conduct-and-writing.md", date=date),
        "kanon/docs/learnings.md": render("learnings.md", date=date),
        "kanon/decisions/.gitkeep": "",
        "kanon/work/.gitkeep": "",
        "kanon/archive/.gitkeep": "",
        "kanon/kanon.toml": render_settings(person),
    }
    for rel, content in files.items():
        folder = (root / rel).parent
        if rel.endswith(".gitkeep") and folder.is_dir() and any(folder.iterdir()):
            continue  # the folder already has content to keep it in Git
        _write_new(root, rel, content, result)
    _ensure_agents(root, result)
    _ensure_claude(root, result)
    return result
