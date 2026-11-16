"""Token usage and cost for a time window, read from Claude Code session logs (P1-07).

Claude Code writes one JSON line per content block, so a single reply can appear several
times with the same message id and the same usage. Replies are counted once per id.
Cost comes only from Claude Code's own cumulative estimate (`cost-state` records); Kanon
keeps no price list of its own. Anything the reader does not recognise is reported as
unknown rather than as zero.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

TOKEN_FIELDS = ("output_tokens", "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


@dataclass
class Totals:
    replies: int = 0
    tokens: dict[str, int] = field(default_factory=lambda: dict.fromkeys(TOKEN_FIELDS, 0))

    def add(self, usage: dict) -> None:
        self.replies += 1
        for key in TOKEN_FIELDS:
            self.tokens[key] += int(usage.get(key) or 0)


@dataclass
class UsageReport:
    since: dt.datetime | None
    until: dt.datetime | None
    main: Totals
    subagents: Totals
    cost_usd: float | None
    status: str  # "ok", "empty" or "unknown"
    notes: list[str]

    def as_dict(self) -> dict:
        return {
            "since": self.since.isoformat() if self.since else None,
            "until": self.until.isoformat() if self.until else None,
            "status": self.status,
            "main": {"replies": self.main.replies, **self.main.tokens},
            "subagents": {"replies": self.subagents.replies, **self.subagents.tokens},
            "estimated_cost_usd": self.cost_usd,
            "notes": self.notes,
        }


def default_log_dir(repo: Path) -> Path:
    """Claude Code stores logs per project, named after the path with separators replaced."""
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    return base / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(repo.resolve()))


def parse_time(value: str, repo: Path | None = None) -> dt.datetime:
    """Accept an ISO 8601 timestamp or a git reference (its commit time)."""
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", value],
            cwd=repo, capture_output=True, text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise ValueError(f"'{value}' is neither an ISO timestamp nor a git reference") from None
        parsed = dt.datetime.fromisoformat(result.stdout.strip())
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def _entries(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue  # a line still being written, or a corrupt line
            if isinstance(entry, dict):
                yield entry


def _in_window(stamp: dt.datetime, since, until) -> bool:
    return (since is None or stamp >= since) and (until is None or stamp < until)


def _collect(files: list[Path], since, until) -> tuple[Totals, int]:
    """Return totals and the number of assistant entries whose usage was unreadable."""
    replies: dict[str, dict] = {}
    unreadable = 0
    for path in files:
        for entry in _entries(path):
            message = entry.get("message")
            if entry.get("type") != "assistant" or not isinstance(message, dict):
                continue
            usage, message_id, stamp = message.get("usage"), message.get("id"), entry.get("timestamp")
            if not (isinstance(usage, dict) and isinstance(usage.get("output_tokens"), int)
                    and isinstance(message_id, str) and isinstance(stamp, str)):
                unreadable += 1
                continue
            try:
                when = parse_time(stamp)
            except ValueError:
                unreadable += 1
                continue
            if _in_window(when, since, until):
                replies[message_id] = usage
    totals = Totals()
    for usage in replies.values():
        totals.add(usage)
    return totals, unreadable


def _cost_delta(main_files: list[Path], since, until, notes: list[str]) -> float | None:
    """Difference in Claude Code's cumulative cost estimate across the window."""
    points: list[tuple[dt.datetime, float]] = []
    for path in main_files:
        last_seen: dt.datetime | None = None
        for entry in _entries(path):
            if isinstance(entry.get("timestamp"), str):
                try:
                    last_seen = parse_time(entry["timestamp"])
                except ValueError:
                    pass
            if entry.get("type") == "cost-state" and isinstance(entry.get("totalCostUSD"), (int, float)):
                if last_seen is not None:
                    points.append((last_seen, float(entry["totalCostUSD"])))
    if not points:
        return None
    points.sort()

    def at_or_before(moment):
        before = [p for p in points if p[0] <= moment]
        return before[-1] if before else None

    def at_or_after(moment):
        after = [p for p in points if p[0] >= moment]
        return after[0] if after else points[-1]

    # Widen the window to the nearest estimate records so the figure is an upper bound.
    start = None if since is None else at_or_before(since)
    end = points[-1] if until is None else at_or_after(until)
    start_cost = start[1] if start else 0.0
    end_cost = end[1] if end else 0.0
    first = start[0].strftime("%Y-%m-%d %H:%M") if start else "session start"
    last = end[0].strftime("%Y-%m-%d %H:%M") if end else "session start"
    notes.append(f"cost measured between estimate records at {first} and {last} (UTC); "
                 "Claude Code updates its estimate about once per turn, so this is an upper bound")
    return round(end_cost - start_cost, 2)


