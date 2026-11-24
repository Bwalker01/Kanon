---
type: work
status: awaiting-approval
updated: 2026-11-24
---

# Kanon Questions

> **Summary:** P1-08, second requirement: a read-only `kanon questions` command that lists the questions
> recorded in work files, unanswered ones first, built after `kanon status` and compared with it.
> **Decision needed:** Review and merge the App's pull request for `kanon/kanon-questions/plan`, after the `kanon status` one; the merge is the approval. KQ-1 passed Kritos in round R1.

## 1. Plan

| Field | Value |
|---|---|
| Output | `kanon questions` in `src/kanon/cli.py`, a question parser in `src/kanon/desk.py`, `tests/test_questions.py`, a README line |
| Inputs | P1-08 in `kanon/work/2026-11-16-phase-1-plan.md`; conduct standard section 1 ("Ask early", "Clear questions"); the Questions table in the work file template; `kanon status` (`kanon/work/2026-11-24-kanon-status.md`) |
| Acceptance | See 1.2 |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### 1.1 Design

| Part | Choice |
|---|---|
| Purpose | One place to see what has been asked and what is still open, so questions are answered early (conduct standard, section 1). |
| Source | The Questions table of every work file: columns Date, Question, Answer, the header every current work file uses. Rows inside code fences are ignored. A question recorded in several files is listed once per file, since each file holds its own record. |
| Unanswered | An Answer cell that is empty or `-`, or whose first word is `open`, `pending` or `awaiting` (case-insensitive, whole words, after markup is stripped, so "Opened" is answered). Every other answer counts as answered. |
| Output | Unanswered questions first, oldest first: date, work file, question. Then, with `--all`, answered questions newest first with their answers. A count line (`<open> open, <answered> answered`) always ends the output, after "No open questions." when none is open. |
| Dates | Sorted by the first `YYYY-MM-DD` in the cell ("2026-11-13 to 15" sorts as 2026-11-13), then by file and row order; a cell with no such date sorts last and is shown as written. |
| Options | `--all` as above; `--work <name>` limits to one work file; `--json` for scripts. |
| Exit code | 0 in every case, including open questions. `verify` is unchanged. |
| Writes | None. |
| Base | This plan is committed on its own on `claude/phase-1-close` with the `kanon status` plan. `kanon/kanon-questions/plan` is created from `main` after the `kanon status` pull request merges, so it starts from that code and carries only this work. |
| Branches | One item, `KQ-1` (section 1.3), on `kanon/kanon-questions/KQ-1`, merged into `kanon/kanon-questions/plan`. |
| Sequence | 0. Once both P1-08 plans pass Kritos and await approval, and every other piece of work on the branch has passed review or been decided by the owner, `claude/phase-1-close` is pushed and the owner opens and merges its pull request. That merge does not approve the P1-08 plans; they stay `awaiting-approval` on `main` until step 2. 1. Kritos passes the plan. 2. The owner approves the plan (`kanon approve kanon-questions --plan` or a transcribed reply); the assistant creates `kanon/kanon-questions/plan` from the `main` commit that merged the `kanon status` pull request (`git branch kanon/kanon-questions/plan <that commit>`, since `kanon branch start` branches from the current commit), and the approval row is its first commit. 3. `kanon branch start kanon-questions KQ-1`; build and commit on the item branch. 4. Kritos reviews the result; findings and rounds recorded in section 3. 5. `kanon branch merge kanon-questions KQ-1`. 6. `kanon verify` and the Cost row; status set to `awaiting-approval` with a "Decision needed" line (rule 5), since `kanon github pr` sets it only when no item was merged. 7. `kanon github pr kanon-questions` opens a draft as the App and writes the "approved when pull request #N merges" row itself. 8. `kanon github notes kanon-questions <notes file>` posts Kritos's findings as a comment review (P1-10); the notes file is written in the session's scratchpad, outside the repository. 9. `kanon github ready kanon-questions`; CI runs (ADR-015). 10. The owner merges; the merge is the approval. 11. Clio sets the status to `complete` on `main`. After step 0, nothing is pushed before step 7. |
| Prerequisite | As for `kanon status`: `kanon verify` should skip git-ignored folders under `.claude`; it passes now that the stale worktree is removed. |

### 1.2 Acceptance

