"""`kanon init` and `kanon new`: lay out a repository for Kanon without overwriting anything."""

from __future__ import annotations

import datetime as dt
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from kanon.schema import PERSON_LEVELS
from kanon.settings import render_settings, validate_settings
from kanon.sync import sync
from kanon.templates import ROLE_FILES, render
from kanon.verify import hook_location, install_hook

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


def ask(prompt: str, read: Callable[[str], str] | None = None) -> str:
    """Ask one free-text question; closed input counts as no answer."""
    read = read or input
    try:
        return read(prompt).strip()
    except EOFError:
        return ""


def ask_level(read: Callable[[str], str] | None = None) -> tuple[str, str]:
    """Ask the technical-level question. Returns (level, description in the person's words)."""
    read = read or input
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


def init(path: Path, approvers: list[str], today: dt.date | None = None) -> InitResult:
    """Lay out the repository containing path. Raises before writing anything if inputs are invalid.

    Writes only shared, committed files under kanon/ and the Kanon block of .gitignore, then runs
    `kanon sync` for the generated agent files. Never creates or edits AGENTS.md, CLAUDE.md or
    CLAUDE.local.md.
    """
    root = repo_root(path)
    if root is None:
        raise RuntimeError(f"{path} is not inside a Git repository; run 'git init' first")
    settings = None
    if not has_settings(root):
        settings = render_settings(approvers)
        problems = validate_settings(settings)
        if problems:
            raise ValueError("; ".join(p.message for p in problems))
    date = (today or dt.date.today()).isoformat()
    result = InitResult()
    files = {
        "kanon/docs/roadmap.md": render("roadmap.md", date=date),
        "kanon/docs/conduct-and-writing.md": render("conduct-and-writing.md", date=date),
        "kanon/docs/learnings.md": render("learnings.md", date=date),
        "kanon/sources.md": render("sources.md", date=date),
        "kanon/decisions/.gitkeep": "",
        "kanon/work/.gitkeep": "",
        "kanon/archive/.gitkeep": "",
        **({"kanon/kanon.toml": settings} if settings else {}),
        **{dest: render(src, date=date) for dest, src in ROLE_FILES.items()},
    }
    for rel, content in files.items():
        folder = (root / rel).parent
        if rel.endswith(".gitkeep") and folder.is_dir() and any(folder.iterdir()):
            continue  # the folder already has content to keep it in Git
        _write_new(root, rel, content, result)
    synced = sync(root)
    from kanon.desk import OUTPUTS
    result.created += [f for f in synced.written if f != ".gitignore" and f not in OUTPUTS]
    if ".gitignore" in synced.written:
        result.updated.append(".gitignore")
    result.kept += synced.unchanged
    result.warnings += [f"{f} exists and was not written by Kanon; it was left alone" for f in synced.refused]
    result.warnings += synced.notes
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
    clash = sorted((root / "kanon" / "work").glob(f"????-??-??-{slug}.md"))
    if target.exists() or clash:
        existing = (clash or [target])[0].relative_to(root)
        raise FileExistsError(f"{existing} already uses the topic '{slug}'; choose a distinct topic")
    title = topic.strip()[:1].upper() + topic.strip()[1:]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render("work.md", date=date, title=title, summary="To be written with the plan."),
                      encoding="utf-8")
    return target
