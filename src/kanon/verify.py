"""`kanon verify`: mechanical checks on a Kanon instance (P1-04).

Each check returns Findings naming the file, line and rule. Nothing here calls a model.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from kanon.schema import split_frontmatter, validate
from kanon.settings import validate_settings

EXEMPT_FROM_WRITING = ("sources", "archive")
PHRASES = (
    "let's", "let me", "delve", "leverage", "seamless", "robust", "holistic", "synergy",
    "in summary", "to summarise", "it's worth noting", "interestingly", "notably", "arguably",
    "the key insight", "this matters because", "best practices",
)
LENGTH_LIMITS = {"decision": 60, "standard": 150}
SUMMARY_MAX_LINES = 3
PLACEHOLDER_REVIEW = "Not yet reviewed"
PLACEHOLDER_DECISION = "Pending."


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


def _strip_fences(lines: list[str]) -> list[str]:
    """Blank out fenced code blocks so their contents are not read as structure or prose."""
    out, fenced = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append("")
        else:
            out.append("" if fenced else line)
    return out


def _body_offset(text: str) -> int:
    """Line number (1-based) of the first body line after the frontmatter."""
    _, body = split_frontmatter(text)
    return text.replace("\r\n", "\n").count("\n") - body.count("\n") + 1


def _sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Map each '## ' heading name (number stripped) to its (start, end) line indexes."""
    starts = [(i, re.sub(r"^## (?:\d+\.\s+)?", "", l).strip()) for i, l in enumerate(lines) if l.startswith("## ")]
    return {name: (i, starts[n + 1][0] if n + 1 < len(starts) else len(lines)) for n, (i, name) in enumerate(starts)}


def _table(lines: list[str]) -> list[list[str]]:
    rows = [l for l in lines if l.startswith("|") and not re.fullmatch(r"\|[\s|:-]+\|", l.strip())]
    return [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]


# ---------------------------------------------------------------- document checks

def check_document(rel: str, text: str) -> list[Finding]:
    findings = [Finding(rel, 1, p.rule, p.message) for p in validate(text)]
    meta, body = split_frontmatter(text)
    if meta is None:
        return findings
    offset = _body_offset(text)
    lines = _strip_fences(body.replace("\r\n", "\n").split("\n"))
    doc_type = meta.get("type")

    content = [(i, l) for i, l in enumerate(lines) if l.strip()]
    if doc_type != "archive" and (not content or not content[0][1].startswith("# ")):
        findings.append(Finding(rel, offset, "layout", "the first line after the frontmatter must be the '# ' title"))
    if doc_type != "archive" and content and content[0][1].startswith("# "):
        after = content[1:]
        block = []
        for i, line in after:
            if not line.startswith(">"):
                break
            block.append(i)
        if not block:
            findings.append(Finding(rel, offset + content[0][0] + 1, "layout",
                                    "the summary block must come directly after the title"))
        elif len(block) > SUMMARY_MAX_LINES:
            findings.append(Finding(rel, offset + block[0], "layout",
                                    f"summary block is {len(block)} lines; the limit is {SUMMARY_MAX_LINES}"))

    seen: dict[str, int] = {}
    for i, line in enumerate(lines):
        if line.startswith("## "):
            name = re.sub(r"^## (?:\d+\.\s+)?", "", line).strip()
            if name in seen:
                findings.append(Finding(rel, offset + i, "sections", f"duplicate section '{name}'"))
            seen.setdefault(name, i)

    limit = LENGTH_LIMITS.get(doc_type)
    total = text.count("\n") + 1
    if limit and total > limit:
        findings.append(Finding(rel, 1, "length", f"{total} lines; the limit for a {doc_type} is {limit}"))

    if doc_type not in EXEMPT_FROM_WRITING:
        findings.extend(check_writing(rel, text, phrases=not rel.endswith("conduct-and-writing.md")))
    return findings


def check_writing(rel: str, text: str, phrases: bool = True) -> list[Finding]:
    findings = []
    lines = _strip_fences(text.split("\n"))
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

