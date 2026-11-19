"""`kanon verify`: mechanical checks on a Kanon instance (P1-04).

Each check returns Findings naming the file, line and rule. Nothing here calls a model.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from kanon.schema import DOC_TYPES, split_frontmatter, strip_fences, validate
from kanon.settings import validate_settings

SOURCES_PATH = "kanon/sources.md"
ARCHIVE_PREFIX = "kanon/archive/"
CONDUCT_PATH = "kanon/docs/conduct-and-writing.md"
ROOT_INSTRUCTIONS = ("AGENTS.md", "CLAUDE.md", "README.md", ".gitignore")
PHRASES = (
    "let's", "let me", "delve", "leverage", "seamless", "robust", "holistic", "synergy",
    "in summary", "to summarise", "it's worth noting", "interestingly", "notably", "arguably",
    "the key insight", "this matters because", "best practices",
)
LENGTH_LIMITS = {"decision": 60, "standard": 150}
SUMMARY_MAX_LINES = 3
PLACEHOLDER_REVIEW = "Not yet reviewed."
PLACEHOLDER_DECISION = "Pending."
PLAN_REQUIRED = ("Creator", "Reviewer")
PLAN_IF_PRESENT = ("Output", "Inputs", "Acceptance")
MIN_EXCEPTION_MATCH = 8


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


def _body(text: str) -> tuple[dict | None, list[str], int]:
    """Frontmatter, body lines with fenced blocks blanked, and the body's first line number."""
    meta, body = split_frontmatter(text)
    normal = text.lstrip("﻿").replace("\r\n", "\n")
    offset = normal.count("\n") - body.count("\n") + 1
    return meta, strip_fences(body.split("\n"))[0], offset


