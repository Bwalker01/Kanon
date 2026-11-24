---
type: work
status: awaiting-approval
updated: 2026-11-24
---

# Kanon Status

> **Summary:** P1-08, first requirement: a read-only `kanon status` command that prints each open piece
> of work with its state and what waits on whom, built and delivered through the full Kanon loop.
> **Decision needed:** Approve this plan in chat (`approve kanon-status`). Kritos passed it in round P3.

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
| Output | Line 1: branch and the count of open work. Then one block per open work file: title, status, path, and the waiting decision, open actions (with assignees) and late reviews when present. Closed work (`complete` and `parked`, `desk.CLOSED`) gets no block of its own; its open actions, waiting decisions and late reviews follow under "From closed work", grouped by file (on this repository: A-1 in the pull request lifecycle file and a late review in the review records file). With no open work and no such items it prints "No open work." |
| Options | `--json` prints the same data as JSON, for scripts. No other options. |
| Profile | `status` lists every person's actions, decisions and late reviews, each action with its assignee. The Desk keeps showing one person's items. |
| Exit code | 0 whenever the repository is a Kanon project; 2 with a message when `kanon/kanon.toml` is missing. |
| Writes | None. A test compares the working tree and `kanon/local/` before and after. |
| Base | This plan is committed on its own on `claude/phase-1-close` (rule 1), which reaches `main` through the owner's pull request. `kanon/kanon-status/plan` is then created from that `main` commit, so its pull request carries only this work. |
| Branches | One item, `KS-1` (section 1.3), on `kanon/kanon-status/KS-1`, merged into `kanon/kanon-status/plan`. |
| Sequence | 0. Once both P1-08 plans pass Kritos and await approval, and every other piece of work on the branch has passed review or been decided by the owner, `claude/phase-1-close` is pushed and the owner opens and merges its pull request. That merge does not approve the P1-08 plans; they stay `awaiting-approval` on `main` until step 2. 1. Kritos passes the plan. 2. The owner approves the plan (`kanon approve kanon-status --plan` or a transcribed reply); the assistant creates `kanon/kanon-status/plan` from the `main` commit that merged step 0 (`git branch kanon/kanon-status/plan <that commit>`, since `kanon branch start` branches from the current commit), and the approval row is its first commit. 3. `kanon branch start kanon-status KS-1`; build and commit on the item branch. 4. Kritos reviews the result; findings and rounds recorded in section 3. 5. `kanon branch merge kanon-status KS-1`. 6. `kanon verify` and the Cost row; status set to `awaiting-approval` with a "Decision needed" line (rule 5), since `kanon github pr` sets it only when no item was merged. 7. `kanon github pr kanon-status` opens a draft as the App and writes the "approved when pull request #N merges" row itself. 8. `kanon github notes kanon-status <notes file>` posts Kritos's findings as a comment review (P1-10); the notes file is written in the session's scratchpad, outside the repository. 9. `kanon github ready kanon-status`; CI runs (ADR-015). 10. The owner merges; the merge is the approval. 11. Clio sets the status to `complete` on `main`. After step 0, nothing is pushed before step 7. |
| Prerequisite | `kanon verify` must skip git-ignored folders under `.claude` (it now reads `.claude/worktrees/`, `src/kanon/verify.py:447`). The stale worktree was removed on 2026-11-24 (owner), so `verify` passes now; the fix stays a separate piece of work. |

### 1.2 Acceptance

| Check | Confirmed by |
|---|---|
| Every open work file appears once with its status and path; `complete` and `parked` work does not | Test on a fixture repository |
| With a profile whose `github` is neither an assignee nor an approver, every action, decision and late review still appears | Test |
| A waiting decision, open actions with assignees, and late reviews are shown for the work that has them | Test |
| An open action and a late review in `complete` or `parked` work appear under "From closed work" | Test on a fixture repository |
| The work listed equals the Work in Progress list of `render_status` on a fixture holding open, `complete` and `parked` work | Test |
| No network call is made | Test with `github.sign_in` patched to raise |
| `--json` holds the same work, decisions, actions, late reviews and "From closed work" items as the text output | Test |
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
actions raised and tokens. Tokens: `kanon usage --since 2026-11-24T18:05:00Z --until <merge of this work's
pull request>`. The start is an ISO time before the Desk rebuild at 18:09 that began this planning,
since the plan commit fcc3772 came after drafting and round 1 (`usage` reads commit time). The joint
plan reviews covered both requirements; their tokens are recorded once, here, and marked as shared.
Assessment: this makes the first run look costlier, and `kanon usage` also counts other work in the
same sessions (on 2026-11-24, the Phase 1 records in 07e3263 and the remote session limits commits of
18:50 to 18:54), which is listed beside the figures.

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-24 | Plan `kanon status` first and `kanon questions` after it ships, or both now? Recommended: status first. | Both now (owner) |

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| P1 | Plan, with `kanon questions` | Kritos (`kritos-reviewer` agent) | correct | 1 to 5 | 1: no Work Items table, so `kanon branch start` failed; table added. 2: `desk.build` filters by profile; `everyone=True` and a test added. 3, 4: comparison checks and token windows added. 5: sequence follows ADR-015 with the plan approval. Non-blocking 7 (base), 8 (section order), 9 (network test), 10, 11 (wording) applied. Outside this plan: `verify` reads `.claude/worktrees/`, listed as a prerequisite. |
| P2 | Round 1 fixes (fcc3772 and the record after it) | Kritos (`kritos-reviewer` agent) | correct | S1, S2 | S1: items in closed work now shown under "From closed work", with a test. S2: token window starts at an ISO time before planning. Non-blocking N1 (notes file), N2 (status before and after the pull request), N3 (base and approval commit), N5 (concurrent work labelled) applied. |
| P3 | Round 2 fixes (370166a) | Kritos (`kritos-reviewer` agent) | pass | None | Non-blocking 1 (step 0 waits for every piece of work on the branch), 2 (step 0 merge does not approve), 5 (who creates the plan branch) and 6 (JSON check, concurrent work) applied. |

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
