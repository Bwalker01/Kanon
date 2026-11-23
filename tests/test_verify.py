import datetime as dt
import subprocess
from pathlib import Path

import pytest

from kanon import init as kinit
from kanon import verify as kv
from kanon.cli import main

APPROVERS = ["ada-dev"]
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
    kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    (tmp_path / WORK).write_text(PLAN_ONLY, encoding="utf-8")
    commit(tmp_path, "plan")
    (tmp_path / WORK).write_text(REVIEWED, encoding="utf-8")
    commit(tmp_path, "review")
    return tmp_path


def rules(repo):
    return [(f.path, f.rule, f.message) for f in kv.verify(repo)]


def test_a_correct_instance_passes(repo):
    assert rules(repo) == []


def edit(repo, rel, old, new):
    path = repo / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


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
    ("| Item | Decision |\n|---|---|\n| Example | Approved by owner |", "Pending.", "approval", "no decision is recorded"),
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
    kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    (tmp_path / WORK).write_text(REVIEWED, encoding="utf-8")
    commit(tmp_path, "plan and review together")
    only(tmp_path, "loop", "not committed on its own")


def test_an_accepted_exception_covers_only_its_finding(tmp_path):
    test_review_without_an_earlier_plan_fails(tmp_path)
    with (tmp_path / "kanon/kanon.toml").open("a", encoding="utf-8") as f:
        f.write(f'\n[[verify.exceptions]]\npath = "{WORK}"\nrule = "loop"\ncontains = "not committed on its own"\nreason = "Record written after the work."\n')
    open_, covered = kv.verify_with_exceptions(tmp_path)
    assert open_ == [] and len(covered) == 1
    edit(tmp_path, WORK, "A file", "A seamless file")
    assert [f.rule for f in kv.verify(tmp_path)] == ["writing"]


def test_an_incomplete_exception_is_itself_a_problem(repo):
    with (repo / "kanon/kanon.toml").open("a", encoding="utf-8") as f:
        f.write('\n[[verify.exceptions]]\npath = "x"\nrule = "loop"\n')
    only(repo, "settings", "needs path, rule, reason")


def test_question_in_decision_needed_line_fails(repo):
    edit(repo, WORK, "> **Decision needed:** None yet.", "> **Decision needed:** Should we use Postgres?")
    only(repo, "questions", "Decision needed")

def test_code_fences_are_ignored(repo):
    edit(repo, WORK, "## 2. Questions", "```text\n## 9. Cost\nA seamless — thing?\n```\n\n## 2. Questions")
    assert rules(repo) == []


def test_conduct_standard_may_name_phrases_but_not_use_dashes(repo):
    assert "seamless" in (repo / "kanon/docs/conduct-and-writing.md").read_text(encoding="utf-8")
    edit(repo, "kanon/docs/conduct-and-writing.md", "## 1. Working with People", "## 1. Working with People —")
    only(repo, "writing", "dash")


def test_sources_and_archive_are_exempt_from_writing_rules(repo):
    edit(repo, "kanon/sources.md", "verbatim.", "verbatim. A seamless — quote.")
    assert rules(repo) == []


def test_decision_length_limit(repo):
    (repo / "kanon/decisions/001-long.md").write_text(
        "---\ntype: decision\nstatus: proposed\nupdated: 2026-11-16\n---\n\n# ADR-001: Long\n\n> **Decision:** x.\n\n"
        "## Context\n\n## Decision\n\n## Basis\n\n## Consequences\n" + "- point\n" * 60, encoding="utf-8")
    only(repo, "length", "limit for a decision is 60")


def test_invalid_settings_fail(repo):
    edit(repo, "kanon/kanon.toml", 'approvers = ["ada-dev"]', 'approvers = ["not valid!"]')
    only(repo, "settings", "not a valid GitHub username")


def test_missing_kanon_folder(tmp_path):
    assert [f.rule for f in kv.verify(tmp_path)] == ["layout"]


