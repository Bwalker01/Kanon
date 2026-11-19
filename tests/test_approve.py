"""P1-05: hashed, labelled approvals, their verify checks and the self-approval refusal."""

import json
import subprocess

import pytest

from kanon import approve
from kanon import sync as ksync
from kanon.cli import main
from test_verify import APPROVERS, WORK, rules
from test_verify import repo as reviewed_repo  # noqa: F401  (fixture)

TODAY = "2026-11-20"


@pytest.fixture
def repo(reviewed_repo):  # noqa: F811
    """A reviewed work file with no decision yet."""
    path = reviewed_repo / WORK
    body = path.read_text().replace("status: complete", "status: awaiting-approval")
    path.write_text(body[:body.index("## 4. Decision")] + "## 4. Decision\n\nPending.\n\n" + body[body.index("## 5. Cost"):])
    return reviewed_repo


def text(repo):
    return (repo / WORK).read_text()


def approval_findings(repo):
    return [m for _, r, m in rules(repo) if r == "approval"]


def test_approval_records_form_commit_and_hash(repo):
    row = approve.record(repo, WORK, "ada-dev", APPROVERS, today=TODAY)
    assert "Approved by ada-dev with kanon approve" in row and "material: result" in row
    assert approve.HASH.search(row).group(1) == approve.digest(text(repo), approve.RESULT)
    assert "status: complete" in text(repo) and "> **Decision needed:** None. Approved by ada-dev" in text(repo)
    assert approval_findings(repo) == []


def test_transcription_is_labelled_with_the_persons_words(repo):
    row = approve.record(repo, WORK, "ada-dev", APPROVERS, quote="approve example", today=TODAY)
    assert 'Owner in chat: "approve example". Transcribed by the assistant for ada-dev' in row
    with pytest.raises(ValueError):
        approve.record(repo, WORK, "ada-dev", APPROVERS, quote="  ", today=TODAY)


def test_changing_approved_material_fails_verify(repo):
    approve.record(repo, WORK, "ada-dev", APPROVERS, today=TODAY)
    path = repo / WORK
    path.write_text(text(repo).replace("| Output | A file |", "| Output | Two files |"))
    assert any("has changed since it was approved" in m for m in approval_findings(repo))


def test_status_summary_actions_and_cost_may_change_after_approval(repo):
    approve.record(repo, WORK, "ada-dev", APPROVERS, today=TODAY)
    changed = text(repo).replace("> **Summary:** An example piece of work.", "> **Summary:** Reworded.")
    changed = changed.replace("Recorded when work starts.", "| Step | Cost |\n|---|---|\n| Build | $1 |")
    (repo / WORK).write_text(changed)
    assert approval_findings(repo) == []


def test_plan_approval_allows_the_build_to_add_review_rows(repo):
    approve.record(repo, WORK, "ada-dev", APPROVERS, plan=True, today=TODAY)
    assert "status: in-progress" in text(repo)
    (repo / WORK).write_text(text(repo).replace("## 3. Review", "## 3. Review\n\nExtra review text.\n", 1))
    assert approval_findings(repo) == []
    (repo / WORK).write_text(text(repo).replace("| Output | A file |", "| Output | Two files |"))
    assert any("approved plan has changed" in m for m in approval_findings(repo))


def test_only_listed_approvers_may_decide(repo):
    with pytest.raises(PermissionError):
        approve.record(repo, WORK, "mallory", APPROVERS, today=TODAY)
    approve.record(repo, WORK, "ada-dev", APPROVERS, today=TODAY)
    (repo / WORK).write_text(text(repo).replace("Approved by ada-dev", "Approved by mallory"))
    assert any("not listed in approvers" in m for m in approval_findings(repo))


def test_request_changes_records_the_text_and_reopens_the_work(repo):
    row = approve.record(repo, WORK, "ada-dev", APPROVERS, changes="split the file", today=TODAY)
    assert "Changes requested" in row and "split the file" in row
    assert "status: in-progress" in text(repo)


def test_late_reviews_are_marked_reviewed_before_hashing(repo):
    marked = text(repo).replace("| None | Accepted |", "| None | Fixed after the final round. Owner decides at the review point |")
    (repo / WORK).write_text(marked)
    approve.record(repo, WORK, "ada-dev", APPROVERS, today=TODAY)
    assert f"Owner reviewed {TODAY}" in text(repo) and approval_findings(repo) == []


def test_a_complete_file_needs_a_hash_after_p1_05_but_legacy_rows_pass(repo):
    original = text(repo)

    def with_row(date):
        body = original.replace("status: awaiting-approval", "status: complete")
        return body.replace("## 4. Decision\n\nPending.", "## 4. Decision\n\n| Item | Decision | Date | Basis |\n"
                            f"|---|---|---|---|\n| Result | Approved | {date} | Owner in chat |")
    (repo / WORK).write_text(with_row("2026-11-19"))
    assert approval_findings(repo) == []
    (repo / WORK).write_text(with_row("2026-11-21"))
    assert any("has no hash" in m for m in approval_findings(repo))
    (repo / WORK).write_text(original)