def _sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Map each '## ' heading name (number stripped) to its (start, end) line indexes."""
    starts = [(i, re.sub(r"^## (?:\d+\.\s+)?", "", l).strip()) for i, l in enumerate(lines) if l.startswith("## ")]
    return {name: (i, starts[n + 1][0] if n + 1 < len(starts) else len(lines)) for n, (i, name) in enumerate(starts)}


def _section_text(lines: list[str], span: tuple[int, int]) -> str:
    return "\n".join(lines[span[0] + 1:span[1]]).strip()


def _table(lines: list[str]) -> list[list[str]]:
    rows = [l for l in lines if l.startswith("|") and not re.fullmatch(r"\|[\s|:-]+\|", l.strip())]
    return [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]


def _cell(rows: list[list[str]], key: str) -> str | None:
    for row in rows:
        if len(row) >= 2 and row[0].lower() == key.lower():
            return row[1]
    return None


# ---------------------------------------------------------------- document checks

def check_document(rel: str, text: str) -> list[Finding]:
    findings = [Finding(rel, 1, p.rule, p.message) for p in validate(text)]
    meta, lines, offset = _body(text)
    if meta is None:
        return findings
    _, unclosed = strip_fences(text.split("\n"))
    if unclosed is not None:
        findings.append(Finding(rel, unclosed + 1, "layout", "code fence is never closed"))
    doc_type = meta.get("type") if isinstance(meta.get("type"), str) else None

    if doc_type in ("sources", "archive"):
        allowed = rel == SOURCES_PATH if doc_type == "sources" else rel.startswith(ARCHIVE_PREFIX)
        if not allowed:
            where = SOURCES_PATH if doc_type == "sources" else ARCHIVE_PREFIX
            findings.append(Finding(rel, 1, "layout", f"type '{doc_type}' is only allowed at {where}"))

    if doc_type != "archive":
        findings.extend(_check_title_and_summary(rel, lines, offset, doc_type))

    seen: set[str] = set()
    for i, line in enumerate(lines):
        if line.startswith("## "):
            name = re.sub(r"^## (?:\d+\.\s+)?", "", line).strip()
            if name in seen:
                findings.append(Finding(rel, offset + i, "sections", f"duplicate section '{name}'"))
            seen.add(name)

    limit = LENGTH_LIMITS.get(doc_type)
    total = len(text.splitlines())
    if limit and total > limit:
        findings.append(Finding(rel, 1, "length", f"{total} lines; the limit for a {doc_type} is {limit}"))

    exempt = rel == SOURCES_PATH or rel.startswith(ARCHIVE_PREFIX)
    if not exempt:
        findings.extend(check_writing(rel, text, phrases=rel != CONDUCT_PATH))
    return findings


def _check_title_and_summary(rel, lines, offset, doc_type) -> list[Finding]:
    content = [(i, l) for i, l in enumerate(lines) if l.strip()]
    if not content or not content[0][1].startswith("# "):
        return [Finding(rel, offset, "layout", "the first line after the frontmatter must be the '# ' title")]
    block = []
    for i, line in content[1:]:
        if not line.startswith(">"):
            break
        block.append((i, line))
    marker = DOC_TYPES[doc_type].summary_marker if doc_type in DOC_TYPES else "> **Summary:**"
    if not block or not block[0][1].startswith(marker):
        return [Finding(rel, offset + content[0][0] + 1, "layout",
                        f"the summary block, starting '{marker}', must come directly after the title")]
    if len(block) > SUMMARY_MAX_LINES:
        return [Finding(rel, offset + block[0][0], "layout",
                        f"summary block is {len(block)} lines; the limit is {SUMMARY_MAX_LINES}")]
    return []


def check_writing(rel: str, text: str, phrases: bool = True) -> list[Finding]:
    findings = []
    lines, _ = strip_fences(text.split("\n"))
    for n, line in enumerate(lines, 1):
        if "—" in line or "–" in line:
            findings.append(Finding(rel, n, "writing", "em or en dash; use a comma, colon, full stop or hyphen"))
        if phrases:
            lower = line.lower()
            for phrase in PHRASES:
                if re.search(r"(?<![\w'])" + re.escape(phrase) + r"(?![\w'])", lower):
                    findings.append(Finding(rel, n, "writing", f"listed phrase '{phrase}'"))
    return findings


# ---------------------------------------------------------------- work file checks

@dataclass(frozen=True)
class Version:
    commit: str
    text: str


def plan_is_filled(text: str) -> bool:
    _, lines, _ = _body(text)
    plan = _sections(lines).get("Plan")
    if not plan:
        return False
    rows = _table(lines[plan[0]:plan[1]])
    if not all(_cell(rows, key) for key in PLAN_REQUIRED):
        return False
    return all(_cell(rows, key) for key in PLAN_IF_PRESENT if _cell(rows, key) is not None)


def _review_is_placeholder(text: str) -> bool:
    _, lines, _ = _body(text)
    review = _sections(lines).get("Review")
    return review is None or _section_text(lines, review) == PLACEHOLDER_REVIEW


def check_work_file(rel: str, text: str, round_limit: int, history=None, changed=None) -> list[Finding]:
    """history: a callable returning committed Versions oldest first; changed: commit -> files changed."""
    findings: list[Finding] = []
    meta, lines, offset = _body(text)
    if meta is None or meta.get("type") != "work":
        return findings
    sections = _sections(lines)

    plan = sections.get("Plan")
    rows = _table(lines[plan[0]:plan[1]]) if plan else []
    if plan:
        creator, reviewer = _cell(rows, "Creator"), _cell(rows, "Reviewer")
        if not creator or not reviewer:
            findings.append(Finding(rel, offset + plan[0], "loop", "Plan must name a Creator and a Reviewer"))
        elif creator.split("(")[0].strip().lower() == reviewer.split("(")[0].strip().lower():
            findings.append(Finding(rel, offset + plan[0], "loop", "Creator and Reviewer must be different"))

    review = sections.get("Review")
    if review and _section_text(lines, review) != PLACEHOLDER_REVIEW:
        group_limit = _cell(rows, "Group round limit")
        group_limit = int(re.match(r"\d+", group_limit).group()) if group_limit and re.match(r"\d+", group_limit) else None
        findings.extend(_check_rounds(rel, offset, lines, review, round_limit, group_limit))
        if history is not None and not _plan_committed_alone(history(), changed):
            findings.append(Finding(rel, offset + review[0], "loop",
                                    "the filled Plan was not committed on its own before the build and review"))

    decision = sections.get("Decision")
    if meta.get("status") == "complete" and decision and _section_text(lines, decision) == PLACEHOLDER_DECISION:
        findings.append(Finding(rel, offset + decision[0], "approval", "status is complete but no decision is recorded"))
    return findings


def _check_rounds(rel, offset, lines, review, limit, group_limit) -> list[Finding]:
    rows = _table(lines[review[0]:review[1]])
    if not rows or rows[0][0].lower() != "round":
        return [Finding(rel, offset + review[0], "loop", "Review must hold a table whose first column is 'Round'")]
    findings, highest = [], {}
    for row in rows[1:]:
        match = re.fullmatch(r"([A-Z]?)(\d+)", row[0])
        if not match:
            findings.append(Finding(rel, offset + review[0], "loop",
                                    f"round '{row[0]}' is not a number or a capital letter and a number"))
            continue
        group, number = match.group(1), int(match.group(2))
        if number > highest.get(group, (0, []))[0]:
            highest[group] = (number, row)
    for group, (number, row) in highest.items():
        cap = group_limit if group and group_limit else limit
        verdict = row[3].strip("` ").lower() if len(row) > 3 else ""
        outcome = row[-1].strip().lower()
        escalated = verdict == "escalate" or outcome.startswith("owner decides") or " owner decides" in outcome
        if number > cap and not escalated:
            findings.append(Finding(rel, offset + review[0], "loop",
                                    f"review round {group}{number} exceeds the limit of {cap} without escalation"))
    return findings


def _plan_committed_alone(versions: list[Version], changed) -> bool:
    """The first version with a filled Plan had no review yet and its commit changed no build files."""
    for version in versions:
        if not plan_is_filled(version.text):
            continue
        if not _review_is_placeholder(version.text):
            return False
        files = changed(version.commit) if changed else []
        return all(f.startswith(("kanon/", ".claude/")) or f in ROOT_INSTRUCTIONS for f in files)
    return False


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True).stdout


def history_of(root: Path, rel: str) -> list[Version]:
    """Committed versions of a file, oldest first, following renames."""
    log = _git(root, "log", "--follow", "--name-only", "--format=%x00%H", "--", rel)
    entries = []
    for chunk in log.split("\x00")[1:]:
        parts = chunk.strip().split("\n")
        if len(parts) >= 2:
            entries.append((parts[0], parts[-1]))
    versions = []
    for commit, path in reversed(entries):
        text = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=root, capture_output=True, text=True)
        if text.returncode == 0:
            versions.append(Version(commit, text.stdout))
    return versions


def changed_files(root: Path, commit: str) -> list[str]:
    return [f for f in _git(root, "show", "--name-only", "--format=", commit).split("\n") if f]


# ---------------------------------------------------------------- review list

def check_decision_needed(rel: str, text: str) -> list[Finding]:
    """A pending decision states what to decide; open questions belong in the Questions section."""
    _, lines, offset = _body(text)
    findings, inside = [], False
    for i, line in enumerate(lines):
        if line.startswith("> **Decision needed:**"):
            inside = True
        elif not line.startswith(">") or line.startswith("> **"):
            inside = False
        if inside and "?" in line:
            findings.append(Finding(rel, offset + i, "questions", "question in the 'Decision needed' line; "
                                    "ask it during the work and record it in Questions"))
    return findings


ACTION_COLUMNS = ("id", "action", "assignee", "blocks", "done")


def check_actions(rel: str, text: str) -> list[Finding]:
    """Actions tables must be readable by the Desk, or actions vanish from it unnoticed."""
    from kanon.settings import GITHUB_USER
    _, lines, offset = _body(text)
    span = _sections(lines).get("Actions")
    if not span:
        return []
    where = offset + span[0]
    raw = [l for l in lines[span[0]:span[1]] if l.startswith("|")]
    rows = _table(lines[span[0]:span[1]])
    if not rows:
        return [Finding(rel, where, "actions", "Actions section has no table")]
    header = [h.lower() for h in rows[0]]
    missing = [c for c in ACTION_COLUMNS if c not in header]
    if missing:
        return [Finding(rel, where, "actions", f"Actions table lacks column(s): {', '.join(missing)}")]
    findings, ids = [], []
    width = raw[0].count("|")
    for i, line in enumerate(lines[span[0]:span[1]]):
        if line.startswith("|") and line != raw[0] and not re.fullmatch(r"\|[\s|:-]+\|", line.strip()) \
                and line.count("|") != width:
            findings.append(Finding(rel, offset + span[0] + i, "actions",
                                    f"row has the wrong number of cells: {line.strip()[:40]}"))
    for row in rows[1:]:
        if len(row) != len(header):
            continue
        cell = dict(zip(header, row))
        ids.append(cell["id"])
        if not re.fullmatch(r"[A-Za-z]+-\d+", cell["id"]):
            findings.append(Finding(rel, where, "actions", f"action ID '{cell['id']}' is not like A-1"))
        names = [a.strip(" `@") for a in re.split(r"[,;]", cell["assignee"]) if a.strip(" `@")]
        if not names or not all(GITHUB_USER.match(n) for n in names):
            findings.append(Finding(rel, where, "actions", f"{cell['id']}: assignee must be GitHub username(s)"))
        if cell["done"].lower() not in ("yes", "no"):
            findings.append(Finding(rel, where, "actions", f"{cell['id']}: Done must be yes or no"))
    for row in rows[1:]:
        if len(row) == len(header):
            cell = dict(zip(header, row))
            for target in [t.strip(" `") for t in re.split(r"[,;]", cell["blocks"]) if t.strip(" `-")]:
                if target not in ids:
                    findings.append(Finding(rel, where, "actions", f"{cell['id']} blocks unknown action '{target}'"))
    for i, line in enumerate(lines[span[0]:span[1]]):
        heading = re.match(r"^### ([A-Za-z]+-\d+)\b", line)
        if heading and heading.group(1) not in ids:
            findings.append(Finding(rel, offset + span[0] + i, "actions", f"steps for '{heading.group(1)}' match no row"))
    return findings


# ---------------------------------------------------------------- exceptions

@dataclass(frozen=True)
class AcceptedException:
    path: str
    rule: str
    contains: str
    reason: str

    def covers(self, finding: Finding) -> bool:
        return (finding.path == self.path and finding.rule == self.rule
                and self.contains.lower() in finding.message.lower())


def load_exceptions(settings: dict) -> tuple[list[AcceptedException], list[Finding]]:
    """Exceptions from [[verify.exceptions]]: path, rule, contains (at least 8 characters), reason."""
    entries = settings.get("verify", {}).get("exceptions", [])
    accepted, problems = [], []
    for n, entry in enumerate(entries if isinstance(entries, list) else [], 1):
        fields = {k: entry.get(k) for k in ("path", "rule", "contains", "reason")} if isinstance(entry, dict) else {}
        valid = len(fields) == 4 and all(isinstance(v, str) and v.strip() for v in fields.values())
        if valid and len(fields["contains"]) >= MIN_EXCEPTION_MATCH:
            accepted.append(AcceptedException(**fields))
        else:
            problems.append(Finding("kanon/kanon.toml", 1, "settings",
                                    f"verify exception {n} needs path, rule, reason and a 'contains' of at least "
                                    f"{MIN_EXCEPTION_MATCH} characters"))
    return accepted, problems


# ---------------------------------------------------------------- instance

def verify(root: Path) -> list[Finding]:
    findings, _ = verify_with_exceptions(root)
    return findings


def verify_with_exceptions(root: Path) -> tuple[list[Finding], list[tuple[Finding, AcceptedException]]]:
    """Return (open findings, findings covered by an accepted exception)."""
    findings, settings = _verify(root)
    accepted, problems = load_exceptions(settings)
    open_, covered, used = list(problems), [], set()
    for finding in findings:
        match = next((e for e in accepted if e.covers(finding)), None)
        if match:
            covered.append((finding, match))
            used.add(match)
        else:
            open_.append(finding)
    open_ += [Finding("kanon/kanon.toml", 1, "settings", f"exception for {e.path} ({e.rule}) matches nothing; remove it")
              for e in accepted if e not in used]
    return open_, covered


def check_approvals(rel: str, text: str, settings: dict) -> list[Finding]:
    """P1-05: the latest approval still matches its hash and names a listed approver."""
    from kanon.approve import check
    meta, _ = split_frontmatter(text)
    if not meta or meta.get("type") != "work":
        return []
    approvers = settings.get("kanon", {}).get("approvers", [])
    approvers = [a for a in approvers if isinstance(a, str)] if isinstance(approvers, list) else []
    return [Finding(rel, line, "approval", message) for line, message in check(text, approvers, meta.get("status"))]


def _verify(root: Path) -> tuple[list[Finding], dict]:
    kanon = root / "kanon"
    if not kanon.is_dir():
        return [Finding("kanon", 0, "layout", "no kanon/ folder; run kanon init")], {}
    findings: list[Finding] = []
    settings: dict = {}
    settings_path = kanon / "kanon.toml"
    if settings_path.exists():
        text = settings_path.read_text(encoding="utf-8")
        findings += [Finding("kanon/kanon.toml", 1, p.rule, p.message) for p in validate_settings(text)]
        try:
            settings = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            pass
    else:
        findings.append(Finding("kanon/kanon.toml", 0, "settings", "missing; run kanon init"))
    limit = settings.get("kanon", {}).get("review_round_limit", 3)
    limit = limit if isinstance(limit, int) and not isinstance(limit, bool) and limit > 0 else 3

    seen_topics: dict[str, str] = {}
    for path in sorted((kanon / "work").glob("*.md")):
        topic = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
        rel = path.relative_to(root).as_posix()
        if topic in seen_topics:
            findings.append(Finding(rel, 1, "layout", f"topic '{topic}' is also used by {seen_topics[topic]}; "
                                                      "replies on the Desk would be ambiguous"))
        seen_topics.setdefault(topic, rel)
    for path in sorted(kanon.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("kanon/local/"):
            continue  # generated views, never committed
        text = path.read_text(encoding="utf-8")
        findings += check_document(rel, text)
        if rel.startswith("kanon/work/"):
            findings += check_work_file(rel, text, limit, lambda rel=rel: history_of(root, rel),
                                        lambda commit: changed_files(root, commit))
            findings += check_decision_needed(rel, text)
            findings += check_actions(rel, text)
            findings += check_approvals(rel, text, settings)

    # Hand-written instruction files are checked; generated ones are checked through their sources.
    from kanon.sync import GENERATED, is_generated
    instruction_files = [root / name for name in ROOT_INSTRUCTIONS[:2]] + sorted((root / ".claude").rglob("*.md"))
    for path in instruction_files:
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            if not (rel in GENERATED and is_generated(text)):
                findings += check_writing(rel, text)
    tracked = set(_git(root, "ls-files", "--", *GENERATED, "kanon/local").split())
    findings += [Finding(rel, 1, "privacy", "generated agent file is committed; remove it with git rm --cached")
                 for rel in sorted(tracked)]
    return findings, settings


HOOK = """#!/bin/sh
# Installed by kanon init. Runs Kanon's checks on the working tree before each commit.
# Limits: it checks files on disk, not only the staged changes; 'git commit --no-verify' skips it.
# In Kanon's own repository, use the version being developed, never a stale global install.
if grep -q '^name = "kanon-engine"' pyproject.toml 2>/dev/null && command -v uv >/dev/null 2>&1; then
  exec uv run --quiet kanon verify
fi
if command -v kanon >/dev/null 2>&1; then exec kanon verify; fi
if command -v uv >/dev/null 2>&1 && uv run --quiet kanon --version >/dev/null 2>&1; then exec uv run --quiet kanon verify; fi
echo "kanon is not installed; kanon verify skipped"
exit 0
"""


def hook_location(root: Path, name: str = "pre-commit") -> str:
    """Path of one of the repository's hooks (it may not exist yet)."""
    result = subprocess.run(["git", "rev-parse", "--git-path", f"hooks/{name}"], cwd=root,
                            capture_output=True, text=True, check=True)
    return str((root / result.stdout.strip()).resolve())


def install_hook(root: Path, name: str = "pre-commit", content: str | None = None) -> tuple[str, bool]:
    """Install or update one of Kanon's hooks; never replace someone else's.

    Returns (hook path, whether it was written).
    """
    content = HOOK if content is None else content
    hook = Path(hook_location(root, name))
    if hook.exists():
        current = hook.read_text(encoding="utf-8", errors="replace")
        if "# Installed by kanon init." not in current or current == content:
            return str(hook), False  # someone else's hook, or already current
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(content, encoding="utf-8")
    hook.chmod(0o755)
    return str(hook), True
