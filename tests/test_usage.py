import datetime as dt
import json
import os
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
    (tmp_path / "s.jsonl").write_text(json.dumps(entry) + "\n", encoding="utf-8")
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
    if os.name == "nt":
        repo, expected = Path("C:/Users/Ada Dev/Mercatus"), "C--Users-Ada-Dev-Mercatus"
    else:
        repo, expected = Path("/home/user/Mercatus"), "-home-user-Mercatus"
    assert usage.default_log_dir(repo) == tmp_path / "projects" / expected


def test_record_appends_rows_to_the_cost_section(tmp_path):
    work = tmp_path / "work.md"
    work.write_text(render("work.md", date="2026-11-16", title="T", summary="S."), encoding="utf-8")
    rep = usage.report(LOGS)
    usage.record(rep, work, "Step A")
    usage.record(rep, work, "Step B")
    text = work.read_text(encoding="utf-8")
    cost = text[text.index("## 5. Cost"):]
    assert cost.count(usage.COST_HEADER) == 1
    assert "| Step A | 3,552 | 700 | 13,037 | 1,492,401 | incomplete: $20.11 so far |" in cost
    assert cost.index("Step A") < cost.index("Step B")


def test_record_refuses_a_file_without_cost_section(tmp_path):
    work = tmp_path / "x.md"
    work.write_text("# No cost\n", encoding="utf-8")
    with pytest.raises(ValueError):
        usage.record(usage.report(LOGS), work, "A")


