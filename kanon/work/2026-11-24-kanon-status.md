---
type: work
status: planning
updated: 2026-11-24
---

# Kanon Status

> **Summary:** P1-08, first requirement: a read-only `kanon status` command that prints each open piece
> of work with its state and what waits on whom, built and delivered through the full Kanon loop.
> **Decision needed:** None yet; the plan goes to Kritos first.

## 1. Plan

| Field | Value |
|---|---|
| Output | `kanon status` in `src/kanon/cli.py`, a `status` renderer in `src/kanon/desk.py`, `tests/test_status.py`, a README line |
| Inputs | P1-08 in `kanon/work/2026-11-16-phase-1-plan.md`; `desk.build` (P1-10 Desk data); ADR-011 |
| Acceptance | See 1.2 |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### 1.1 Design

| Part | Choice |
|---|---|
| Purpose | The terminal view of `kanon/local/STATUS.md`, without rebuilding the Desk or writing a file. |
| Data | `desk.build(root, everyone=True)`: a new keyword argument that skips the profile filters (`github in a.assignees`, `may_approve`) and the "no GitHub username" note; the Desk keeps the default `everyone=False`. Other profile notes are printed after the output. No network call; pull request state comes from Git history and the local cache (K-402). |
| Output | Line 1: branch and the count of open work. Then one block per open work file: title, status, path, and the waiting decision, open actions (with assignees) and late reviews when present. Closed work (`complete` and `parked`, `desk.CLOSED`) is omitted. With no open work it prints "No open work." |
| Options | `--json` prints the same data as JSON, for scripts. No other options. |
| Profile | `status` lists every person's actions, decisions and late reviews, each action with its assignee. The Desk keeps showing one person's items. |
| Exit code | 0 whenever the repository is a Kanon project; 2 with a message when `kanon/kanon.toml` is missing. |
| Writes | None. A test compares the working tree and `kanon/local/` before and after. |
| Base | This plan is committed on its own on `claude/phase-1-close` (rule 1), which reaches `main` through the owner's pull request. `kanon/kanon-status/plan` is then created from that `main` commit, so its pull request carries only this work. |
| Branches | One item, `KS-1` (section 1.3), on `kanon/kanon-status/KS-1`, merged into `kanon/kanon-status/plan`. |
| Sequence | 1. Kritos passes the plan. 2. The owner approves the plan (`kanon approve kanon-status --plan` or a transcribed reply). 3. `kanon branch start kanon-status KS-1`; build and commit on the item branch. 4. Kritos reviews the result; findings and rounds recorded in section 3. 5. `kanon branch merge kanon-status KS-1`. 6. `kanon verify` and the Cost row. 7. `kanon github pr kanon-status` opens a draft as the App and writes the "approved when pull request #N merges" row itself. 8. `kanon github notes kanon-status` posts Kritos's findings as a comment review (P1-10). 9. `kanon github ready kanon-status`; CI runs (ADR-015). 10. The owner merges; the merge is the approval. Nothing is pushed before step 7. |
| Prerequisite | `kanon verify` must skip git-ignored folders under `.claude` (it now reads `.claude/worktrees/`, `src/kanon/verify.py:447`). The stale worktree was removed on 2026-11-24 (owner), so `verify` passes now; the fix stays a separate piece of work. |

### 1.2 Acceptance

| Check | Confirmed by |
|---|---|
| Every open work file appears once with its status and path; `complete` and `parked` work does not | Test on a fixture repository |
| With a profile whose `github` is neither an assignee nor an approver, every action, decision and late review still appears | Test |
| A waiting decision, open actions with assignees, and late reviews are shown for the work that has them | Test |
| The work listed equals the Work in Progress list of `render_status` on a fixture holding open, `complete` and `parked` work | Test |
| No network call is made | Test with `github.sign_in` patched to raise |
| `--json` holds the same work, decisions and actions as the text output | Test |
| No file is written or changed | Test |
| Runs from a subdirectory; missing `kanon.toml` exits 2 with a message | Tests |
| `uv run pytest -q` and `uv run kanon verify` pass | Command output |
| The work file holds every section in schema order, and the plan was committed on its own before the build (`verify`'s loop rule) | `kanon verify` on this repository |
| Removing any one section from a copy of this file fails `check_document` naming the section | Test, one case per section |
| Section 1.4 records rounds, questions asked, owner actions and tokens | Owner reads section 1.4 at the final review |
| Kritos passes the plan and the result | Section 3 |

Not covered: a check of the pull request's App identity beyond the author shown on GitHub.

### 1.3 Work Items

| ID | Item | Delivers |
|---|---|---|
| KS-1 | `kanon status` | Command, `everyone` option on `desk.build`, tests, README line |

### 1.4 Measures for P1-08

Recorded at the end for comparison with `kanon questions`: review rounds, questions asked, owner
actions raised and tokens. Tokens: `kanon usage --since <this plan's commit> --until <merge of this
work's pull request>`. The joint plan review of 2026-11-24 covered both requirements; its tokens are
recorded once, here, and marked as shared. Assessment: this makes the first run look costlier.

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-24 | Plan `kanon status` first and `kanon questions` after it ships, or both now? Recommended: status first. | Both now (owner) |

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| P1 | Plan, with `kanon questions` | Kritos (`kritos-reviewer` agent) | correct | 1 to 5 | 1: no Work Items table, so `kanon branch start` failed; table added. 2: `desk.build` filters by profile; `everyone=True` and a test added. 3, 4: comparison checks and token windows added. 5: sequence follows ADR-015 with the plan approval. Non-blocking 7 (base), 8 (section order), 9 (network test), 10, 11 (wording) applied. Outside this plan: `verify` reads `.claude/worktrees/`, listed as a prerequisite. |

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
