import datetime as dt
import subprocess
from pathlib import Path

import pytest

from kanon import init as kinit
from kanon import verify as kv
from kanon.cli import main
from kanon.settings import Person

PERSON = Person("owner", "Ada", "developer", "", "owner@laptop")
WORK = "kanon/work/2026-11-16-example.md"

PLAN_ONLY = """---
type: work
status: in-progress
updated: 2026-11-16
---

# Example Work

> **Summary:** An example piece of work.
> **Decision needed:** None yet.

## 1. Plan

| Field | Value |
|---|---|
| Output | A file |
| Creator | Builder |
| Reviewer | Kritos (independent) |

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

REVIEWED = PLAN_ONLY.replace("Not yet reviewed.", """| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| 1 | Example | Kritos | pass | None | Accepted |""").replace("status: in-progress", "status: complete").replace(
    "Pending.", "| Item | Decision |\n|---|---|\n| Example | Approved by owner |")


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def commit(repo, message):
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--no-verify", "-m", message)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    kinit.init(tmp_path, PERSON, dt.date(2026, 11, 16))
    (tmp_path / WORK).write_text(PLAN_ONLY)
    commit(tmp_path, "plan")
    (tmp_path / WORK).write_text(REVIEWED)
    commit(tmp_path, "review")
    return tmp_path


def rules(repo):
    return [(f.path, f.rule, f.message) for f in kv.verify(repo)]


def test_a_correct_instance_passes(repo):
    assert rules(repo) == []


def edit(repo, rel, old, new):
    path = repo / rel
    text = path.read_text()
    assert old in text, old
    path.write_text(text.replace(old, new, 1))


def only(repo, rule, fragment):
    found = rules(repo)
    assert len(found) == 1, found
    assert found[0][1] == rule and fragment in found[0][2], found


@pytest.mark.parametrize("old,new,rule,fragment", [
    ("type: work\n", "", "frontmatter", "missing required field 'type'"),
    ("# Example Work\n", "Example Work\n", "layout", "'# ' title"),
    ("> **Summary:** An example piece of work.\n> **Decision needed:** None yet.\n",
     "Intro line.\n\n> **Summary:** An example piece of work.\n> **Decision needed:** None yet.\n", "layout", "directly after the title"),
    ("> **Decision needed:** None yet.\n", "> **Decision needed:** None yet.\n> a\n> b\n", "layout", "summary block is 4 lines"),
    ("## 5. Cost\n", "## 5. Cost\n\n## 6. Cost\n", "sections", "duplicate section 'Cost'"),
    ("A file", "A file — really", "writing", "dash"),
    ("A file", "A seamless file", "writing", "listed phrase 'seamless'"),
    ("| Creator | Builder |\n", "", "loop", "Creator and a Reviewer"),
    ("| Creator | Builder |", "| Creator | Kritos |", "loop", "must be different"),
    ("| 1 | Example |", "| 4 | Example |", "loop", "exceeds the limit of 3"),
    ("| Example | Approved by owner |", "Pending.", "approval", "no decision is recorded"),
])
def test_each_rule_fails_alone_and_names_itself(repo, old, new, rule, fragment):
    edit(repo, WORK, old, new)
    only(repo, rule, fragment)


def test_escalated_rounds_over_the_limit_are_allowed(repo):
    edit(repo, WORK, "| 1 | Example | Kritos | pass | None | Accepted |",
         "| 4 | Example | Kritos | correct | K-1 | Escalated: owner decides |")
    assert rules(repo) == []


def test_review_without_an_earlier_plan_fails(tmp_path):
    git(tmp_path, "init", "-q")
    kinit.init(tmp_path, PERSON, dt.date(2026, 11, 16))
    (tmp_path / WORK).write_text(REVIEWED)
    commit(tmp_path, "plan and review together")
    only(tmp_path, "loop", "plan first")


def test_an_accepted_exception_covers_only_its_finding(tmp_path):
    test_review_without_an_earlier_plan_fails(tmp_path)
    with (tmp_path / "kanon/kanon.toml").open("a") as f:
        f.write(f'\n[[verify.exceptions]]\npath = "{WORK}"\nrule = "loop"\ncontains = "plan first"\nreason = "Record written after the work."\n')
    open_, covered = kv.verify_with_exceptions(tmp_path)
    assert open_ == [] and len(covered) == 1
    edit(tmp_path, WORK, "A file", "A seamless file")
    assert [f.rule for f in kv.verify(tmp_path)] == ["writing"]


def test_an_incomplete_exception_is_itself_a_problem(repo):
    with (repo / "kanon/kanon.toml").open("a") as f:
        f.write('\n[[verify.exceptions]]\npath = "x"\nrule = "loop"\n')
    only(repo, "settings", "needs path, rule, contains and reason")


def test_open_question_in_review_list_fails(repo):
    edit(repo, "kanon/REVIEW.md", "Nothing is awaiting a decision.", "Nothing is awaiting a decision.\n\nShould we use Postgres?")
    only(repo, "questions", "open question")


def test_code_fences_are_ignored(repo):
    edit(repo, WORK, "## 2. Questions", "```text\n## 9. Cost\nA seamless — thing?\n```\n\n## 2. Questions")
    assert rules(repo) == []


def test_conduct_standard_may_name_phrases_but_not_use_dashes(repo):
    assert "seamless" in (repo / "kanon/docs/conduct-and-writing.md").read_text()
    edit(repo, "kanon/docs/conduct-and-writing.md", "## 1. Working with People", "## 1. Working with People —")
    only(repo, "writing", "dash")


def test_sources_and_archive_are_exempt_from_writing_rules(repo):
    edit(repo, "kanon/sources.md", "verbatim.", "verbatim. A seamless — quote.")
    assert rules(repo) == []


def test_decision_length_limit(repo):
    (repo / "kanon/decisions/001-long.md").write_text(
        "---\ntype: decision\nstatus: proposed\nupdated: 2026-11-16\n---\n\n# ADR-001: Long\n\n> **Decision:** x.\n\n"
        "## Context\n\n## Decision\n\n## Basis\n\n## Consequences\n" + "- point\n" * 60)
    only(repo, "length", "limit for a decision is 60")


def test_invalid_settings_fail(repo):
    edit(repo, "kanon/kanon.toml", 'level = "developer"', 'level = "wizard"')
    only(repo, "settings", "level 'wizard'")


def test_missing_kanon_folder(tmp_path):
    assert [f.rule for f in kv.verify(tmp_path)] == ["layout"]


def test_hook_is_installed_once_and_never_overwritten(tmp_path):
    git(tmp_path, "init", "-q")
    hook = tmp_path / ".git/hooks/pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho mine\n")
    kinit.init(tmp_path, PERSON, dt.date(2026, 11, 16))
    assert hook.read_text() == "#!/bin/sh\necho mine\n"


def test_cli_exit_codes(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    assert main(["verify"]) == 0
    edit(repo, WORK, "A file", "A seamless file")
    assert main(["verify"]) == 1
    assert "1 problem(s)" in capsys.readouterr().out
