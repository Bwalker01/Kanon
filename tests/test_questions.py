"""`kanon questions` (KQ-1, kanon/work/2026-11-24-kanon-questions.md)."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from kanon import desk
from kanon.cli import main
from kanon.verify import check_document
from test_desk import commit, repo, work_file  # noqa: F401  (repo is a fixture)

HEADER = "| Date | Question | Answer |\n|---|---|---|\n"


def with_questions(title, rows, extra=""):
    return work_file(title).replace(HEADER, HEADER + rows + extra)


@pytest.fixture
def project(repo):
    work = repo / "kanon/work"
    (work / "2026-11-18-alpha.md").write_text(with_questions("Alpha", (
        "| 2026-11-20 | Alpha late open? | |\n"
        "| 2026-11-16 | Alpha answered early? | Yes, chosen. |\n"
        "| 2026-11-19 | Alpha dash? | - |\n"
        "| 2026-11-17 | Alpha opened? | Opened as a draft. |\n"),
        "\n```\n| 2026-11-01 | Fenced question? | |\n```\n"), encoding="utf-8")
    (work / "2026-11-18-beta.md").write_text(with_questions("Beta", (
        "| 2026-11-13 to 15 | Beta range? | Awaiting the owner |\n"
        "| 2026-11-18 | Beta pending? | **Pending** a reply |\n"
        "| 2026-11-18 | Beta open? | Open; outside this work |\n"
        "| soon | Beta undated? | |\n"
        "| 2026-11-21 | Beta answered late? | Done |\n")), encoding="utf-8")
    (work / "2026-11-18-gamma.md").write_text(work_file("Gamma"), encoding="utf-8")  # empty table
    commit(repo, "questions")
    return repo


def run(capsys, *args):
    code = main(["questions", *args])
    return code, capsys.readouterr().out


def asked(out):
    return re.findall(r"^    (\S.*\?)$", out, re.M)


def test_every_row_is_found_once_and_fenced_rows_are_not(project):
    rows = desk.questions(project)
    assert len(rows) == 9 and len({(q.work, q.question) for q in rows}) == 9
    assert all("Fenced" not in q.question for q in rows)


@pytest.mark.parametrize("answer, is_open", [
    ("", True), ("-", True), ("open", True), ("Open; outside this work", True), ("Awaiting the owner", True),
    ("**Pending** a reply", True), ("`pending`", True), ("Opened as a draft.", False), ("OpenAI chosen", False),
    ("Yes", False), ("Not open", False), ("Done (owner)", False)])
def test_open_answer_forms(answer, is_open):
    assert desk.Question("w", "2026-11-18", "q?", answer, 1).is_open is is_open


def test_open_questions_oldest_first_and_undated_last(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    code, out = run(capsys)
    assert code == 0
    assert asked(out) == ["Beta range?", "Beta pending?", "Beta open?", "Alpha dash?", "Alpha late open?",
                          "Beta undated?"]
    assert out.rstrip().endswith("6 open, 3 answered")
    assert "Answer:" not in out


def test_all_adds_answered_newest_first(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    _, out = run(capsys, "--all")
    answered = out.split("\nAnswered\n")[1]
    assert asked(answered) == ["Beta answered late?", "Alpha opened?", "Alpha answered early?"]
    assert "Answer: Opened as a draft." in answered


def test_work_limits_to_one_file_and_unknown_exits_2(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    _, out = run(capsys, "--work", "alpha", "--all")
    assert {line.split()[1] for line in out.splitlines() if line.startswith("2026")} == {"kanon/work/2026-11-18-alpha.md"}
    code, out = run(capsys, "--work", "nope")
    assert code == 2 and "no work file named 'nope'" in out


def test_json_holds_the_same_rows_as_the_text(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    _, text = run(capsys, "--all")
    data = json.loads(run(capsys, "--all", "--json")[1])
    assert [q["question"] for q in data["open"]] + [q["question"] for q in data["answered"]] == asked(text)
    assert data["counts"] == {"open": 6, "answered": 3}
    assert json.loads(run(capsys, "--json")[1])["answered"] == []


def test_no_open_questions_still_prints_the_count(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    code, out = run(capsys)
    assert code == 0 and out == "No open questions.\n\n0 open, 0 answered\n"


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, p.read_bytes())
            for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}


def test_no_file_is_written_or_changed(project, capsys, monkeypatch):
    monkeypatch.chdir(project)
    before = snapshot(project)
    run(capsys, "--all")
    run(capsys, "--json")
    assert snapshot(project) == before


def test_missing_settings_exit_2(project, capsys, monkeypatch):
    (project / "kanon/kanon.toml").unlink()
    monkeypatch.chdir(project)
    code, out = run(capsys)
    assert code == 2 and "kanon init" in out


def test_piped_output_survives_characters_outside_the_code_page(project):
    path = project / "kanon/work/2026-11-18-beta.md"
    path.write_text(path.read_text(encoding="utf-8").replace("Beta open?", "Beta → open?"), encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    result = subprocess.run([sys.executable, "-m", "kanon", "questions"], cwd=project, env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert b"Beta ? open?" in result.stdout


ROOT = Path(__file__).resolve().parents[1]
WORK_FILE = ROOT / "kanon/work/2026-11-24-kanon-questions.md"


def test_this_repository_matches_an_independent_count():
    rows = desk.questions(ROOT)
    count = 0
    for path in sorted((ROOT / "kanon/work").glob("*.md")):  # the plan's awk command, in Python
        inside = False
        for line in path.read_text(encoding="utf-8").split("\n"):
            if re.match(r"^## [0-9.]* *Questions", line):
                inside = True
            elif line.startswith("## "):
                inside = False
            elif inside and line.startswith("| ") and not line.startswith("| Date") and not line.startswith("|---"):
                count += 1
    assert len(rows) == count


@pytest.mark.parametrize("section", ["Plan", "Questions", "Review", "Decision", "Cost"])
def test_removing_a_section_of_this_work_file_fails_verify(section):
    text = WORK_FILE.read_text(encoding="utf-8")
    rel = "kanon/work/2026-11-24-kanon-questions.md"
    assert not [f for f in check_document(rel, text) if f.rule == "sections"]
    cut = re.sub(rf"^## \d+\. {section}\n.*?(?=^## |\Z)", "", text, count=1, flags=re.M | re.S)
    assert cut != text
    assert any(f.rule == "sections" and f"'{section}'" in f.message for f in check_document(rel, cut))
