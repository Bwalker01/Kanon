"""`kanon status` (KS-1, kanon/work/2026-11-24-kanon-status.md)."""

import json
import re
from pathlib import Path

import pytest

from kanon import desk, github
from kanon.cli import main
from kanon.verify import check_document
from test_desk import ACTIONS, commit, repo, work_file  # noqa: F401  (repo is a fixture)

REVIEW = ("| Round | Items | Reviewer | Verdict | Blocking | Outcome |\n|---|---|---|---|---|---|\n"
          "| 2 | Fixes | Kritos | correct | K-1 | Fixed after the final round. Owner decides at the review point |")


def late(text):
    return text.replace("Not yet reviewed.", REVIEW)


@pytest.fixture
def project(repo):
    work = repo / "kanon/work"
    (work / "2026-11-18-open.md").write_text(late(work_file("Open", ACTIONS)), encoding="utf-8")
    (work / "2026-11-18-waiting.md").write_text(
        work_file("Waiting", status="awaiting-approval", needed="Approve the plan."), encoding="utf-8")
    (work / "2026-11-18-done.md").write_text(late(work_file("Done", ACTIONS, status="complete")), encoding="utf-8")
    (work / "2026-11-18-parked.md").write_text(work_file("Parked", status="parked"), encoding="utf-8")
    (work / "2026-11-18-quiet.md").write_text(work_file("Quiet", status="complete"), encoding="utf-8")
    commit(repo, "work")
    return repo


def run(capsys, *args):
    code = main(["status", *args])
    return code, capsys.readouterr().out


def blocks(out):
    """Open work blocks before 'From closed work', keyed by path."""
    head = out.split("From closed work")[0]
    return re.findall(r"^    (kanon/work/\S+)$", head, re.M)


def test_every_open_work_file_appears_once_and_closed_work_has_no_block(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    code, out = run(capsys)
    assert code == 0
    assert blocks(out) == ["kanon/work/2026-11-18-open.md", "kanon/work/2026-11-18-waiting.md"]
    assert "Done (complete)" not in out and "Parked" not in out and "quiet" not in out


def test_decisions_actions_with_assignees_and_late_reviews_are_shown(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    _, out = run(capsys)
    opened = out.split("Waiting (awaiting-approval)")[0]
    assert "Action A-1 (ada-dev): Merge the branch" in opened and "Action A-3 (bo-dev): Bo's job" in opened
    assert "A-4" not in out  # done actions are not shown
    assert "Late review, round 2" in opened
    assert "Decision: Approve the plan." in out.split("Waiting (awaiting-approval)")[1].split("From closed work")[0]


def test_open_items_in_closed_work_are_listed_under_from_closed_work(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    _, out = run(capsys)
    closed = out.split("From closed work")[1]
    assert re.findall(r"^  (kanon/work/\S+)$", closed, re.M) == ["kanon/work/2026-11-18-done.md"]
    assert "Action A-1 (ada-dev)" in closed and "Late review, round 2" in closed


def test_a_profile_that_is_neither_assignee_nor_approver_still_sees_everything(project, capsys, monkeypatch):
    monkeypatch.setenv("KANON_PROFILE", json.dumps({"github": "outsider"}))
    monkeypatch.chdir(project)
    assert desk.build(project).decisions == [] and desk.build(project).actions == []  # the Desk filters
    _, out = run(capsys, "--json")
    data = json.loads(out)
    opened = {w["path"]: w for w in data["work"]}
    assert opened["kanon/work/2026-11-18-waiting.md"]["decisions"] == ["Approve the plan."]
    assert sorted(a["id"] for a in opened["kanon/work/2026-11-18-open.md"]["actions"]) == ["A-1", "A-2", "A-3"]
    assert opened["kanon/work/2026-11-18-open.md"]["late_reviews"][0]["round"] == "2"
    assert data["closed_work"][0]["path"] == "kanon/work/2026-11-18-done.md"
    assert not any("showing every person's items" in n for n in data["notes"])


def test_work_listed_equals_the_status_page_work_in_progress(project):
    built = desk.build(project, everyone=True)
    page = desk.render_status(built)
    listed = re.findall(r"`(kanon/work/[^`]+)`$", page, re.M)
    assert listed == blocks(desk.render_terminal(built))


def test_no_network_call_is_made(project, capsys, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network call")
    monkeypatch.setattr(github, "sign_in", refuse)
    monkeypatch.setattr(github, "call", refuse)
    monkeypatch.chdir(project)
    assert run(capsys)[0] == 0 and run(capsys, "--json")[0] == 0


def test_json_holds_the_same_content_as_the_text(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    _, text = run(capsys)
    _, raw = run(capsys, "--json")
    data = json.loads(raw)
    assert [w["path"] for w in data["work"]] == blocks(text)
    for entry in [*data["work"], *data["closed_work"]]:
        for d in entry["decisions"]:
            assert f"Decision: {d}" in text
        for a in entry["actions"]:
            assert f"Action {a['id']} ({a['assignee']}): {a['title']}" in text
        for r in entry["late_reviews"]:
            assert f"Late review, round {r['round']}" in text
    assert [c["path"] for c in data["closed_work"]] == re.findall(r"^  (kanon/work/\S+)$", text, re.M)


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, p.read_bytes())
            for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}


def test_no_file_is_written_or_changed(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    before = snapshot(project)
    run(capsys)
    run(capsys, "--json")
    assert snapshot(project) == before  # includes kanon/local/, which kanon init already filled


def test_runs_from_a_subdirectory(project, capsys, monkeypatch):
    monkeypatch.chdir(project / "kanon/work")
    code, out = run(capsys)
    assert code == 0 and "kanon/work/2026-11-18-open.md" in out


def test_missing_settings_exit_2_with_a_message(project, capsys, monkeypatch):
    (project / "kanon/kanon.toml").unlink()
    monkeypatch.chdir(project)
    code, out = run(capsys)
    assert code == 2 and "kanon init" in out


def test_no_open_work_prints_no_open_work(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    code, out = run(capsys)
    assert code == 0 and "No open work." in out


WORK_FILE = Path(__file__).resolve().parents[1] / "kanon/work/2026-11-24-kanon-status.md"


@pytest.mark.parametrize("section", ["Plan", "Questions", "Review", "Decision", "Cost"])
def test_removing_a_section_of_this_work_file_fails_verify(section):
    text = WORK_FILE.read_text(encoding="utf-8")
    rel = "kanon/work/2026-11-24-kanon-status.md"
    assert not [f for f in check_document(rel, text) if f.rule == "sections"]
    cut = re.sub(rf"^## \d+\. {section}\n.*?(?=^## |\Z)", "", text, count=1, flags=re.M | re.S)
    assert cut != text
    assert any(f.rule == "sections" and f"'{section}'" in f.message for f in check_document(rel, cut))
