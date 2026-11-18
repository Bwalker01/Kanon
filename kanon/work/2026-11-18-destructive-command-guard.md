---
type: work
status: awaiting-approval
updated: 2026-11-18
---

# Destructive Command Guard

> **Summary:** Block agent commands that delete shared locations, after a reviewer's cleanup deleted `/tmp` and with it the session's commit-signing helper.
> **Decision needed:** Approve the round 3 fixes (94796b5), made after the approval of `be4dbe8`; no reviewer has checked them.

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
- When a loop, `$(...)` or `xargs` appears anywhere in the command, every non-reading unit is judged as
  a deletion, so a unit such as `cp "$f" .` can be blocked (K-265). The false block is accepted as the safe side.
- It fails open: when the hook script, the project folder variable or `python3` is missing, commands run unchecked.
- The signing helper returns only with a new container. Commits from 13:38 to 16:09 on 2026-11-18 are unsigned; signing was restored in a fresh session (`phase-1-plan` action A-2).

## 2. Questions

| Date | Question | Answer |
|---|---|---|

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| 1 | Guard, hook registration, rule | Kritos (`kritos-reviewer` agent) | correct | K-101 to K-105 | All fixed with tests; non-blocking K-106 to K-109 fixed |
| 2 | Round 1 fixes | Kritos (`kritos-reviewer` agent) | correct | K-110 | K-110 (git in front hid the deletion), K-111 (shell flags), K-112 (false blocks after `cd` into the project), K-113 (find start reused as a target), K-114 (`cd` and `pathlib`), K-115 (cost shown as $0.00 so far) fixed with tests; reviewed in round 3 |
| 3 | Round 2 fixes (bb29241) | Kritos (`kritos-reviewer` agent) | correct | K-260 to K-262 | K-260 (newlines not separators), K-261 (`uv run` and `make` skipped), K-262 (git stage in a pipeline hid the deletion), K-263 to K-268 fixed with tests after the final round; K-265 false blocks under loops or substitution accepted as a limit. Not independently reviewed. Owner decides at the review point |

## 4. Decision

| Item | Decision | Date | Basis |
|---|---|---|---|
| Guard hook and deletion rule | Approved | 2026-11-18 | Owner in chat: "approve destructive-command-guard". Transcribed by the assistant; applies to commit `be4dbe8` |

## 5. Cost

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| Guard build, review round 1 and fixes | 35,219 | 29,496 | 102,292 | 22,182,324 | not yet calculated |
