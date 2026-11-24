"""Branches (P1-09): one branch per work item, merged into the plan branch only after review.

Names: `kanon/<work>/plan` and `kanon/<work>/<item>` (owner, 2026-11-19). Merges use
`git merge --no-ff` only, so history is never rewritten. Work files are edited on the plan branch,
so parallel items never conflict on the Review table.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from kanon import approve

PREFIX = "kanon"
ITEM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class BranchError(RuntimeError):
    pass


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise BranchError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result


def plan_branch(work: str) -> str:
    return f"{PREFIX}/{work}/plan"


def item_branch(work: str, item: str) -> str:
    if not ITEM.fullmatch(item) or item == "plan":
        raise BranchError(f"'{item}' is not a usable item ID")
    return f"{PREFIX}/{work}/{item}"


def work_file(root: Path, work: str, ref: str | None = None) -> tuple[str, str]:
    """(path, text) of the work file named work, read from ref (default: the working tree)."""
    if ref is None:
        matches = sorted((root / "kanon" / "work").glob(f"????-??-??-{work}.md"))
        if len(matches) != 1:
            raise BranchError(f"no single work file named '{work}' in kanon/work")
        rel = matches[0].relative_to(root).as_posix()
        return rel, matches[0].read_text(encoding="utf-8")
    listing = _git(root, "ls-tree", "--name-only", ref, "kanon/work/").stdout.split()
    found = [p for p in listing if re.fullmatch(rf"kanon/work/\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(work)}\.md", p)]
    if len(found) != 1:
        raise BranchError(f"no single work file named '{work}' on {ref}")
    return found[0], _git(root, "show", f"{ref}:{found[0]}").stdout


def items(text: str) -> list[str]:
    """Item IDs from the Work Items table: first cells that look like IDs, such as P1-09."""
    found, section, subsection = [], None, ""
    for line in text.split("\n"):
        if line.startswith("## "):
            section = re.sub(r"^## (?:\d+\.\s+)?", "", line).strip()
        elif line.startswith("### "):
            subsection = line
        elif section == "Plan" and "Work Items" in subsection and line.startswith("|"):
            cell = line.strip().strip("|").split("|")[0].strip()
            if re.fullmatch(r"[A-Z][A-Za-z0-9]*-\d+[A-Za-z]?", cell):
                found.append(cell)
    return found


PENDING = ("owner decides", "owner to decide", "not independently reviewed")
SHORT_HASH = re.compile(r"\b[0-9a-f]{7,40}\b")


def _review_rows(text: str, item: str) -> list[list[str]]:
    """Review rows naming the item, outside code fences (K-388)."""
    lines = text.split("\n")
    rows, section = [], None
    for line, open_ in zip(lines, approve._unfenced(lines)):
        if open_ and line.startswith("## "):
            section = re.sub(r"^## (?:\d+\.\s+)?", "", line).strip()
        elif open_ and section == "Review" and line.startswith("|"):
            cells = [c.strip() for c in approve.CELL_SPLIT.split(line.strip().strip("|"))]
            if len(cells) >= 6 and approve._names_item(cells[1], item):
                rows.append(cells)
    return rows


def _cites(cells: list[str], tip: str | None) -> bool:
    """True when the row's Items cell cites the reviewed commit and it is the item's tip (K-383)."""
    if tip is None:
        return True
    return any(tip.startswith(h) for h in SHORT_HASH.findall(cells[1]))


def review_state(text: str, item: str, tip: str | None = None, approvers: list[str] | None = None) -> tuple[bool, str]:
    """(may merge, reason) for an item, from the plan branch's work file.

    The latest Decision row for the item decides first: a change request refuses; a recorded,
    labelled approval by a listed approver whose hash still matches allows (K-382, K-386). Otherwise
    the latest Review row naming the item must be a `pass` with no blocking findings, not awaiting
    the owner, citing the item branch's tip commit.
    """
    allowed = [a.lower() for a in approvers] if approvers is not None else None
    decisions = [r for r in approve.decision_rows(text) if r.item == item or r.kind == f"item {item}"]
    if decisions:
        row = decisions[-1]
        if not row.decision.lower().startswith("approved"):
            return False, f"changes were requested on {row.date}"
        valid = row.labelled and row.approver and (allowed is None or row.approver.lower() in allowed) \
            and row.hash and row.hash == approve.digest(text, f"item {item}")
        if valid:
            reviewed = _review_rows(text, item)
            if reviewed and not _cites(reviewed[-1], tip):
                return False, "approved, but the item branch has commits newer than the reviewed one"
            return True, f"approved ({row.date})"
    reviewed = _review_rows(text, item)
    if not reviewed:
        return False, "not reviewed"
    latest = reviewed[-1]
    verdict, blocking, outcome = latest[3].strip("` ").lower(), latest[4].strip().lower(), latest[-1].lower()
    if any(p in outcome for p in PENDING) and "owner reviewed" not in outcome:
        return False, f"round {latest[0]} awaits the owner's decision"
    if verdict != "pass":
        return False, f"latest review round {latest[0]} is '{verdict}', not pass"
    if blocking not in ("", "none", "-"):
        return False, f"review round {latest[0]} lists blocking findings ({latest[4]})"
    if not _cites(latest, tip):
        return False, f"review round {latest[0]} does not cite the item branch's tip commit {tip[:7]}"
    return True, f"review round {latest[0]} passed"


def _approvers(root: Path) -> list[str]:
    import tomllib
    try:
        data = tomllib.loads((root / "kanon" / "kanon.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    found = data.get("kanon", {}).get("approvers", [])
    return [a for a in found if isinstance(a, str)] if isinstance(found, list) else []


def _clean(root: Path) -> None:
    if _git(root, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise BranchError("the working tree has uncommitted changes; commit or stash them first")


def _exists(root: Path, branch: str) -> bool:
    return _git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0


def start(root: Path, work: str, item: str | None = None) -> str:
    """Create the plan branch (from the current commit) if missing, then the item branch; switch to it."""
    _clean(root)
    _, text = work_file(root, work)
    plan = plan_branch(work)
    if not _exists(root, plan):
        _git(root, "branch", plan)
    # A plain `git merge` into the plan branch then always makes a merge commit, so the hook runs (K-380).
    _git(root, "config", f"branch.{plan}.mergeoptions", "--no-ff")
    if item is None:
        _git(root, "switch", plan)
        return plan
    if item not in items(text):
        raise BranchError(f"{item} is not in the Work Items table of '{work}'")
    branch = item_branch(work, item)
    if _exists(root, branch):
        _git(root, "switch", branch)
    else:
        _git(root, "switch", "-c", branch, plan)
    return branch


def merge(root: Path, work: str, item: str) -> str:
    """Merge a reviewed item into the plan branch with a merge commit. Returns the merge commit."""
    _clean(root)
    plan, branch = plan_branch(work), item_branch(work, item)
    for name in (plan, branch):
        if not _exists(root, name):
            raise BranchError(f"branch {name} does not exist")
    _, text = work_file(root, work, plan)
    tip = _git(root, "rev-parse", branch).stdout.strip()
    ok, reason = review_state(text, item, tip, _approvers(root))
    if not ok:
        raise BranchError(f"{item} cannot be merged: {reason}")
    touched = _git(root, "diff", "--name-only", f"{plan}...{branch}", "--", "kanon/work/").stdout.split()
    if touched:
        raise BranchError(f"{branch} changed work files ({', '.join(touched)}); record reviews on {plan} instead")
    origin = _git(root, "symbolic-ref", "--short", "-q", "HEAD", check=False).stdout.strip()
    _git(root, "switch", plan)
    result = _git(root, "merge", "--no-ff", "-m", f"MODIFIED: merge {item} into the {work} plan branch after review",
                  branch, check=False)
    if result.returncode != 0:
        conflicted = _git(root, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
        _git(root, "merge", "--abort", check=False)
        if origin and origin != plan:
            _git(root, "switch", origin, check=False)  # back where the person started (K-391)
        raise BranchError(f"merge stopped and was undone: {', '.join(conflicted) or result.stderr.strip()}")
    return _git(root, "rev-parse", "--short", "HEAD").stdout.strip()


@dataclass
class ItemStatus:
    item: str
    branch: str | None
    merged: bool
    review: str


def status(root: Path, work: str) -> list[ItemStatus]:
    plan = plan_branch(work)
    ref = plan if _exists(root, plan) else None
    _, text = work_file(root, work, ref)
    out = []
    for item in items(text):
        branch = item_branch(work, item)
        exists = _exists(root, branch)
        tip = _git(root, "rev-parse", branch).stdout.strip() if exists else None
        merged = bool(tip) and ref is not None and tip in _merged_parents(root, plan)
        out.append(ItemStatus(item, branch if exists else None, merged, review_state(text, item, tip)[1]))
    return out


def _merged_parents(root: Path, plan: str) -> set[str]:
    """Commits merged into the plan branch as a non-first parent of a merge commit (K-389)."""
    lines = _git(root, "rev-list", "--merges", "--parents", plan, check=False).stdout.splitlines()
    return {parent for line in lines for parent in line.split()[2:]}


def _merged_names(action: str) -> list[str]:
    """Refs named in GIT_REFLOG_ACTION ("merge ..." or "pull ..."), without option values (K-385, K-390)."""
    words = action.split()
    if not words or words[0] not in ("merge", "pull"):
        return []
    names, skip = [], False
    for word in words[1:]:
        if skip:
            skip = False
        elif word in ("-m", "-F", "-s", "-X", "--strategy", "--strategy-option", "--file", "--message"):
            skip = True
        elif not word.startswith("-") and word != ".":
            names.append(word)
    return names


def check_merge(root: Path) -> str | None:
    """For the pre-merge-commit hook: reason to refuse merging an unreviewed item, or None."""
    current = _git(root, "symbolic-ref", "--short", "-q", "HEAD", check=False).stdout.strip()
    match = re.fullmatch(rf"{PREFIX}/(.+)/plan", current)
    if not match:
        return None
    work = match.group(1)
    # Git 2.43 has not written MERGE_HEAD when it runs pre-merge-commit; GIT_REFLOG_ACTION names the
    # merged refs. MERGE_HEAD covers other versions and `git commit` after a refused merge (K-381).
    import os
    heads = [h for h in (_git(root, "rev-parse", "-q", "--verify", f"{w}^{{commit}}", check=False).stdout.strip()
                         for w in _merged_names(os.environ.get("GIT_REFLOG_ACTION", ""))) if h]
    merge_head = root / _git(root, "rev-parse", "--git-path", "MERGE_HEAD").stdout.strip()
    if merge_head.is_file():
        heads += merge_head.read_text().split()
    try:
        _, text = work_file(root, work, "HEAD")
    except BranchError as error:
        return str(error)
    approvers = _approvers(root)
    for head in sorted(set(heads)):
        tips = _git(root, "for-each-ref", "--format=%(refname:short)", "--points-at", head,
                    f"refs/heads/{PREFIX}/{work}/", f"refs/remotes/*/{PREFIX}/{work}/").stdout.split()
        candidates = [t.rsplit("/", 1)[1] for t in tips if t.rsplit("/", 1)[1] != "plan"]
        if not candidates:
            continue
        results = [(item, *review_state(text, item, head, approvers)) for item in candidates]
        if not any(ok for _, ok, _ in results):  # one reviewed item at this commit is enough (K-390)
            item, _, reason = results[0]
            return f"{item} cannot be merged into {current}: {reason}"
    return None


MERGE_HOOK = """#!/bin/sh
# Installed by kanon init. Refuses merging an unreviewed item branch into a Kanon plan branch (P1-09).
# Limit: 'git merge --no-verify' skips it.
if grep -Eq '^name *= *"kanon-engine"' pyproject.toml 2>/dev/null && command -v uv >/dev/null 2>&1; then
  exec uv run --quiet kanon branch check-merge
fi
if command -v kanon >/dev/null 2>&1; then exec kanon branch check-merge; fi
echo "kanon is not installed; the item review check was skipped (a documented limit)"
exit 0
"""