def _cell(rows: list[list[str]], key: str) -> str | None:
    for row in rows:
        if len(row) >= 2 and row[0].lower() == key.lower():
            return row[1]
    return None


def check_work_file(rel: str, text: str, round_limit: int, history: list[str]) -> list[Finding]:
    """history: the file's committed versions, oldest first."""
    findings: list[Finding] = []
    meta, body = split_frontmatter(text)
    if meta is None or meta.get("type") != "work":
        return findings
    offset = _body_offset(text)
    lines = _strip_fences(body.replace("\r\n", "\n").split("\n"))
    sections = _sections(lines)

    plan = sections.get("Plan")
    if plan:
        rows = _table(lines[plan[0]:plan[1]])
        creator, reviewer = _cell(rows, "Creator"), _cell(rows, "Reviewer")
        if not creator or not reviewer:
            findings.append(Finding(rel, offset + plan[0], "loop", "Plan must name a Creator and a Reviewer"))
        elif creator.split("(")[0].strip().lower() == reviewer.split("(")[0].strip().lower():
            findings.append(Finding(rel, offset + plan[0], "loop", "Creator and Reviewer must be different"))

    review = sections.get("Review")
    reviewed = bool(review) and PLACEHOLDER_REVIEW not in "\n".join(lines[review[0]:review[1]])
    if reviewed:
        findings.extend(_check_rounds(rel, offset, lines, review, round_limit))
        if not _plan_committed_before_review(history):
            findings.append(Finding(rel, offset + review[0], "loop",
                                    "no commit shows the Plan before the Review: plan first, then review"))

    decision = sections.get("Decision")
    if meta.get("status") == "complete" and decision:
        if PLACEHOLDER_DECISION in "\n".join(lines[decision[0]:decision[1]]):
            findings.append(Finding(rel, offset + decision[0], "approval", "status is complete but no decision is recorded"))
    return findings


def _check_rounds(rel, offset, lines, review, limit) -> list[Finding]:
    rows = _table(lines[review[0]:review[1]])
    if not rows or rows[0][0].lower() != "round":
        return []
    highest: dict[str, tuple[int, list[str]]] = {}
    for row in rows[1:]:
        match = re.fullmatch(r"([A-Za-z]*)(\d+)", row[0])
        if match:
            group, number = match.group(1), int(match.group(2))
            if number > highest.get(group, (0, []))[0]:
                highest[group] = (number, row)
    findings = []
    for group, (number, row) in highest.items():
        escalated = re.search(r"escalat|owner decides", " ".join(row), re.IGNORECASE)
        if number > limit and not escalated:
            findings.append(Finding(rel, offset + review[0], "loop",
                                    f"review round {group}{number} exceeds the limit of {limit} without escalation"))
    return findings


def _plan_committed_before_review(history: list[str]) -> bool:
    for version in history:
        _, body = split_frontmatter(version)
        lines = body.split("\n")
        sections = _sections(lines)
        plan, review = sections.get("Plan"), sections.get("Review")
        if not plan:
            continue
        plan_text = "\n".join(lines[plan[0] + 1:plan[1]]).strip()
        review_text = "\n".join(lines[review[0] + 1:review[1]]) if review else ""
        if plan_text and (not review or PLACEHOLDER_REVIEW in review_text):
            return True
        if review and PLACEHOLDER_REVIEW not in review_text:
            return False  # the earliest version with a Plan already had a review
    return False


# ---------------------------------------------------------------- instance

def _history(root: Path, rel: str) -> list[str]:
    log = subprocess.run(["git", "log", "--follow", "--format=%H", "--", rel], cwd=root,
                         capture_output=True, text=True)
    versions = []
    for commit in reversed(log.stdout.split()):
        shown = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=root, capture_output=True, text=True)
        if shown.returncode == 0:
            versions.append(shown.stdout)
    return versions


