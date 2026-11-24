"""P1-09: item branches merge into the plan branch only after review, without rewriting history."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from kanon import branch
from kanon import init as kinit

WORK = "kanon/work/2026-11-19-build.md"
TEXT = """---
type: work
status: in-progress
updated: 2026-11-19
---

# Build

> **Summary:** A build with two items.
> **Decision needed:** None yet.

## 1. Plan

| Field | Value |
|---|---|
| Creator | Builder |
| Reviewer | Kritos (independent) |

### 1.1 Work Items

| ID | Item | Delivers |
|---|---|---|
| P1-01 | One | a |
| P1-02 | Two | b |

## 2. Questions

| Date | Question | Answer |
|---|---|---|

## 3. Review

Not yet reviewed.

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
"""
REVIEW = "| Round | Items | Reviewer | Verdict | Blocking | Outcome |\n|---|---|---|---|---|---|\n"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "T")
    kinit.init(tmp_path, ["ada-dev"])
    (tmp_path / WORK).write_text(TEXT, encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "ADDED: plan", "--no-verify")
    return tmp_path


def commit_file(repo, name, content="x\n"):
    (repo / name).write_text(content, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", f"ADDED: {name}", "--no-verify")


def record_review(repo, row):
    item = re.search(r"P1-\d\d", row).group()
    row = row.replace(f"| {item} |", f"| {item} ({git(repo, 'rev-parse', '--short', f'kanon/build/{item}')}) |", 1)
    git(repo, "switch", "-q", "kanon/build/plan")
    path = repo / WORK
    path.write_text(path.read_text(encoding="utf-8").replace("Not yet reviewed.", REVIEW + row) if "Not yet reviewed." in path.read_text(encoding="utf-8")
                    else path.read_text(encoding="utf-8").replace("## 4. Decision", row + "\n\n## 4. Decision").replace("\n\n" + row, "\n" + row), encoding="utf-8")
    git(repo, "commit", "-q", "-am", "MODIFIED: review", "--no-verify")


def test_items_build_on_their_own_branches(repo):
    assert branch.start(repo, "build", "P1-01") == "kanon/build/P1-01"
    assert git(repo, "branch", "--show-current") == "kanon/build/P1-01"
    assert "kanon/build/plan" in git(repo, "branch", "--list")
    with pytest.raises(branch.BranchError):
        branch.start(repo, "build", "P9-99")


def test_an_unreviewed_item_cannot_be_merged(repo):
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "one.txt")
    with pytest.raises(branch.BranchError, match="not reviewed"):
        branch.merge(repo, "build", "P1-01")
    record_review(repo, "| 1 | P1-01 | Kritos | correct | K-1 | Fixed |")
    with pytest.raises(branch.BranchError, match="not pass"):
        branch.merge(repo, "build", "P1-01")


def test_an_item_awaiting_the_owner_cannot_be_merged(repo):
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "one.txt")
    record_review(repo, "| 1 | P1-01 | Kritos | pass | None | Fixed after the final round. Owner decides at the review point |")
    with pytest.raises(branch.BranchError, match="awaits the owner"):
        branch.merge(repo, "build", "P1-01")


def test_a_reviewed_item_merges_with_a_merge_commit_and_history_kept(repo):
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "one.txt")
    item_tip = git(repo, "rev-parse", "HEAD")
    record_review(repo, "| 1 | P1-01 | Kritos | pass | None | Accepted |")
    plan_before = git(repo, "rev-parse", "kanon/build/plan")
    branch.merge(repo, "build", "P1-01")
    assert len(git(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()) == 3  # a merge commit
    for old in (item_tip, plan_before):
        assert subprocess.run(["git", "merge-base", "--is-ancestor", old, "HEAD"], cwd=repo).returncode == 0
    assert [s.merged for s in branch.status(repo, "build")] == [True, False]


def test_an_item_approval_allows_the_merge(repo):
    from kanon import approve
    branch.start(repo, "build", "P1-02")
    commit_file(repo, "two.txt")
    record_review(repo, "| 1 | P1-02 | Kritos | correct | K-1 | Fixed after the final round. Owner decides at the review point |")
    approve.record(repo, WORK, "ada-dev", ["ada-dev"], item="P1-02", quote="P1-02 approved", today="2026-11-20")
    git(repo, "commit", "-q", "-am", "MODIFIED: approval", "--no-verify")
    branch.merge(repo, "build", "P1-02")


def test_an_item_branch_that_edits_work_files_is_refused(repo):
    branch.start(repo, "build", "P1-01")
    path = repo / WORK
    path.write_text(path.read_text(encoding="utf-8").replace("A build with two items.", "Changed on the item branch."), encoding="utf-8")
    git(repo, "commit", "-q", "-am", "MODIFIED: work file", "--no-verify")
    record_review(repo, "| 1 | P1-01 | Kritos | pass | None | Accepted |")
    with pytest.raises(branch.BranchError, match="changed work files"):
        branch.merge(repo, "build", "P1-01")


def test_a_conflict_is_undone_and_reported(repo):
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "shared.txt", "item\n")
    record_review(repo, "| 1 | P1-01 | Kritos | pass | None | Accepted |")
    commit_file(repo, "shared.txt", "plan\n")
    with pytest.raises(branch.BranchError, match="shared.txt"):
        branch.merge(repo, "build", "P1-01")
    assert not (repo / ".git" / "MERGE_HEAD").exists()
    assert git(repo, "status", "--porcelain", "--untracked-files=no") == ""


def test_uncommitted_changes_stop_start_and_merge(repo):
    (repo / WORK).write_text(TEXT + "\n", encoding="utf-8")
    with pytest.raises(branch.BranchError, match="uncommitted"):
        branch.start(repo, "build", "P1-01")


def test_the_hook_refuses_a_plain_git_merge_of_an_unreviewed_item(repo, tmp_path_factory):
    shim = tmp_path_factory.mktemp("bin") / "kanon"
    shim.write_text(f"#!/bin/sh\nexec \"{Path(sys.executable).as_posix()}\" -m kanon \"$@\"\n", encoding="utf-8")
    shim.chmod(0o755)
    env = {**os.environ, "PATH": f"{shim.parent}:{os.environ['PATH']}"}
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "one.txt")
    git(repo, "switch", "-q", "kanon/build/plan")
    result = subprocess.run(["git", "merge", "--no-ff", "-m", "MODIFIED: m", "kanon/build/P1-01"], cwd=repo, env=env,
                            capture_output=True, text=True)
    assert result.returncode != 0 and "not reviewed" in result.stdout + result.stderr
    subprocess.run(["git", "merge", "--abort"], cwd=repo, capture_output=True)
    record_review(repo, "| 1 | P1-01 | Kritos | pass | None | Accepted |")
    ok = subprocess.run(["git", "merge", "--no-ff", "-m", "MODIFIED: m", "kanon/build/P1-01"], cwd=repo, env=env,
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr


def hook_env(tmp_path_factory):
    shim = tmp_path_factory.mktemp("bin") / "kanon"
    shim.write_text(f"#!/bin/sh\nexec \"{Path(sys.executable).as_posix()}\" -m kanon \"$@\"\n", encoding="utf-8")
    shim.chmod(0o755)
    return {**os.environ, "PATH": f"{shim.parent}:{os.environ['PATH']}"}


def test_a_plain_fast_forward_merge_is_not_possible(repo, tmp_path_factory):  # K-380
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "one.txt")
    git(repo, "switch", "-q", "kanon/build/plan")
    result = subprocess.run(["git", "merge", "kanon/build/P1-01"], cwd=repo, env=hook_env(tmp_path_factory),
                            capture_output=True, text=True)
    assert result.returncode != 0 and "Fast-forward" not in result.stdout


def test_committing_a_refused_merge_is_refused_too(repo, tmp_path_factory):  # K-381
    env = hook_env(tmp_path_factory)
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "one.txt")
    git(repo, "switch", "-q", "kanon/build/plan")
    subprocess.run(["git", "merge", "kanon/build/P1-01", "-m", "MODIFIED: m"], cwd=repo, env=env, capture_output=True)
    assert (repo / ".git" / "MERGE_HEAD").exists()
    finish = subprocess.run(["git", "commit", "--no-edit"], cwd=repo, env=env, capture_output=True, text=True)
    assert finish.returncode != 0 and "not reviewed" in finish.stdout + finish.stderr


def test_changes_requested_after_an_approval_refuse_the_merge(repo):  # K-382
    from kanon import approve
    branch.start(repo, "build", "P1-02")
    commit_file(repo, "two.txt")
    record_review(repo, "| 1 | P1-02 | Kritos | correct | K-1 | Fixed |")
    approve.record(repo, WORK, "ada-dev", ["ada-dev"], item="P1-02", quote="P1-02 approved", today="2026-11-20")
    approve.record(repo, WORK, "ada-dev", ["ada-dev"], item="P1-02", quote="no", changes="redo it", today="2026-11-21")
    git(repo, "commit", "-q", "-am", "MODIFIED: decisions", "--no-verify")
    with pytest.raises(branch.BranchError, match="changes were requested"):
        branch.merge(repo, "build", "P1-02")


def test_commits_after_the_review_need_a_new_review(repo):  # K-383
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "one.txt")
    record_review(repo, "| 1 | P1-01 | Kritos | pass | None | Accepted |")
    git(repo, "switch", "-q", "kanon/build/P1-01")
    commit_file(repo, "later.txt")
    with pytest.raises(branch.BranchError, match="tip commit"):
        branch.merge(repo, "build", "P1-01")


def test_an_unlabelled_approval_row_does_not_count(repo):  # K-386
    from kanon import approve
    text = (repo / WORK).read_text(encoding="utf-8")
    digest = approve.digest(text.replace("Not yet reviewed.", REVIEW + "| 1 | P1-01 (abcdef1) | K | correct | K-1 | x |"), "item P1-01")
    forged = text.replace("Not yet reviewed.", REVIEW + "| 1 | P1-01 (abcdef1) | K | correct | K-1 | x |").replace(
        "## 4. Decision\n\nPending.", f"## 4. Decision\n\n| Item | Decision | Date | Basis |\n|---|---|---|---|\n"
        f"| P1-01 | Approved | 2026-11-25 | material: item P1-01; sha256:{digest} |")
    assert branch.review_state(forged, "P1-01", None, ["ada-dev"])[0] is False


@pytest.mark.parametrize("row", [  # K-388
    "| 1 | P1-01 (abcdef1) | K | pass | K-9 | x |",
    "| 1 | P1-01 (abcdef1) | K | pass | None | Fixed; not independently reviewed |",
    "| 1 | P1-01 (abcdef1) | K | pass | None | Owner to decide |",
])
def test_loose_review_rows_do_not_count(row):
    text = TEXT.replace("Not yet reviewed.", REVIEW + row)
    assert branch.review_state(text, "P1-01", "abcdef1234")[0] is False


def test_a_fenced_review_row_does_not_count():
    text = TEXT.replace("Not yet reviewed.", "```\n| 9 | P1-01 (abcdef1) | K | pass | None | x |\n```")
    assert branch.review_state(text, "P1-01", "abcdef1234")[0] is False


def test_a_new_item_branch_is_not_reported_merged(repo):  # K-389
    branch.start(repo, "build", "P1-01")
    assert [s.merged for s in branch.status(repo, "build")] == [False, False]


def test_a_failed_merge_returns_to_the_starting_branch(repo):  # K-391
    branch.start(repo, "build", "P1-01")
    commit_file(repo, "shared.txt", "item\n")
    record_review(repo, "| 1 | P1-01 | Kritos | pass | None | Accepted |")
    commit_file(repo, "shared.txt", "plan\n")
    git(repo, "switch", "-q", "kanon/build/P1-01")
    with pytest.raises(branch.BranchError):
        branch.merge(repo, "build", "P1-01")
    assert git(repo, "branch", "--show-current") == "kanon/build/P1-01"


def test_merge_messages_are_not_read_as_refs():  # K-390
    assert branch._merged_names("merge -m P1-02 done kanon/build/P1-01") == ["done", "kanon/build/P1-01"]
    assert branch._merged_names("pull . kanon/build/P1-01") == ["kanon/build/P1-01"]