def report(log_dir: Path, since=None, until=None) -> UsageReport:
    notes: list[str] = []
    if not log_dir.is_dir():
        return UsageReport(since, until, Totals(), Totals(), None, "unknown",
                           [f"no Claude Code logs found at {log_dir}"])
    main_files = sorted(log_dir.glob("*.jsonl"))
    sub_files = sorted(log_dir.glob("*/subagents/*.jsonl"))
    main, bad_main = _collect(main_files, since, until)
    subs, bad_subs = _collect(sub_files, since, until)
    cost = _cost_delta(main_files, since, until, notes)
    if cost is None:
        notes.append("no cost estimate found in the logs")

    if bad_main + bad_subs and main.replies + subs.replies == 0:
        return UsageReport(since, until, main, subs, None, "unknown",
                           notes + [f"{bad_main + bad_subs} assistant entries in an unrecognised format"])
    if bad_main + bad_subs:
        notes.append(f"{bad_main + bad_subs} assistant entries skipped: unrecognised format")
    status = "ok" if main.replies + subs.replies else "empty"
    if status == "empty":
        notes.append("no replies in this window")
    return UsageReport(since, until, main, subs, cost, status, notes)


def format_report(rep: UsageReport) -> str:
    if rep.status == "unknown":
        return "Usage: unknown\n" + "\n".join(f"  - {n}" for n in rep.notes)
    rows = [("", "Main session", "Subagents")]
    for label, key in (("Output tokens", "output_tokens"), ("Cache writes", "cache_creation_input_tokens"),
                       ("Cache reads", "cache_read_input_tokens"), ("Uncached input", "input_tokens")):
        rows.append((label, f"{rep.main.tokens[key]:,}", f"{rep.subagents.tokens[key]:,}"))
    rows.append(("Replies", str(rep.main.replies), str(rep.subagents.replies)))
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    lines = ["  ".join(c.ljust(widths[i]) if i == 0 else c.rjust(widths[i]) for i, c in enumerate(r)) for r in rows]
    cost = "unavailable" if rep.cost_usd is None else f"at most ${rep.cost_usd:.2f} (Claude Code estimate, API-equivalent)"
    lines.append(f"Estimated cost: {cost}")
    lines.extend(f"Note: {n}" for n in rep.notes)
    return "\n".join(lines)


COST_HEADER = "| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |"


def record(rep: UsageReport, work_file: Path, label: str) -> None:
    """Append a row for this window to the Cost section of a work file."""
    text = work_file.read_text(encoding="utf-8")
    match = re.search(r"^## (?:\d+\.\s+)?Cost\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"{work_file} has no Cost section")
    if rep.status == "unknown":
        cells = [label, "unknown", "unknown", "unknown", "unknown", "unknown"]
    else:
        writes = rep.main.tokens["cache_creation_input_tokens"] + rep.subagents.tokens["cache_creation_input_tokens"]
        reads = rep.main.tokens["cache_read_input_tokens"] + rep.subagents.tokens["cache_read_input_tokens"]
        cost = "unavailable" if rep.cost_usd is None else f"at most ${rep.cost_usd:.2f}"
        cells = [label, f"{rep.main.tokens['output_tokens']:,}", f"{rep.subagents.tokens['output_tokens']:,}",
                 f"{writes:,}", f"{reads:,}", cost]
    row = "| " + " | ".join(cells) + " |"
    section_end = re.search(r"^## ", text[match.end():], re.MULTILINE)
    end = match.end() + section_end.start() if section_end else len(text)
    section = text[match.end():end]
    if COST_HEADER in section:
        table_at = match.end() + section.index(COST_HEADER)
        table_end = text.find("\n\n", table_at)
        table_end = end if table_end == -1 or table_end > end else table_end
        new = text[:table_end].rstrip("\n") + "\n" + row + text[table_end:]
    else:
        block = f"\n{COST_HEADER}\n|---|---|---|---|---|---|\n{row}\n"
        new = text[:end].rstrip("\n") + "\n" + block + ("\n" + text[end:] if end < len(text) else "")
    work_file.write_text(new, encoding="utf-8")