def check_review_list(rel: str, text: str) -> list[Finding]:
    _, body = split_frontmatter(text)
    lines = _strip_fences(body.split("\n"))
    offset = _body_offset(text)
    return [Finding(rel, offset + i, "questions",
                    "open question in the review list; ask it in the work, record it in the work file")
            for i, line in enumerate(lines) if line.rstrip().endswith("?")]


@dataclass(frozen=True)
class Exception_:
    path: str
    rule: str
    contains: str
    reason: str

    def covers(self, finding: Finding) -> bool:
        return (finding.path == self.path and finding.rule == self.rule
                and self.contains.lower() in finding.message.lower())


def load_exceptions(settings: dict) -> tuple[list[Exception_], list[Finding]]:
    """Accepted exceptions from [[verify.exceptions]]; each needs path, rule, contains and reason."""
    entries = settings.get("verify", {}).get("exceptions", [])
    accepted, problems = [], []
    for n, entry in enumerate(entries if isinstance(entries, list) else [], 1):
        fields = {k: entry.get(k) for k in ("path", "rule", "contains", "reason")} if isinstance(entry, dict) else {}
        if all(isinstance(v, str) and v.strip() for v in fields.values()) and len(fields) == 4:
            accepted.append(Exception_(**fields))
        else:
            problems.append(Finding("kanon/kanon.toml", 1, "settings",
                                    f"verify exception {n} needs path, rule, contains and reason"))
    return accepted, problems


def verify(root: Path) -> list[Finding]:
    findings, _ = verify_with_exceptions(root)
    return findings


def verify_with_exceptions(root: Path) -> tuple[list[Finding], list[tuple[Finding, Exception_]]]:
    """Return (open findings, findings covered by an accepted exception)."""
    findings = _verify(root)
    settings_path = root / "kanon" / "kanon.toml"
    try:
        settings = tomllib.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    except tomllib.TOMLDecodeError:
        settings = {}
    accepted, problems = load_exceptions(settings)
    open_, covered = list(problems), []
    for finding in findings:
        match = next((e for e in accepted if e.covers(finding)), None)
        if match:
            covered.append((finding, match))
        else:
            open_.append(finding)
    return open_, covered


def _verify(root: Path) -> list[Finding]:
    kanon = root / "kanon"
    if not kanon.is_dir():
        return [Finding("kanon", 0, "layout", "no kanon/ folder; run kanon init")]
    findings: list[Finding] = []
    settings_path = kanon / "kanon.toml"
    round_limit = 3
    if settings_path.exists():
        text = settings_path.read_text(encoding="utf-8")
        findings += [Finding("kanon/kanon.toml", 1, p.rule, p.message) for p in validate_settings(text)]
        try:
            round_limit = tomllib.loads(text).get("kanon", {}).get("review_round_limit", 3)
        except tomllib.TOMLDecodeError:
            pass
    else:
        findings.append(Finding("kanon/kanon.toml", 0, "settings", "missing; run kanon init"))

    for path in sorted(kanon.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        findings += check_document(rel, text)
        if rel.startswith("kanon/work/"):
            findings += check_work_file(rel, text, round_limit if isinstance(round_limit, int) else 3,
                                        _history(root, rel))
        if rel == "kanon/REVIEW.md":
            findings += check_review_list(rel, text)
    return findings


HOOK = """#!/bin/sh
# Installed by kanon init. Runs Kanon's mechanical checks before each commit.
command -v kanon >/dev/null 2>&1 || { echo "kanon not installed; skipping kanon verify"; exit 0; }
exec kanon verify
"""


def install_hook(root: Path) -> str | None:
    """Install the pre-commit hook unless one exists. Returns the hook path if written."""
    result = subprocess.run(["git", "rev-parse", "--git-path", "hooks/pre-commit"], cwd=root,
                            capture_output=True, text=True)
    if result.returncode != 0:
        return None
    hook = (root / result.stdout.strip()).resolve()
    if hook.exists():
        return None
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(HOOK, encoding="utf-8")
    hook.chmod(0o755)
    return str(hook)
