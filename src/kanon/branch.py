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


def review_state(text: str, item: str) -> tuple[bool, str]:
    """(may merge, reason) for an item, from the plan branch's work file."""
    for row in reversed(approve.decision_rows(text)):
        if row.kind == f"item {item}" and row.decision.lower().startswith("approved"):
            if row.hash and row.hash == approve.digest(text, row.kind):
                return True, f"approved ({row.date})"
            return False, "approved, but the approved record has changed since"
    latest = None
    section = None
    for line in text.split("\n"):
        if line.startswith("## "):
            section = re.sub(r"^## (?:\d+\.\s+)?", "", line).strip()
        elif section == "Review" and line.startswith("|"):
            cells = [c.strip() for c in approve.CELL_SPLIT.split(line.strip().strip("|"))]
            if len(cells) >= 6 and approve._names_item(cells[1], item):
                latest = cells
    if latest is None:
        return False, "not reviewed"
    verdict, outcome = latest[3].strip("` ").lower(), latest[-1].lower()
    if "owner decides" in outcome and "owner reviewed" not in outcome:
        return False, f"round {latest[0]} awaits the owner's decision"
    if verdict == "pass":
        return True, f"review round {latest[0]} passed"
    return False, f"latest review round {latest[0]} is '{verdict}', not pass"


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
    ok, reason = review_state(text, item)
    if not ok:
        raise BranchError(f"{item} cannot be merged: {reason}")
    touched = _git(root, "diff", "--name-only", f"{plan}...{branch}", "--", "kanon/work/").stdout.split()
    if touched:
        raise BranchError(f"{branch} changed work files ({', '.join(touched)}); record reviews on {plan} instead")
    _git(root, "switch", plan)
    result = _git(root, "merge", "--no-ff", "-m", f"MODIFIED: merge {item} into the {work} plan branch after review",
                  branch, check=False)
    if result.returncode != 0:
        conflicted = _git(root, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
        _git(root, "merge", "--abort", check=False)
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
        merged = exists and ref is not None and _git(
            root, "merge-base", "--is-ancestor", branch, plan, check=False).returncode == 0
        out.append(ItemStatus(item, branch if exists else None, merged, review_state(text, item)[1]))
    return out


def check_merge(root: Path) -> str | None:
    """For the pre-merge-commit hook: reason to refuse merging an unreviewed item, or None."""
    current = _git(root, "symbolic-ref", "--short", "-q", "HEAD", check=False).stdout.strip()
    match = re.fullmatch(rf"{PREFIX}/(.+)/plan", current)
    if not match:
        return None
    work = match.group(1)
    # Git 2.43 has not written MERGE_HEAD when it runs pre-merge-commit; GIT_REFLOG_ACTION names the
    # merged refs ("merge <ref>..."). MERGE_HEAD is the fallback for other versions.
    import os
    action = os.environ.get("GIT_REFLOG_ACTION", "")
    wanted = [a for a in action.split()[1:] if not a.startswith("-")] if action.startswith("merge") else []
    heads = [h for h in (_git(root, "rev-parse", "-q", "--verify", f"{w}^{{commit}}", check=False).stdout.strip()
                         for w in wanted) if h]
    merge_head = _git(root, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).stdout.strip()
    heads += [merge_head] if merge_head else []
    tips = sorted({t for h in heads for t in _git(root, "for-each-ref", "--format=%(refname:short)", "--points-at", h,
                                                   f"refs/heads/{PREFIX}/{work}/").stdout.split()})
    for tip in tips:
        item = tip.rsplit("/", 1)[1]
        if item == "plan":
            continue
        try:
            _, text = work_file(root, work, "HEAD")
        except BranchError as error:
            return str(error)
        ok, reason = review_state(text, item)
        if not ok:
            return f"{item} cannot be merged into {current}: {reason}"
    return None


MERGE_HOOK = """#!/bin/sh
# Installed by kanon init. Refuses merging an unreviewed item branch into a Kanon plan branch (P1-09).
# Limit: 'git merge --no-verify' skips it.
if grep -q '^name = "kanon-engine"' pyproject.toml 2>/dev/null && command -v uv >/dev/null 2>&1; then
  exec uv run --quiet kanon branch check-merge
fi
if command -v kanon >/dev/null 2>&1; then exec kanon branch check-merge; fi
echo "kanon is not installed; the item review check was skipped"
exit 0
"""
