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
HASH = re.compile(r"sha256:(\S+)")
VALID_HASH = re.compile(r"[0-9a-f]{64}")
MATERIAL = re.compile(r"material: (plan|result|item [A-Za-z0-9._-]+)")
FORMS = ("with kanon approve", "Transcribed by the assistant for", "on GitHub by", "material:")
LATE = "owner decides"
CELL_SPLIT = re.compile(r"(?<!\\)\|")


def _split(text: str) -> tuple[str, list[str]]:
    """(frontmatter including its fences, body lines), with line endings normalised."""
    text = normalise(text)
    match = re.match(r"---\n.*?\n---\n", text, re.S)
    head = match.group(0) if match else ""
    return head, text[len(head):].split("\n")


def _heading_name(line: str) -> str:
    return re.sub(r"^## (?:\d+\.\s+)?", "", line).strip()


def _fence_left_open(lines: list[str]) -> bool:
    fence = None
    for line in lines:
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if fence is None and marker:
            fence = marker.group(1)[0] * len(marker.group(1))
        elif fence is not None and line.strip().startswith(fence) and not line.strip().strip(fence[0]):
            fence = None
    return fence is not None


def _unfenced(lines: list[str]) -> list[bool]:
    """For each line, True when it is outside a fenced code block (K-349)."""
    out, fence = [], None
    for line in lines:
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if fence is None and marker:
            fence = marker.group(1)[0] * len(marker.group(1))
            out.append(False)
        elif fence is not None:
            if line.strip().startswith(fence) and not line.strip().strip(fence[0]):
                fence = None
            out.append(False)
        else:
            out.append(True)
    return out


def _cells(line: str) -> list[str]:
    return [c.strip() for c in CELL_SPLIT.split(line.strip().strip("|"))]


def _names_item(text: str, item: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(item)}(?![\w-])", text) is not None


def _item_material(lines: list[str], item: str) -> str:
    """An item's own record: its Work Items row, Plan subsections naming it, and Review rows naming it."""
    out, section, subsection = [], None, ""
    for line, open_ in zip(lines, _unfenced(lines)):
        if open_ and line.startswith("## "):
            section, subsection = _heading_name(line), ""
            continue
        if open_ and line.startswith("### "):
            subsection = line
            if section == "Plan" and _names_item(line, item):
                out.append(line.rstrip())
            continue
        if section == "Plan":
            if subsection and _names_item(subsection, item):
                out.append(line.rstrip())
            elif line.startswith("|") and _cells(line)[0] == item:
                out.append(line.rstrip())
        elif section == "Review" and line.startswith("|"):
            cells = _cells(line)
            if len(cells) > 1 and _names_item(cells[1], item):
                out.append(line.rstrip())
    if not out:
        raise ValueError(f"no record of item {item} in the work file (Work Items row, Plan subsection or Review row)")
    return "\n".join(out).strip() + "\n"


def material(text: str, kind: str) -> str:
    """The approved text: title and sections up to the Plan's end (plan) or the Review's end (result).

    The summary block and the Actions section are left out: they change when the decision is
    recorded or when the person confirms an action, not when the approved work changes.
    """
    _, lines = _split(text)
    if kind.startswith("item "):
        return _item_material(lines, kind[5:])
    out, section, in_summary = [], None, False
    stop = "Questions" if kind == PLAN else "Decision"
    for line, open_ in zip(lines, _unfenced(lines)):
        if open_ and line.startswith("## "):
            section = _heading_name(line)
            if section == stop or (kind == PLAN and section != "Plan"):
                break
            in_summary = False
        elif open_ and line.startswith("# ") and section is None:
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
    def label(self) -> str:
        """The basis after any quoted words: only Kanon writes here (K-365)."""
        marker = "Transcribed by the assistant for "
        return self.basis[self.basis.rindex(marker):] if marker in self.basis else self.basis

    @property
    def hash(self) -> str | None:
        match = HASH.search(self.label)
        return match.group(1) if match else None

    @property
    def kind(self) -> str:
        match = MATERIAL.search(self.label)
        return match.group(1) if match else (PLAN if self.item.lower().startswith("plan") else RESULT)

    @property
    def approver(self) -> str | None:
        """The approver named by Kanon's own label, never a name inside the quoted words (K-342)."""
        marker = "Transcribed by the assistant for "
        if marker in self.basis:
            match = re.match(r"@?([A-Za-z0-9-]+)", self.basis[self.basis.rindex(marker) + len(marker):])
        else:
            match = re.match(r"(?:Approved by|Changes requested by) @?([A-Za-z0-9-]+) with kanon", self.basis) or \
                re.match(r"(?:Approved|Changes requested) on GitHub by @?([A-Za-z0-9-]+) \(", self.basis)
        return match.group(1) if match else None

    @property
    def labelled(self) -> bool:
        return any(form in self.label for form in FORMS)


def decision_rows(text: str) -> list[Row]:
    head, lines = _split(text)
    offset = head.count("\n") + 1
    rows, inside = [], False
    for index, (line, open_) in enumerate(zip(lines, _unfenced(lines))):
        if open_ and line.startswith("## "):
            inside = _heading_name(line) == "Decision"
            continue
        if inside and open_ and line.startswith("|") and not re.fullmatch(r"\|[\s|:-]+\|", line.strip()):
            cells = _cells(line)
            if len(cells) >= 4 and cells[0].lower() != "item":
                rows.append(Row(cells[0], cells[1], cells[2], " | ".join(cells[3:]), index + offset))
    return rows