| Check | Confirmed by |
|---|---|
| Every Questions row in every work file is found once; rows in code fences are not | Test on a fixture repository |
| Empty and `-` answers, and answers whose first word is `open`, `pending` or `awaiting`, are unanswered; "Opened" and any other text are answered | Tests, one per form |
| On this repository the open rows equal those that fit the rule at build time (as of 2026-11-24, after the owner answered Q-1 and Q-2 of `2026-11-23-remote-session-limits.md`: 1, the open row in `2026-11-22-windows-test-portability.md`) | Command output and an independent count recorded in section 3 |
| Order: unanswered oldest first; with `--all`, answered newest first | Test |
| `--work` limits to one file; an unknown name exits 2 with a message | Tests |
| `--json` holds the same rows as the text output | Test |
| No file is written or changed | Test |
| On this repository the total equals the row count from `awk '/^## [0-9.]* *Questions/{q=1;next} /^## /{q=0} q && /^\| / && !/^\| Date/ && !/^\|---/' kanon/work/*.md \| wc -l` | Both outputs recorded in section 3 |
| `uv run pytest -q` and `uv run kanon verify` pass | Command output |
| The work file holds every section in schema order, and the plan was committed on its own before the build (`verify`'s loop rule) | `kanon verify` on this repository |
| Removing any one section from a copy of this file fails `check_document` naming the section | Test, one case per section |
| Section 1.4 compares rounds, questions asked, owner actions and tokens with `kanon status` section 1.4 | Owner reads section 1.4 at the final review |
| Kritos passes the plan and the result | Section 3 |

### 1.3 Work Items

| ID | Item | Delivers |
|---|---|---|
| KQ-1 | `kanon questions` | Command, question parser, tests, README line |

### 1.4 Comparison with the First Run

Recorded at the end, against `kanon/work/2026-11-24-kanon-status.md` section 1.4: review rounds,
questions asked, owner actions raised and tokens. Tokens: `kanon usage --since <merge of the
status pull request> --until <merge of this work's pull request>`; the shared plan review
is counted in `kanon status` only. Other work in the same sessions within the window is listed beside the
figures (assessment: `kanon usage` counts every session in the log folder). Differences are stated with
their likely cause, as an assessment.

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-24 | Plan `kanon status` first and `kanon questions` after it ships, or both now? Recommended: status first. | Both now (owner) |
| 2026-11-24 | Delivery after approval (owner in chat, quoted in full in `2026-11-24-kanon-status.md`, Questions) | The close-out branch is `kanon/phase-1-close`; the plan approval rows travel with it. Both requirements are completed now, so `kanon/kanon-questions/plan` starts from `kanon/kanon-status/plan` after KS-1 is merged into it, and its pull request carries only KQ-1 once the status pull request merges |

## 3. Actions

| ID | Action | Assignee | Blocks | Done |
|---|---|---|---|---|
| A-1 | Make the App key readable on this computer | Bwalker01 | | yes |

### A-1: App Key on This Computer

1. Do A-1 of `kanon/work/2026-11-24-kanon-status.md`; the same key serves both pull requests.
2. Tell the assistant; it runs `kanon github pr kanon-questions` after the `kanon status` pull request is open.
3. Confirm: the pull request's author is `kanon-agent[bot]` and its diff holds only KQ-1 once the `kanon status` pull request has merged.

Done 2026-11-24 with A-1 of `2026-11-24-kanon-status.md`: the key is in the git-ignored `.env`.

## 4. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| P1 | Plan, with `kanon status` | Kritos (`kritos-reviewer` agent) | correct | 1, 3 to 6 | 1: Work Items table added. 3, 4: comparison check and token windows added. 5: sequence follows ADR-015 with the plan approval. 6: contrast wording removed. Non-blocking 7 (base), 8 (section order), 12 (exact count command), 13 (dates, duplicates, count line) applied. Outside this plan: `verify` reads `.claude/worktrees/`, listed as a prerequisite. |
| P2 | Round 1 fixes (fcc3772 and the record after it) | Kritos (`kritos-reviewer` agent) | correct | Q1 | Q1: answers starting with `open`, `pending` or `awaiting` count as unanswered, with a check that this repository shows 3. Non-blocking N1, N2, N3, N4 (file count dropped), N5 applied. |
| P3 | Round 2 fixes (370166a) | Kritos (`kritos-reviewer` agent) | pass | None | Non-blocking 1 (step 0 waits for every piece of work on the branch), 2 (step 0 merge does not approve), 3 (open count dated), 4 (whole words) and 5 (who creates the plan branch) applied. |
| R1 | KQ-1 (75d5f82) | Kritos (`kritos-reviewer` agent) | pass | None | Every acceptance row met; 627 passed, 2 skipped. On this repository: `kanon questions` gives 1 open and 61 answered (62 rows), the plan's awk command gives 62, and an independent awk pass of the open rule gives the same single open row (`2026-11-22-windows-test-portability.md`). Non-blocking, recorded as limits below: 1 to 6. |

**After round P3:** the open count example in 1.2 was corrected from 3 to 1 once the owner answered Q-1 and Q-2 on 2026-11-24; the rule is unchanged.

**Known limits after R1 (non-blocking):** 1: a second table inside the Questions section would be read as questions (the awk count shares the gap). 2: of two `## Questions` headings only the last is read. 3: the first word must start the answer, so "(pending)" counts as answered and "Open-ended" as open. 4: an escaped `\|` keeps its backslash. 5: `--work` takes the name without the date. 6: ties between files on one date, and undated answered rows, have no ordering test.

## 5. Decision

| Item | Decision | Date | Basis |
|---|---|---|---|
| Plan | Approved | 2026-11-24 | Owner in chat: "I approve all of the plans.". Transcribed by the assistant for Bwalker01; commit `1694896`; material: plan; sha256:f5497c82e21263e7d14b22bfb16a58206c2a5962f7b8796b3dd8f5a3d42f0217 |

## 6. Cost

Window: `kanon usage --since c4981c5` (the last `kanon status` record, after which this build began) to the end of review round R1. The shared plan rounds are counted in `kanon status` only.

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| KQ-1 build and review round R1 | 11,531 | 9,861 | 46,231 | 4,151,146 | not yet calculated (Claude Code has not updated its estimate) |

**Comparison with the first run (plan section 1.4, recorded here because the approved plan is hashed):**

| Measure | `kanon status` | `kanon questions` |
|---|---|---|
| Review rounds | 3 plan (shared) and 3 result | 0 own plan (shared, counted in status) and 1 result |
| Questions asked | 3 | 2 |
| Owner actions raised | 1 (App key) | 1 (the same key) |
| Output tokens, main and subagents | 93,583 and 69,761 | 11,531 and 9,861 |

Assessment: the second run cost about an eighth of the first. Likely causes: the joint plan rounds and the close-out records are counted in the first run only; the first run found and fixed the Windows output and line-ending problems, which the second reused; and the second command reads one table, with no profile filters to bypass.
