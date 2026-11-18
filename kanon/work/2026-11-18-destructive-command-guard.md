---
type: work
status: awaiting-approval
updated: 2026-11-18
---

# Destructive Command Guard

> **Summary:** Block agent commands that delete shared locations, after a reviewer's cleanup deleted `/tmp` and with it the session's commit-signing helper.
> **Decision needed:** Approve the guard hook and the deletion rule for all agents.

## 1. Plan

| Field | Value |
|---|---|
| Output | `src/kanon/guard.py`; generated `.claude/hooks/kanon-guard.py`; hook registered in `.claude/settings.local.json` by `kanon sync`; deletion rule for all agents; learning L-004 |
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

- The guard reads command text. It cannot see what variables hold, what scripts do, or deletions made
  by other programs, and it allows patterns with literal text such as `/tmp/tmp*`.
- It can block a harmless command whose text resembles a dangerous deletion (for example such text
  inside a heredoc); agents then write that text with a file editor.
- It fails open: when the hook script, the project folder variable or `python3` is missing, commands run unchecked.
- The signing helper returns only with a new container; this session's later commits are unsigned.

## 2. Questions

| Date | Question | Answer |
|---|---|---|

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| 1 | Guard, hook registration, rule | Kritos (`kritos-reviewer` agent) | correct | K-101 to K-105 | All fixed with tests; non-blocking K-106 to K-109 fixed |

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| Guard build, review round 1 and fixes | 35,219 | 29,496 | 102,292 | 22,182,324 | incomplete: $0.00 so far |
