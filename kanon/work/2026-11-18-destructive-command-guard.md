---
type: work
status: awaiting-approval
updated: 2026-11-18
---

# Destructive command guard

> **Summary:** Block agent commands that delete shared locations, after a reviewer's cleanup deleted `/tmp` and with it the session's commit-signing helper.
> **Decision needed:** Approve the guard hook and the deletion rule for all agents.

## 1. Plan

| Field | Value |
|---|---|
| Output | `kanon/guard.py`; generated `.claude/hooks/kanon-guard.py`; hook registered in `.claude/settings.local.json` by `kanon sync`; deletion rule for all agents; learning L-004 |
| Inputs | Incident 2026-11-18 13:38:38 (subagent log); Claude Code hooks documentation, read 2026-11-18 |
| Acceptance | The incident command is blocked; deletions of paths the agent created pass; other settings in `settings.local.json` survive sync; hooks fire for subagents (per documentation) |
| Creator | Claude Code (builder session) |
| Reviewer | Kritos (independent) |

### 1.1 Cause

At 13:38:38 a reviewer subagent ran a cleanup loop over the results of `find /tmp -maxdepth 1 -name 'tmp*'`.
`find` returns its own starting folder, `/tmp` matched `tmp*`, and the loop deleted all of `/tmp`,
including the session's commit-signing helper `/tmp/code-sign`. Evidence: the subagent log, the
`/tmp` creation time (13:38:42) and signed commits at 13:28 and 13:34 but not after.

### 1.2 Limits

- The guard reads command text. It cannot see through variables, scripts or other programs, and it
  also blocks commands that only quote such text (for example a heredoc); agents then use a file editor.
- The signing helper returns only with a new container; this session's later commits are unsigned.

## 2. Questions

| Date | Question | Answer |
|---|---|---|

## 3. Review

Not yet reviewed.

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
