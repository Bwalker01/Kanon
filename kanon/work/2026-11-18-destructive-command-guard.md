---
type: work
status: in-progress
updated: 2026-11-18
---

# Destructive command guard

> **Summary:** Block agent commands that delete shared locations, after a reviewer's cleanup deleted `/tmp` and with it the session's commit-signing helper.
> **Decision needed:** None yet.

## 1. Plan

| Field | Value |
|---|---|
| Output | `kanon/guard.py`; generated `.claude/hooks/kanon-guard.py`; hook registered in `.claude/settings.local.json` by `kanon sync`; deletion rule for all agents; learning L-004 |
| Inputs | Incident 2026-11-18 13:38:38 (subagent log); Claude Code hooks documentation, read 2026-11-18 |
| Acceptance | The incident command is blocked; deletions of paths the agent created pass; other settings in `settings.local.json` survive sync; hooks fire for subagents (per documentation) |
| Creator | Claude Code (builder session) |
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
