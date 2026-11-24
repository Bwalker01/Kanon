---
type: work
status: planning
updated: 2026-11-24
---

# Kanon Questions

> **Summary:** P1-08, second requirement: a read-only `kanon questions` command that lists the questions
> recorded in work files, unanswered ones first, built after `kanon status` and compared with it.
> **Decision needed:** None yet; the plan goes to Kritos first.

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
| Source | The Questions table of every work file: columns Date, Question, Answer (all 13 current work files use this header). Rows inside code fences are ignored. A question recorded in several files is listed once per file, since each file holds its own record. |
| Unanswered | An Answer cell that is empty, `-`, `pending` or `open` (case-insensitive). Every other answer counts as answered. |
| Output | Unanswered questions first, oldest first: date, work file, question. Then, with `--all`, answered questions newest first with their answers. A count line (`<open> open, <answered> answered`) always ends the output, after "No open questions." when none is open. |
| Dates | Sorted by the first `YYYY-MM-DD` in the cell ("2026-11-13 to 15" sorts as 2026-11-13), then by file and row order; a cell with no such date sorts last and is shown as written. |
| Options | `--all` as above; `--work <name>` limits to one work file; `--json` for scripts. |
| Exit code | 0 in every case, including open questions. `verify` is unchanged. |
| Writes | None. |
| Base | This plan is committed on its own on `claude/phase-1-close` with the `kanon status` plan. `kanon/kanon-questions/plan` is created from `main` after the `kanon status` pull request merges, so it starts from that code and carries only this work. |
| Branches | One item, `KQ-1` (section 1.3), on `kanon/kanon-questions/KQ-1`, merged into `kanon/kanon-questions/plan`. |
| Sequence | 1. Kritos passes the plan. 2. The owner approves the plan (`kanon approve kanon-questions --plan` or a transcribed reply). 3. `kanon branch start kanon-questions KQ-1`; build and commit on the item branch. 4. Kritos reviews the result; findings and rounds recorded in section 3. 5. `kanon branch merge kanon-questions KQ-1`. 6. `kanon verify` and the Cost row. 7. `kanon github pr kanon-questions` opens a draft as the App and writes the "approved when pull request #N merges" row itself. 8. `kanon github notes kanon-questions` posts Kritos's findings as a comment review (P1-10). 9. `kanon github ready kanon-questions`; CI runs (ADR-015). 10. The owner merges; the merge is the approval. Nothing is pushed before step 7. |
| Prerequisite | As for `kanon status`: `kanon verify` should skip git-ignored folders under `.claude`; it passes now that the stale worktree is removed. |

### 1.2 Acceptance

| Check | Confirmed by |
|---|---|
| Every Questions row in every work file is found once; rows in code fences are not | Test on a fixture repository |
| Empty, `-`, `pending` and `open` answers are unanswered; any other text is answered | Tests, one per form |
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
is counted in `kanon status` only. Differences are stated with their likely cause, as an assessment.

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-24 | Plan `kanon status` first and `kanon questions` after it ships, or both now? Recommended: status first. | Both now (owner) |

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| P1 | Plan, with `kanon status` | Kritos (`kritos-reviewer` agent) | correct | 1, 3 to 6 | 1: Work Items table added. 3, 4: comparison check and token windows added. 5: sequence follows ADR-015 with the plan approval. 6: contrast wording removed. Non-blocking 7 (base), 8 (section order), 12 (exact count command), 13 (dates, duplicates, count line) applied. Outside this plan: `verify` reads `.claude/worktrees/`, listed as a prerequisite. |

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