def test_cli_refuses_approve_inside_an_assistant_session(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("KANON_PROFILE", json.dumps({"github": "ada-dev"}))
    assert main(["approve", "example"]) == 2
    assert main(["request-changes", "example", "x"]) == 2
    assert "refused inside an assistant session" in capsys.readouterr().out
    assert "kanon approve" not in text(repo) and "Changes requested" not in text(repo)
    assert main(["transcribe", "example", "--quote", "approve example"]) == 0
    assert "Transcribed by the assistant for ada-dev" in text(repo)


def test_cli_approve_outside_an_assistant(repo, monkeypatch):
    monkeypatch.chdir(repo)
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setenv("KANON_PROFILE", json.dumps({"github": "ada-dev"}))
    assert main(["approve", "example", "--plan"]) == 0
    assert "Approved by ada-dev with kanon approve" in text(repo)


def test_sync_writes_deny_rules_for_self_approval_and_owner_settings(repo):
    ksync.sync(repo)
    deny = json.loads((repo / ksync.SETTINGS_LOCAL).read_text())["permissions"]["deny"]
    for rule in ("Bash(kanon approve:*)", "Bash(uv run kanon approve:*)", "Bash(kanon request-changes:*)",
                 "Edit(kanon/kanon.toml)", "Write(kanon/kanon.toml)", "Bash(python3 -m kanon.cli approve:*)",
                 "Edit(.claude/settings.local.json)", "Write(.claude/settings.local.json)"):
        assert rule in deny
    assert "Bash(kanon transcribe:*)" not in deny
    ksync.sync(repo)
    assert json.loads((repo / ksync.SETTINGS_LOCAL).read_text())["permissions"]["deny"] == deny
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout
    assert "settings.local.json" not in status


ITEMS = """
### 1.3 Work Items

| ID | Item | Delivers |
|---|---|---|
| P1-05 | Approvals | Hashes |
| P1-08 | End-to-end | Runs |

### 1.6 P1-05 Design

| Part | Design |
|---|---|
| Material | Hashed |
"""


def item_repo(repo):
    body = text(repo).replace("| Reviewer | Kritos (independent) |", "| Reviewer | Kritos (independent) |\n" + ITEMS)
    body = body.replace("| 1 | Example | Kritos | pass | None | Accepted |",
                        "| C1 | P1-05 | Kritos | correct | K-1 | Fixed |").replace("status: awaiting-approval", "status: in-progress")
    (repo / WORK).write_text(body)
    return repo


def test_an_item_approval_keeps_the_status_and_ignores_later_items(repo):  # K-340
    item_repo(repo)
    row = approve.record(repo, WORK, "ada-dev", APPROVERS, item="P1-05", quote="group C approved", today=TODAY)
    assert row.startswith("| P1-05 | Approved |") and "material: item P1-05" in row
    assert "status: in-progress" in text(repo) and "> **Decision needed:** None yet." in text(repo)
    later = text(repo).replace("| C1 | P1-05 | Kritos | correct | K-1 | Fixed |",
                               "| C1 | P1-05 | Kritos | correct | K-1 | Fixed |\n| G1 | P1-08 | Kritos | pass | None | Fine |")
    (repo / WORK).write_text(later.replace("| P1-08 | End-to-end | Runs |", "| P1-08 | End-to-end | Two runs |"))
    assert approval_findings(repo) == []
    (repo / WORK).write_text(text(repo).replace("| Material | Hashed |", "| Material | Unhashed |"))
    assert any("approved item P1-05 has changed" in m for m in approval_findings(repo))


def test_an_unknown_item_is_refused(repo):
    with pytest.raises(ValueError):
        approve.record(repo, WORK, "ada-dev", APPROVERS, item="P9-99", today=TODAY)


@pytest.mark.parametrize("quote", ["Yes, approved for now", "Approved by me | ship it", "Approved for P1-05"])
def test_the_approver_is_never_read_from_the_quoted_words(repo, quote):  # K-342
    approve.record(repo, WORK, "ada-dev", APPROVERS, quote=quote, today=TODAY)
    assert approve.decision_rows(text(repo))[-1].approver == "ada-dev"
    assert approval_findings(repo) == []


def test_a_damaged_hash_fails_instead_of_being_skipped(repo):  # K-346
    approve.record(repo, WORK, "ada-dev", APPROVERS, plan=True, today=TODAY)
    damaged = approve.HASH.sub("sha256:deadbeef", text(repo))
    (repo / WORK).write_text(damaged)
    assert any("missing or malformed hash" in m for m in approval_findings(repo))


def test_a_prose_decision_section_gets_a_table_after_it(repo):  # K-348
    body = text(repo).replace("## 4. Decision\n\nPending.", "## 4. Decision\n\nThe owner approved this in chat.")
    (repo / WORK).write_text(body)
    approve.record(repo, WORK, "ada-dev", APPROVERS, today=TODAY)
    assert "The owner approved this in chat.\n\n| Item | Decision | Date | Basis |" in text(repo)


def test_a_fenced_heading_does_not_end_the_material(repo):  # K-349
    fenced = text(repo).replace("| Output | A file |", "| Output | A file |\n\n```\n## 4. Decision\n```\n")
    (repo / WORK).write_text(fenced)
    approve.record(repo, WORK, "ada-dev", APPROVERS, plan=True, today=TODAY)
    assert approve.decision_rows(text(repo))[-1].item == "Plan"
    (repo / WORK).write_text(text(repo).replace("| Creator | Builder |", "| Creator | Someone |"))
    assert any("approved plan has changed" in m for m in approval_findings(repo))


def test_uncommitted_material_is_marked(repo):  # K-350
    row = approve.record(repo, WORK, "ada-dev", APPROVERS, today=TODAY)
    assert "plus uncommitted changes" in row
