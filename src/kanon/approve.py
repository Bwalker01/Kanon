"""Approvals (P1-05): hashed, labelled decisions recorded in a work file's Decision table.

Two forms count (owner, 2026-11-19): `kanon approve`, run by the person, and `kanon transcribe`,
run by the assistant with the person's exact words. Both hash the approved material and record the
commit. Local records are tamper-evident only (L-001); a separate identity (P1-10) makes them
tamper-proof.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from kanon.schema import normalise

PLAN, RESULT = "plan", "result"
# Rows dated on or before this day were recorded before P1-05 and carry no hash (legacy).
LEGACY_UNTIL = dt.date(2026, 11, 19)
DECISION_HEADER = "| Item | Decision | Date | Basis |\n|---|---|---|---|"
HASH = re.compile(r"sha256:([0-9a-f]{64})")
MATERIAL = re.compile(r"material: (plan|result)")
LATE = "owner decides"


def _split(text: str) -> tuple[str, list[str]]:
    """(frontmatter including its fences, body lines), with line endings normalised."""
    text = normalise(text)
    match = re.match(r"---\n.*?\n---\n", text, re.S)
    head = match.group(0) if match else ""
    return head, text[len(head):].split("\n")


def _heading_name(line: str) -> str:
    return re.sub(r"^## (?:\d+\.\s+)?", "", line).strip()


def material(text: str, kind: str) -> str:
    """The approved text: title and sections up to the Plan's end (plan) or the Review's end (result).

    The summary block and the Actions section are left out: they change when the decision is
    recorded or when the person confirms an action, not when the approved work changes.
    """
    _, lines = _split(text)
    out, section, in_summary = [], None, False
    stop = "Questions" if kind == PLAN else "Decision"
    for line in lines:
        if line.startswith("## "):
            section = _heading_name(line)
            if section == stop or (kind == PLAN and section != "Plan"):
                break
            in_summary = False
        elif line.startswith("# ") and section is None:
            in_summary = True
        elif in_summary and line.startswith(">"):
            continue
        if section == "Actions":
            continue
        out.append(line.rstrip())
    return "\n".join(out).strip() + "\n"


def digest(text: str, kind: str) -> str:
    return hashlib.sha256(material(text, kind).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Row:
    item: str
    decision: str
    date: str
    basis: str
    line: int  # 1-based line in the file

    @property
    def hash(self) -> str | None:
        match = HASH.search(self.basis)
        return match.group(1) if match else None

    @property
    def kind(self) -> str:
        match = MATERIAL.search(self.basis)
        return match.group(1) if match else (PLAN if self.item.lower().startswith("plan") else RESULT)

    @property
    def approver(self) -> str | None:
        match = re.search(r"(?:Approved by|Changes requested by|for) @?([A-Za-z0-9-]+)", self.basis)
        return match.group(1) if match else None


def decision_rows(text: str) -> list[Row]:
    head, lines = _split(text)
    offset = head.count("\n") + 1
    rows, inside = [], False
    for index, line in enumerate(lines):
        if line.startswith("## "):
            inside = _heading_name(line) == "Decision"
            continue
        if inside and line.startswith("|") and not re.fullmatch(r"\|[\s|:-]+\|", line.strip()):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[0].lower() != "item":
                rows.append(Row(cells[0], cells[1], cells[2], " | ".join(cells[3:]), index + offset))
    return rows


def _git_head(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True)
    return result.stdout.strip() or "none"


def _mark_late_reviews(lines: list[str], today: str) -> None:
    section = None
    for index, line in enumerate(lines):
        if line.startswith("## "):
            section = _heading_name(line)
        elif section == "Review" and line.startswith("|") and LATE in line.lower() and "owner reviewed" not in line.lower():
            lines[index] = line.rstrip().rstrip("|").rstrip() + f". Owner reviewed {today} |"


def _set_summary(lines: list[str], decided: str) -> None:
    for index, line in enumerate(lines):
        if line.startswith("> **Decision needed:**") or line.startswith("> **Decision:**"):
            end = index + 1
            while end < len(lines) and lines[end].startswith(">") and not lines[end].startswith("> **"):
                end += 1
            lines[index:end] = [f"> **Decision needed:** None. {decided}"]
            return


def _append_row(lines: list[str], row: str) -> None:
    start = next((i for i, l in enumerate(lines) if l.startswith("## ") and _heading_name(l) == "Decision"), None)
    if start is None:
        raise ValueError("the work file has no Decision section")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    body = [l for l in lines[start + 1:end] if l.strip()]
    if not body or body == ["Pending."]:
        lines[start + 1:end] = ["", *DECISION_HEADER.split("\n"), row, ""]
        return
    last = max(i for i in range(start + 1, end) if lines[i].startswith("|"))
    lines.insert(last + 1, row)


def record(root: Path, rel: str, approver: str, approvers: list[str], *, changes: str | None = None,
           plan: bool = False, quote: str | None = None, today: str | None = None) -> str:
    """Record a decision in the work file at rel. Returns the new Decision row.

    quote: the person's words, when the assistant transcribes them; None when the person runs it.
    changes: the requested changes; None for an approval.
    """
    if approver.lower() not in [a.lower() for a in approvers]:
        raise PermissionError(f"{approver} is not listed in approvers in kanon/kanon.toml")
    if quote is not None and not quote.strip():
        raise ValueError("a transcription needs the person's exact words (--quote)")
    path = root / rel
    head, lines = _split(path.read_text(encoding="utf-8"))
    if not re.search(r"^type: work$", head, re.M):
        raise ValueError(f"{rel} is not a work file")
    today = today or dt.date.today().isoformat()
    kind = PLAN if plan else RESULT
    if changes is None:
        _mark_late_reviews(lines, today)
    text = head + "\n".join(lines)
    commit = _git_head(root)
    who = f'Owner in chat: "{quote.strip()}". Transcribed by the assistant for {approver}' if quote is not None \
        else (f"Changes requested by {approver} with kanon request-changes" if changes is not None
              else f"Approved by {approver} with kanon approve")
    if changes is not None:
        row = f"| {'Plan' if plan else 'Result'} | Changes requested | {today} | {who}: {changes.strip()}; commit `{commit}` |"
        status, decided = "in-progress", f"Changes requested by {approver} on {today}."
    else:
        row = (f"| {'Plan' if plan else 'Result'} | Approved | {today} | {who}; commit `{commit}`; "
               f"material: {kind}; sha256:{digest(text, kind)} |")
        status = "in-progress" if plan else "complete"
        decided = f"{'Plan approved' if plan else 'Approved'} by {approver} on {today}."
    _append_row(lines, row.replace("\n", " "))
    _set_summary(lines, decided)
    head = re.sub(r"^status: .*$", f"status: {status}", head, count=1, flags=re.M)
    head = re.sub(r"^updated: .*$", f"updated: {today}", head, count=1, flags=re.M)
    path.write_text(head + "\n".join(lines), encoding="utf-8")
    return row


def in_assistant() -> bool:
    """True inside a Claude Code session, where `kanon approve` must not run (self-approval)."""
    return bool(os.environ.get("CLAUDECODE"))


def check(text: str, approvers: list[str], status: str | None) -> list[tuple[int, str]]:
    """(line, message) for each approval problem in a work file."""
    rows = decision_rows(text)
    problems: list[tuple[int, str]] = []
    allowed = [a.lower() for a in approvers]
    for row in rows:
        who = row.approver
        if row.hash and who and who.lower() not in allowed:
            problems.append((row.line, f"decision recorded for {who}, who is not listed in approvers"))
    approvals = [r for r in rows if r.decision.lower().startswith("approved")]
    if not approvals:
        return problems
    latest = approvals[-1]
    if latest.hash:
        if latest.hash != digest(text, latest.kind):
            problems.append((latest.line, f"the approved {latest.kind} has changed since it was approved; "
                                          "a new decision is needed"))
    elif status == "complete":
        try:
            day = dt.date.fromisoformat(latest.date)
        except ValueError:
            day = None
        if day is None or day > LEGACY_UNTIL:
            problems.append((latest.line, "the latest approval has no hash; record it with kanon approve or kanon transcribe"))
    return problems
