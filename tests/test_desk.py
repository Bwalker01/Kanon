import datetime as dt
import json
import re
import subprocess

import pytest

from kanon import desk
from kanon import init as kinit
from kanon import sync as ksync

TODAY = dt.date(2026, 11, 18)


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def commit(repo, message):
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--no-verify", "-m", message)


def work_file(title, actions="", status="in-progress", needed="None yet."):
    section = f"\n## 3. Actions\n\n{actions}\n" if actions else ""
    return f"""---
type: work
status: {status}
updated: 2026-11-18
---

# {title}

> **Summary:** {title} summary.
> **Decision needed:** {needed}

## 1. Plan

| Field | Value |
|---|---|
| Creator | Builder |
| Reviewer | Kritos |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
{section}
## 4. Review

Not yet reviewed.

## 5. Decision

Pending.

## 6. Cost

None.
"""


ACTIONS = """| ID | Action | Assignee | Blocks | Done |
|---|---|---|---|---|
| A-2 | Protect main | ada-dev | | no |
| A-1 | Merge the branch | ada-dev | A-2 | no |
| A-3 | Bo's job | bo-dev | | no |
| A-4 | Already done | ada-dev | | yes |

### A-1: Merge the branch

1. Open the pull request.
2. Merge without squashing.

### A-2: Protect main

1. Add a ruleset.
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    monkeypatch.setenv("KANON_PROFILE", json.dumps({"github": "ada-dev", "name": "Ada"}))
    kinit.init(tmp_path, ["ada-dev", "bo-dev"], TODAY)
    commit(tmp_path, "init")
    return tmp_path


def test_desk_lists_only_this_persons_open_actions_in_dependency_order(repo):
    (repo / "kanon/work/2026-11-18-setup.md").write_text(work_file("Setup", ACTIONS))
    built = desk.build(repo)
    assert [a.id for a in built.actions] == ["A-1", "A-2"]
    assert built.actions[0].steps == ["Open the pull request.", "Merge without squashing."]


def test_awaiting_approval_becomes_a_decision_for_approvers_only(repo, monkeypatch):
    (repo / "kanon/work/2026-11-18-plan.md").write_text(work_file("Plan", status="awaiting-approval", needed="Approve the plan."))
    built = desk.build(repo)
    assert [(d.id, d.needed) for d in built.decisions] == [("R-1", "Approve the plan.")]
    monkeypatch.setenv("KANON_PROFILE", json.dumps({"github": "outsider"}))
    assert desk.build(repo).decisions == []


def test_late_fixes_marked_for_the_owner_appear_under_review_later(repo):
    text = work_file("Fixes").replace("Not yet reviewed.", "| Round | Items | Reviewer | Verdict | Blocking | Outcome |\n"
        "|---|---|---|---|---|---|\n| 2 | Fixes | Kritos | correct | K-1 | Fixed after the final round. Owner decides at the review point |")
    (repo / "kanon/work/2026-11-18-fixes.md").write_text(text)
    assert [r.round for r in desk.build(repo).reviews] == ["2"]


def test_removing_an_action_removes_it_from_the_desk(repo):
    path = repo / "kanon/work/2026-11-18-setup.md"
    path.write_text(work_file("Setup", ACTIONS))
    desk.write(repo)
    assert "Merge the branch" in (repo / "kanon/local/DESK.md").read_text()
    path.write_text(work_file("Setup"))
    desk.write(repo)
    assert "Merge the branch" not in (repo / "kanon/local/DESK.md").read_text()


def test_desk_page_loads_nothing_external_and_escapes_text(repo):
    (repo / "kanon/work/2026-11-18-setup.md").write_text(work_file("Setup <script>", ACTIONS))
    desk.write(repo)
    page = (repo / "kanon/local/desk.html").read_text()
    assert not re.search(r'(src|href)\s*=\s*["\']?https?:', page)
    assert "<script>alert" not in page and "Setup &lt;script&gt;" in page


def test_two_branches_add_work_and_merge_without_conflict(repo):
    git(repo, "checkout", "-q", "-b", "feature-a")
    (repo / "kanon/work/2026-11-18-a.md").write_text(work_file("A", ACTIONS, status="awaiting-approval"))
    ksync.sync(repo)
    commit(repo, "a")
    git(repo, "checkout", "-q", "-")
    git(repo, "checkout", "-q", "-b", "feature-b")
    (repo / "kanon/work/2026-11-18-b.md").write_text(work_file("B", ACTIONS, status="awaiting-approval"))
    ksync.sync(repo)
    commit(repo, "b")
    git(repo, "merge", "-q", "--no-edit", "feature-a")
    assert git(repo, "ls-files", "kanon/local") == ""
    built = desk.build(repo)
    assert len(built.decisions) == 2 and len(built.actions) == 4


def test_without_a_profile_everything_is_shown_with_a_note(repo, monkeypatch):
    monkeypatch.delenv("KANON_PROFILE")
    (repo / "kanon/work/2026-11-18-setup.md").write_text(work_file("Setup", ACTIONS))
    built = desk.build(repo)
    assert len(built.actions) == 3 and any("showing every person's items" in n for n in built.notes)