def test_cli_prints_json(capsys):
    assert main(["usage", "--logs", str(LOGS), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["main"]["output_tokens"] == MAIN["output_tokens"]
    assert data["estimated_cost_usd"] == 20.11


def test_cli_rejects_bad_time(capsys):
    assert main(["usage", "--logs", str(LOGS), "--since", "nonsense"]) == 2


def write_log(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")


def reply(mid, when, out, session="s"):
    return {"type": "assistant", "timestamp": when, "sessionId": session,
            "message": {"id": mid, "usage": {"output_tokens": out}}}


def cost(total, session="s", unknown=False):
    return {"type": "cost-state", "sessionId": session, "totalCostUSD": total, "hasUnknownModelCost": unknown}


def mark(when, session="s"):
    return {"type": "user", "timestamp": when, "sessionId": session}


def test_cost_is_summed_per_session(tmp_path):
    write_log(tmp_path / "a.jsonl", [mark("2026-01-01T09:00:00Z", "a"), cost(1, "a"),
                                     reply("a1", "2026-01-01T09:30:00Z", 10, "a"),
                                     mark("2026-01-01T10:00:00Z", "a"), cost(10, "a")])
    write_log(tmp_path / "b.jsonl", [mark("2026-01-01T11:00:00Z", "b"), cost(1, "b"),
                                     reply("b1", "2026-01-01T11:30:00Z", 10, "b"),
                                     mark("2026-01-01T12:00:00Z", "b"), cost(3, "b")])
    assert usage.report(tmp_path).cost_usd == 13.0
    assert usage.report(tmp_path, t("2026-01-01T11:00:00Z")).cost_usd == 2.0


def test_replies_after_the_last_estimate_make_the_cost_incomplete(tmp_path):
    write_log(tmp_path / "s.jsonl", [mark("2026-01-01T09:00:00Z"), cost(1),
                                     reply("r1", "2026-01-01T09:30:00Z", 9999)])
    rep = usage.report(tmp_path, t("2026-01-01T09:10:00Z"))
    assert rep.cost_bound == "incomplete"
    assert usage.cost_text(rep).startswith("incomplete")
    assert "at most" not in usage.format_report(rep)


def test_unknown_model_pricing_makes_cost_unavailable(tmp_path):
    write_log(tmp_path / "s.jsonl", [mark("2026-01-01T09:00:00Z"), cost(1),
                                     reply("r1", "2026-01-01T09:30:00Z", 5),
                                     mark("2026-01-01T10:00:00Z"), cost(2, unknown=True)])
    rep = usage.report(tmp_path)
    assert rep.cost_usd is None and "unavailable" in usage.format_report(rep)


def test_a_reply_straddling_a_boundary_counts_in_one_window_only(tmp_path):
    write_log(tmp_path / "s.jsonl", [reply("r1", "2026-01-01T10:00:05Z", 7), reply("r1", "2026-01-01T10:00:15Z", 7)])
    first = usage.report(tmp_path, t("2026-01-01T10:00:00Z"), t("2026-01-01T10:00:10Z"))
    second = usage.report(tmp_path, t("2026-01-01T10:00:10Z"), t("2026-01-01T10:00:20Z"))
    assert (first.main.replies, second.main.replies) == (1, 0)


def test_synthetic_entries_are_not_replies(tmp_path):
    synthetic = reply("x", "2026-01-01T10:00:00Z", 0)
    synthetic["message"]["model"] = "<synthetic>"
    write_log(tmp_path / "s.jsonl", [synthetic, reply("r1", "2026-01-01T10:00:01Z", 3)])
    assert usage.report(tmp_path).main.replies == 1


def test_option_like_values_never_reach_git(tmp_path):
    with pytest.raises(ValueError):
        usage.parse_time(f"--output={tmp_path}/injected.txt", Path(__file__).resolve().parents[1])
    assert not (tmp_path / "injected.txt").exists()


def test_record_keeps_crlf_line_endings(tmp_path):
    work = tmp_path / "w.md"
    body = render("work.md", date="2026-11-16", title="T", summary="S.")
    work.write_bytes(body.replace("\n", "\r\n").encode())
    usage.record(usage.report(LOGS), work, "A")
    text = work.read_bytes().decode()
    assert "| A |" in text
    assert "\n" not in text.replace("\r\n", "")


def test_record_places_rows_inside_the_table_before_trailing_text(tmp_path):
    work = tmp_path / "w.md"
    work.write_text(render("work.md", date="2026-11-16", title="T", summary="S."), encoding="utf-8")
    rep = usage.report(LOGS)
    usage.record(rep, work, "A")
    work.write_text(work.read_text(encoding="utf-8").rstrip("\n") + "\nNote: trailing.\n", encoding="utf-8")
    usage.record(rep, work, "B")
    lines = work.read_text(encoding="utf-8").splitlines()
    row_b = next(n for n, l in enumerate(lines) if l.startswith("| B"))
    assert lines[row_b - 1].startswith("| A") and row_b < lines.index("Note: trailing.")


def test_a_session_after_the_window_adds_no_cost(tmp_path):
    write_log(tmp_path / "a.jsonl", [mark("2026-01-01T09:00:00Z", "a"), cost(1, "a"),
                                     reply("a1", "2026-01-01T09:30:00Z", 5, "a"),
                                     mark("2026-01-01T09:45:00Z", "a"), cost(2, "a")])
    write_log(tmp_path / "b.jsonl", [mark("2026-01-02T09:00:00Z", "b"), cost(50, "b")])
    rep = usage.report(tmp_path, t("2026-01-01T08:00:00Z"), t("2026-01-01T10:00:00Z"))
    assert rep.cost_usd == 2.0
    assert usage.report(tmp_path, t("2025-12-31T00:00:00Z"), t("2025-12-31T01:00:00Z")).cost_usd == 0.0


def test_a_falling_running_total_makes_cost_unavailable(tmp_path):
    write_log(tmp_path / "s.jsonl", [mark("2026-01-01T09:00:00Z"), cost(5),
                                     reply("r1", "2026-01-01T09:30:00Z", 5),
                                     mark("2026-01-01T10:00:00Z"), cost(1)])
    rep = usage.report(tmp_path, t("2026-01-01T09:10:00Z"))
    assert rep.cost_usd is None and any("went down" in n for n in rep.notes)


def test_subagent_without_session_id_belongs_to_its_parent_session(tmp_path):
    write_log(tmp_path / "s.jsonl", [mark("2026-01-01T09:00:00Z"), cost(1)])
    sub = reply("x1", "2026-01-01T09:30:00Z", 5)
    del sub["sessionId"]
    write_log(tmp_path / "s" / "subagents" / "agent-1.jsonl", [sub])
    rep = usage.report(tmp_path, t("2026-01-01T08:00:00Z"))
    assert rep.cost_bound == "incomplete"


def test_cli_usage_resolves_git_refs_from_a_subdirectory(monkeypatch, capsys):
    monkeypatch.chdir(Path(__file__).resolve().parent)
    assert main(["usage", "--logs", str(LOGS), "--since", "HEAD"]) == 0
