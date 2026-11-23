---
type: work
status: planning
updated: 2026-11-23
---

# Pull Request Lifecycle

> **Summary:** Pull requests are opened as drafts only for completed, reviewed work; CI runs when one
> is marked ready; a CI failure or a human review that is not an approval returns it to draft.
> **Decision needed:** None yet.

## 1. Plan

| Field | Value |
|---|---|
| Output | ADR-011; owner's words in `kanon/sources.md`; workflows in `.github/workflows/`; Metis procedure (`kanon/docs/roles/metis.md` and its template) |
| Inputs | Owner instruction, 2026-11-23 (`kanon/sources.md`, section 12); ADR-007; Phase 1 plan item P1-10; `.github/workflows/check.yml` from `2026-11-22-windows-test-portability.md` |
| Acceptance | A draft PR, or a push to one, starts no run; marking it ready starts the check; a failing check returns the PR to draft; a human review that is not an approval returns it to draft; an approval or a bot review does not; `kanon verify` passes |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### Lifecycle

| Stage | Who acts | Result |
|---|---|---|
| Work in progress | Creator, Kritos | Commits stay local; nothing is pushed while review findings are open |
| Work complete | Metis | Branch pushed; draft PR opened |
| Ready | Metis | PR marked ready for review; the check runs once |
| Check fails | Workflow | PR returned to draft; Metis fixes, reviews, then marks it ready again |
| Human review, not an approval | Workflow | PR returned to draft; Metis addresses it, then marks it ready again |
| Approval | Owner | Merge without squashing |

### Workflow Design

| Item | Choice |
|---|---|
| `check.yml` triggers | `pull_request` into `main`: `opened`, `reopened`, `ready_for_review`, `synchronize`; every job skipped while the PR is a draft |
| Push to a ready PR | Runs the check (assessment: rare under this process, and it prevents a stale result on a new commit) |
| Failure handling | A second job in `check.yml`, run only when the check fails, converts the PR to draft with `gh pr ready --undo` |
| Review handling | `review-to-draft.yml` on `pull_request_review: submitted`; acts when the reviewer is not a bot, the state is not `approved` and the PR is not a draft |
| Permissions | Check: `contents: read`. Draft jobs: `pull-requests: write`, no checkout |
| Cost | Draft jobs run in seconds on Ubuntu, only on those events; no model calls |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-23 | Which human reviews return a ready PR to draft? | Owner: changes requested and comment reviews; approvals and bot reviews do not |
| 2026-11-23 | Who returns the PR to draft: a small Actions job, or the assistant through `gh`? | Owner: a small Actions job |

## 3. Review

Not yet reviewed.

## 4. Decision

Pending.

## 5. Cost