def _git_head(root: Path, rel: str) -> str:
    """The commit at approval, marked when the work file has changes not yet committed (K-350)."""
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=root, capture_output=True, text=True)
    commit = f"`{head.stdout.strip() or 'none'}`"
    return commit + (" plus uncommitted changes" if dirty.stdout.strip() else "")


def _mark_late_reviews(lines: list[str], today: str, item: str | None = None) -> None:
    section = None
    for index, (line, open_) in enumerate(zip(lines, _unfenced(lines))):
        if open_ and line.startswith("## "):
            section = _heading_name(line)
        elif section == "Review" and line.startswith("|") and LATE in line.lower() and "owner reviewed" not in line.lower():
            if item and not (len(_cells(line)) > 1 and _names_item(_cells(line)[1], item)):
                continue
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
    open_ = _unfenced(lines)
    heads = [i for i, l in enumerate(lines) if open_[i] and l.startswith("## ")]
    start = next((i for i in heads if _heading_name(lines[i]) == "Decision"), None)
    if start is None:
        raise ValueError("the work file has no Decision section")
    end = next((i for i in heads if i > start), len(lines))
    body = [l for l in lines[start + 1:end] if l.strip()]
    table = [i for i in range(start + 1, end) if open_[i] and lines[i].startswith("|")]
    if not body or body == ["Pending."]:
        lines[start + 1:end] = ["", *DECISION_HEADER.split("\n"), row, ""]
    elif not table:  # a Decision section written as prose keeps its text, with the table after it (K-348)
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        lines[end:end] = ["", *DECISION_HEADER.split("\n"), row]
    else:
        lines.insert(table[-1] + 1, row)


def record(root: Path, rel: str, approver: str, approvers: list[str], *, changes: str | None = None,
           plan: bool = False, quote: str | None = None, today: str | None = None, item: str | None = None,
           github_review: str | None = None) -> str:
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
    if item is not None and (plan or not re.fullmatch(r"[A-Za-z0-9._-]+", item)):
        raise ValueError("--item takes an item ID such as P1-05 and cannot be combined with --plan")
    today = today or dt.date.today().isoformat()
    kind = f"item {item}" if item else (PLAN if plan else RESULT)
    label = item or ("Plan" if plan else "Result")
    if changes is None:
        _mark_late_reviews(lines, today, item)
    text = head + "\n".join(lines)
    commit = _git_head(root, rel)
    clean = lambda words: " ".join(words.split()).replace("|", "\\|")  # noqa: E731
    if github_review is not None:  # read back through the App by kanon github sync (P1-10)
        who = f"{'Changes requested' if changes is not None else 'Approved'} on GitHub by {approver} ({github_review})"
    elif quote is not None:
        who = f'Owner in chat: "{clean(quote)}". Transcribed by the assistant for {approver}'
    else:
        who = (f"Changes requested by {approver} with kanon request-changes" if changes is not None
               else f"Approved by {approver} with kanon approve")
    if changes is not None:
        row = f"| {label} | Changes requested | {today} | {who}; changes: {clean(changes)}; commit {commit} |"
        status, decided = "in-progress", f"Changes requested by {approver} on {today}."
    else:
        row = (f"| {label} | Approved | {today} | {who}; commit {commit}; "
               f"material: {kind}; sha256:{digest(text, kind)} |")
        status = "in-progress" if plan else "complete"
        decided = f"{'Plan approved' if plan else 'Approved'} by {approver} on {today}."
    _append_row(lines, row)
    if item is None:  # an item approval leaves the work file's status and summary as they are (K-340)
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
    head, lines = _split(text)
    if _fence_left_open(lines):  # K-364: an open fence would hide the Decision rows
        problems.append((head.count("\n") + 1, "a code fence is never closed; Decision rows after it cannot be checked"))
    allowed = [a.lower() for a in approvers]
    for row in rows:
        who = row.approver
        if row.hash and who and who.lower() not in allowed:
            problems.append((row.line, f"decision recorded for {who}, who is not listed in approvers"))
    approvals = [r for r in rows if r.decision.lower().startswith("approved")]
    latest: dict[str, Row] = {}
    for row in approvals:
        latest[row.kind] = row
    for kind, row in latest.items():
        if row.labelled and not (row.hash and VALID_HASH.fullmatch(row.hash)):
            problems.append((row.line, "a recorded approval has a missing or malformed hash"))
        elif row.hash:
            try:
                current = digest(text, kind)
            except ValueError as error:
                problems.append((row.line, str(error)))
                continue
            if row.hash != current:
                problems.append((row.line, f"the approved {kind} has changed since it was approved; "
                                           "a new decision is needed"))
    final = [r for r in approvals if not r.kind.startswith("item ")]
    on_merge = final and "on merge of pull request" in final[-1].decision.lower()  # P1-10: the merge approves
    if status == "complete" and final and not final[-1].hash and not on_merge:
        try:
            day = dt.date.fromisoformat(final[-1].date)
        except ValueError:
            day = None
        if day is None or day > LEGACY_UNTIL:
            problems.append((final[-1].line, "the latest approval has no hash; "
                                             "record it with kanon approve or kanon transcribe"))
    return problems