def test_hook_is_installed_once_and_never_overwritten(tmp_path):
    git(tmp_path, "init", "-q")
    hook = tmp_path / ".git/hooks/pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
    kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    assert hook.read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n"


def test_cli_exit_codes(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    assert main(["verify"]) == 0
    edit(repo, WORK, "A file", "A seamless file")
    assert main(["verify"]) == 1
    assert "1 problem(s)" in capsys.readouterr().out


@pytest.mark.parametrize("old,new,rule,fragment", [
    ("## 4. Decision", "## 4. Decisions", "sections", "missing section 'Decision'"),
    ("> **Summary:** An example piece of work.", "> An example piece of work.", "summary", "missing summary block"),
    ("status: complete", "status: done", "frontmatter", "status 'done'"),
    ("updated: 2026-11-16", "updated: 2026-02-30", "frontmatter", "unreadable"),
    ("| 1 | Example |", "| 1a | Example |", "loop", "round '1a'"),
    ("| 1 | Example | Kritos | pass | None | Accepted |",
     "| 1 | Example | Kritos | pass | None | Accepted |\n\nNot yet reviewed. Round 9 pending.", "loop", ""),
    ("## 2. Questions", "~~~\nA seamless thing.\n~~~\n\n## 2. Questions", None, None),
    ("## 2. Questions", "```\nnever closed\n\n## 2. Questions", "layout", "never closed"),
])
def test_more_rules_fail_alone(repo, old, new, rule, fragment):
    edit(repo, WORK, old, new)
    found = rules(repo)
    if rule is None:
        assert found == []
    elif fragment == "":
        assert found == [], found  # placeholder text inside a real review no longer hides anything
    else:
        assert any(r == rule and fragment in m for _, r, m in found), found


def test_rounds_hidden_by_placeholder_text_are_still_counted(repo):
    edit(repo, WORK, "| 1 | Example | Kritos | pass | None | Accepted |",
         "| 9 | Example | Kritos | pass | None | Accepted |\n\nNot yet reviewed. Round 10 pending.")
    only(repo, "loop", "round 9 exceeds the limit of 3")


def test_group_round_limit_applies_to_lettered_groups(repo):
    edit(repo, WORK, "| Reviewer | Kritos (independent) |", "| Reviewer | Kritos (independent) |\n| Group round limit | 2 |")
    edit(repo, WORK, "| 1 | Example |", "| B3 | Example |")
    only(repo, "loop", "round B3 exceeds the limit of 2")


def test_a_bare_template_plan_does_not_count_as_a_plan(tmp_path):
    git(tmp_path, "init", "-q")
    kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    path = kinit.new_work(tmp_path, "example", dt.date(2026, 11, 16))
    commit(tmp_path, "empty template")
    (tmp_path / "src.py").write_text("x = 1\n", encoding="utf-8")
    path.write_text(REVIEWED, encoding="utf-8")
    commit(tmp_path, "plan, build and review together")
    found = rules(tmp_path)
    assert any("not committed on its own" in m for _, _, m in found), found


def test_plan_committed_with_build_files_fails(tmp_path):
    git(tmp_path, "init", "-q")
    kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    (tmp_path / WORK).write_text(PLAN_ONLY, encoding="utf-8")
    (tmp_path / "src.py").write_text("x = 1\n", encoding="utf-8")
    commit(tmp_path, "plan and build together")
    (tmp_path / WORK).write_text(REVIEWED, encoding="utf-8")
    commit(tmp_path, "review")
    only(tmp_path, "loop", "not committed on its own")


@pytest.mark.parametrize("doc_type,limit", [("decision", 60), ("standard", 150)])
def test_length_limits_are_exact(repo, doc_type, limit):
    marker = "> **Decision:** x." if doc_type == "decision" else "> **Summary:** x."
    sections = "## Context\n\n## Decision\n\n## Basis\n\n## Consequences\n" if doc_type == "decision" else ""
    head = f"---\ntype: {doc_type}\nstatus: proposed\nupdated: 2026-11-16\n---\n\n# Title\n\n{marker}\n\n{sections}"
    filler = limit - len(head.splitlines())
    path = repo / f"kanon/docs/{doc_type}-limit.md"
    path.write_text(head + "- point\n" * filler, encoding="utf-8")
    assert rules(repo) == []
    path.write_text(head + "- point\n" * (filler + 1), encoding="utf-8")
    only(repo, "length", f"limit for a {doc_type} is {limit}")


def test_sources_type_outside_its_path_is_a_finding(repo):
    (repo / "kanon/docs/notes.md").write_text(
        "---\ntype: sources\nstatus: reference\nupdated: 2026-11-16\n---\n\n# Notes\n\n> **Summary:** x.\n\nA seamless thing.\n", encoding="utf-8")
    found = rules(repo)
    assert any(r == "layout" and "only allowed at kanon/sources.md" in m for _, r, m in found)
    assert any(r == "writing" for _, r, _ in found)


def test_conduct_exemption_is_by_exact_path(repo):
    (repo / "kanon/work/my-conduct-and-writing.md").write_text(PLAN_ONLY.replace("A file", "A seamless file"), encoding="utf-8")
    assert any(r == "writing" for _, r, _ in rules(repo))


def test_generated_desk_is_never_checked_or_committed(repo):
    (repo / "kanon/local").mkdir(exist_ok=True)
    (repo / "kanon/local/DESK.md").write_text("no frontmatter, a seamless \u2014 note")
    assert rules(repo) == []
    git(repo, "add", "-f", "kanon/local/DESK.md")
    only(repo, "privacy", "generated agent file is committed")

def test_unused_exception_is_reported(repo):
    with (repo / "kanon/kanon.toml").open("a", encoding="utf-8") as f:
        f.write('\n[[verify.exceptions]]\npath = "kanon/x.md"\nrule = "loop"\ncontains = "something long"\nreason = "r"\n')
    only(repo, "settings", "matches nothing")


def test_short_exception_match_is_refused(repo):
    with (repo / "kanon/kanon.toml").open("a", encoding="utf-8") as f:
        f.write(f'\n[[verify.exceptions]]\npath = "{WORK}"\nrule = "loop"\ncontains = "e"\nreason = "r"\n')
    only(repo, "settings", "at least 8 characters")


def test_root_instruction_files_get_the_writing_check(repo):
    (repo / "AGENTS.md").write_text("# Team\n\nA note \u2014 here.\n", encoding="utf-8")
    only(repo, "writing", "dash")


def test_new_work_creates_a_valid_file_once(tmp_path):
    git(tmp_path, "init", "-q")
    kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    path = kinit.new_work(tmp_path, "Add caching", dt.date(2026, 11, 16))
    assert path.name == "2026-11-16-add-caching.md"
    assert "# Add caching" in path.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        kinit.new_work(tmp_path, "add caching", dt.date(2026, 11, 16))


def test_existing_hook_is_reported(tmp_path):
    git(tmp_path, "init", "-q")
    hook = tmp_path / ".git/hooks/pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\n", encoding="utf-8")
    result = kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    assert any("existing pre-commit hook was kept" in w for w in result.warnings)


