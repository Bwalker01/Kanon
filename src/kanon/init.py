"""`kanon init`: lay out a repository for Kanon without overwriting anything (P1-03)."""

from __future__ import annotations

import datetime as dt
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from kanon.schema import PERSON_LEVELS
from kanon.settings import Person, render_settings, validate_settings
from kanon.templates import CLAUDE_FILES, ROLE_FILES, render
from kanon.verify import hook_location, install_hook

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
    warnings: list[str] = field(default_factory=list)


def repo_root(path: Path) -> Path | None:
    """The top level of the Git repository containing path, or None."""
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path,
                            capture_output=True, text=True)
    return Path(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else None


def has_settings(root: Path) -> bool:
    return (root / "kanon" / "kanon.toml").exists()


def ask_level(read: Callable[[str], str] = input) -> tuple[str, str]:
    """Ask the technical-level question. Returns (level, description in the person's words)."""
    try:
        answer = read(LEVEL_QUESTION).strip()
        if answer not in {"1", "2", "3", "4"}:
            return "", ""
        level = PERSON_LEVELS[int(answer) - 1]
        description = read("Anything to add about your background (Enter to skip): ").strip()
    except EOFError:  # no input available: treat as skipped
        return "", ""
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
        return
    text = path.read_text(encoding="utf-8")
    has_start, has_end = START in text, END in text
    if has_start and has_end and text.index(START) < text.index(END):
        result.kept.append("AGENTS.md")
    elif has_start or has_end:
        result.kept.append("AGENTS.md")
        result.warnings.append(
            f"AGENTS.md has an incomplete Kanon section; it needs both {START} and {END}. "
            "Remove the partial markers and run kanon init again."
        )
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


def init(path: Path, person: Person, today: dt.date | None = None) -> InitResult:
    """Lay out the repository containing path. Raises before writing anything if inputs are invalid."""
    root = repo_root(path)
    if root is None:
        raise RuntimeError(f"{path} is not inside a Git repository; run 'git init' first")
    settings = render_settings(person)
    problems = validate_settings(settings)
    if problems:
        raise ValueError("; ".join(p.message for p in problems))
    date = (today or dt.date.today()).isoformat()
    result = InitResult()
    files = {
        "kanon/REVIEW.md": render("review.md", date=date),
        "kanon/STATUS.md": render("status.md", date=date),
        "kanon/docs/conduct-and-writing.md": render("conduct-and-writing.md", date=date),
        "kanon/docs/learnings.md": render("learnings.md", date=date),
        "kanon/sources.md": render("sources.md", date=date),
        "kanon/decisions/.gitkeep": "",
        "kanon/work/.gitkeep": "",
        "kanon/archive/.gitkeep": "",
        "kanon/kanon.toml": settings,
        **{dest: render(src, date=date) for dest, src in ROLE_FILES.items()},
        **{dest: render(src) for dest, src in CLAUDE_FILES.items()},
    }
    for rel, content in files.items():
        folder = (root / rel).parent
        if rel.endswith(".gitkeep") and folder.is_dir() and any(folder.iterdir()):
            continue  # the folder already has content to keep it in Git
        _write_new(root, rel, content, result)
    _ensure_agents(root, result)
    _ensure_claude(root, result)
    hook_path = Path(hook_location(root))
    existed = hook_path.exists()
    hook, written = install_hook(root)
    ours = existed and "# Installed by kanon init." in hook_path.read_text(encoding="utf-8", errors="replace")
    if written:
        (result.updated if existed else result.created).append(".git/hooks/pre-commit")
    elif ours:
        result.kept.append(".git/hooks/pre-commit")
    else:
        result.warnings.append(f"an existing pre-commit hook was kept at {hook}; it does not run kanon verify "
                               "unless you add it")
    return result


def new_work(path: Path, topic: str, today: dt.date | None = None) -> Path:
    """Create kanon/work/YYYY-MM-DD-<topic>.md from the template. Never overwrites."""
    root = repo_root(path)
    if root is None:
        raise RuntimeError(f"{path} is not inside a Git repository")
    if not has_settings(root):
        raise RuntimeError("Kanon is not set up in this repository; run kanon init first")
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    if not slug:
        raise ValueError("the topic needs at least one letter or digit")
    date = (today or dt.date.today()).isoformat()
    target = root / "kanon" / "work" / f"{date}-{slug}.md"
    if target.exists():
        raise FileExistsError(f"{target.relative_to(root)} already exists")
    title = topic.strip()[:1].upper() + topic.strip()[1:]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render("work.md", date=date, title=title, summary="To be written with the plan."),
                      encoding="utf-8")
    return target
