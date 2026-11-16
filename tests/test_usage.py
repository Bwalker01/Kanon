import datetime as dt
import json
import shutil
from pathlib import Path

import pytest

from kanon import usage
from kanon.cli import main
from kanon.templates import render

LOGS = Path(__file__).parent / "fixtures" / "claude_logs"
UTC = dt.timezone.utc


def t(text):
    return usage.parse_time(text)


# Expected values computed independently with jq (unique_by message id) over the fixture.
MAIN = {"replies": 4, "output_tokens": 3552, "cache_creation_input_tokens": 8037,
        "cache_read_input_tokens": 1472401, "input_tokens": 8}
SUB = {"replies": 1, "output_tokens": 700, "cache_creation_input_tokens": 5000,
       "cache_read_input_tokens": 20000, "input_tokens": 3}
MSG_2_OUTPUT = 538


def test_totals_count_each_reply_once():
    rep = usage.report(LOGS)
    assert rep.status == "ok"
    assert {"replies": rep.main.replies, **rep.main.tokens} == MAIN
    assert {"replies": rep.subagents.replies, **rep.subagents.tokens} == SUB


def test_window_selects_replies_by_time():
    rep = usage.report(LOGS, t("2026-11-16T14:54:10Z"), t("2026-11-16T14:54:16Z"))
    assert rep.main.replies == 1
    assert rep.main.tokens["output_tokens"] == MSG_2_OUTPUT
    assert rep.subagents.replies == 0


def test_cost_is_the_change_in_claude_codes_estimate():
    assert usage.report(LOGS, t("2026-11-16T14:54:00Z")).cost_usd == 0.75
    assert usage.report(LOGS).cost_usd == 20.11


def test_cost_window_widens_to_an_upper_bound():
    # The window ends between estimate records; the next record (20.11) is used, never an earlier one.
    rep = usage.report(LOGS, t("2026-11-16T14:54:00Z"), t("2026-11-16T14:54:10Z"))
    assert rep.cost_usd == 0.75


def test_empty_window_is_zero_with_a_note():
    rep = usage.report(LOGS, t("2030-01-01T00:00:00Z"))
    assert rep.status == "empty"
    assert rep.main.tokens["output_tokens"] == 0
    assert "no replies in this window" in rep.notes


def test_unrecognised_format_is_unknown_not_zero(tmp_path):
    entry = {"type": "assistant", "timestamp": "2026-11-16T14:54:01Z",
             "message": {"id": "m1", "usage": {"outputTokens": 10}}}
    (tmp_path / "s.jsonl").write_text(json.dumps(entry) + "\n")
    rep = usage.report(tmp_path)
    assert rep.status == "unknown"
    assert "Usage: unknown" in usage.format_report(rep)


def test_missing_log_folder_is_unknown(tmp_path):
    rep = usage.report(tmp_path / "absent")
    assert rep.status == "unknown"
    assert rep.cost_usd is None


def test_parse_time_accepts_git_refs_and_rejects_nonsense():
    repo = Path(__file__).resolve().parents[1]
    assert usage.parse_time("HEAD", repo).tzinfo is not None
    with pytest.raises(ValueError):
        usage.parse_time("not-a-ref-or-date", repo)


def test_default_log_dir_follows_claude_code_naming(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert usage.default_log_dir(Path("/home/user/Mercatus")) == tmp_path / "projects" / "-home-user-Mercatus"


def test_record_appends_rows_to_the_cost_section(tmp_path):
    work = tmp_path / "work.md"
    work.write_text(render("work.md", date="2026-11-16", title="T", summary="S."))
    rep = usage.report(LOGS)
    usage.record(rep, work, "Step A")
    usage.record(rep, work, "Step B")
    text = work.read_text()
    cost = text[text.index("## 5. Cost"):]
    assert cost.count(usage.COST_HEADER) == 1
    assert "| Step A | 3,552 | 700 | 13,037 | 1,492,401 | at most $20.11 |" in cost
    assert cost.index("Step A") < cost.index("Step B")


def test_record_refuses_a_file_without_cost_section(tmp_path):
    work = tmp_path / "x.md"
    work.write_text("# No cost\n")
    with pytest.raises(ValueError):
        usage.record(usage.report(LOGS), work, "A")


def test_cli_prints_json(capsys):
    assert main(["usage", "--logs", str(LOGS), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["main"]["output_tokens"] == MAIN["output_tokens"]
    assert data["estimated_cost_usd"] == 20.11


def test_cli_rejects_bad_time(capsys):
    assert main(["usage", "--logs", str(LOGS), "--since", "nonsense"]) == 2


def test_cost_note_names_the_records_used():
    rep = usage.report(LOGS, t("2026-11-16T14:54:00Z"))
    assert any("between estimate records at 2026-11-16 14:54 and 2026-11-16 14:54" in n for n in rep.notes)