def test_an_outdated_kanon_hook_is_updated_but_others_are_not(tmp_path):
    git(tmp_path, "init", "-q")
    hook = tmp_path / ".git/hooks/pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\n# Installed by kanon init. Old version.\nexit 0\n", encoding="utf-8")
    result = kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    assert hook.read_text(encoding="utf-8") == kv.HOOK and ".git/hooks/pre-commit" in result.updated
    result = kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    assert ".git/hooks/pre-commit" in result.kept


def test_a_quote_before_the_summary_marker_fails(repo):
    edit(repo, WORK, "> **Summary:** An example piece of work.", "> Note.\n> **Summary:** An example piece of work.")
    only(repo, "layout", "must come directly after the title")


def test_an_empty_output_row_means_the_plan_is_not_filled(tmp_path):
    git(tmp_path, "init", "-q")
    kinit.init(tmp_path, APPROVERS, dt.date(2026, 11, 16))
    (tmp_path / WORK).write_text(PLAN_ONLY.replace("| Output | A file |", "| Output | |"), encoding="utf-8")
    commit(tmp_path, "plan without an output")
    (tmp_path / "src.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / WORK).write_text(REVIEWED, encoding="utf-8")
    commit(tmp_path, "output, build and review together")
    only(tmp_path, "loop", "not committed on its own")


def test_archive_exemption_is_only_for_the_top_level_archive(repo):
    (repo / "kanon/docs/archive").mkdir()
    (repo / "kanon/docs/archive/x.md").write_text(
        "---\ntype: doc\nstatus: draft\nupdated: 2026-11-16\n---\n\n# X\n\n> **Summary:** x.\n\nA seamless thing.\n", encoding="utf-8")
    only(repo, "writing", "seamless")


def test_negated_escalation_does_not_lift_the_round_limit(repo):
    edit(repo, WORK, "| 1 | Example | Kritos | pass | None | Accepted |",
         "| 7 | Example | Kritos | pass | None | Fixed; no escalation needed |")
    only(repo, "loop", "round 7 exceeds")


def test_new_work_requires_kanon_init(tmp_path):
    git(tmp_path, "init", "-q")
    with pytest.raises(RuntimeError, match="run kanon init first"):
        kinit.new_work(tmp_path, "x")


@pytest.mark.parametrize("table,fragment", [
    ("| ID | Action | Assignee | Done |\n|---|---|---|---|\n| A-1 | x | ada-dev | no |", "lacks column(s): blocks"),
    ("| ID | Action | Assignee | Blocks | Done |\n|---|---|---|---|---|\n| A-1 | x | not valid! | | no |", "GitHub username"),
    ("| ID | Action | Assignee | Blocks | Done |\n|---|---|---|---|---|\n| A-1 | x | ada-dev | | maybe |", "yes or no"),
    ("| ID | Action | Assignee | Blocks | Done |\n|---|---|---|---|---|\n| A-1 | x | ada-dev | A-9 | no |", "unknown action 'A-9'"),
    ("| ID | Action | Assignee | Blocks | Done |\n|---|---|---|---|---|\n| A-1 | `a|b` | ada-dev | | no |", "wrong number of cells"),
    ("| ID | Action | Assignee | Blocks | Done |\n|---|---|---|---|---|\n| A-1 | x | ada-dev | | no |\n\n### A-7: Stray", "match no row"),
])
def test_actions_tables_are_checked(repo, table, fragment):
    edit(repo, WORK, "## 3. Review", f"## 3. Actions\n\n{table}\n\n## 3. Review")
    found = [m for _, r, m in rules(repo) if r == "actions"]
    assert any(fragment in m for m in found), found


def test_question_on_a_continuation_line_of_decision_needed_fails(repo):
    edit(repo, WORK, "> **Decision needed:** None yet.", "> **Decision needed:** Choose a store.\n> Postgres or SQLite?")
    only(repo, "questions", "Decision needed")


def test_a_row_with_the_wrong_cell_count_is_reported_on_its_own_line(repo):  # K-241
    table = "| ID | Action | Assignee | Blocks | Done |\n|---|---|---|---|---|\n| A-1 | `a|b` | ada-dev | | no |"
    edit(repo, WORK, "## 3. Review", f"## 3. Actions\n\n{table}\n\n## 3. Review")
    lines = (repo / WORK).read_text().splitlines()
    row = next(i for i, l in enumerate(lines, 1) if l.startswith("| A-1 |"))
    found = [f for f in kv.verify(repo) if f.rule == "actions" and "wrong number of cells" in f.message]
    assert found and found[0].line == row
