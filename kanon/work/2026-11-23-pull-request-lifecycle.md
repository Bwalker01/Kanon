---
type: work
status: awaiting-approval
updated: 2026-11-23
---

# Pull Request Lifecycle

> **Summary:** Pull requests are opened as drafts only for completed, reviewed work; CI runs when one
> is marked ready; a CI failure or a human review that is not an approval returns it to draft.
> **Decision needed:** Approve ADR-015 in chat (`approve pull-request-lifecycle`); then merge pull request #4. The return to draft is untested on GitHub.

## 1. Plan

| Field | Value |
|---|---|
| Output | ADR-015; owner's words in `kanon/sources.md`; workflows in `.github/workflows/`; Metis procedure step 11 (`kanon/docs/roles/metis.md` and its template) |
| Inputs | Owner instruction, 2026-11-23 (`kanon/sources.md`, section 18); ADR-007; ADR-014; `.github/workflows/check.yml` from `2026-11-22-windows-test-portability.md` |
| Acceptance | A draft PR, or a push to one, starts no run; marking it ready starts the check; a failing check returns the PR to draft; a human review that is not an approval returns it to draft; an approval or a bot review does not; no agent acts on GitHub as the person; `kanon verify` passes |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### Lifecycle

| Stage | Who acts | Result |
|---|---|---|
| Work in progress | Creator, Kritos | Commits stay local; nothing is pushed while review findings are open |
| Work complete | Metis, then the person | Metis pushes the branch; the person opens a draft PR (or runs `kanon github pr`) |
| Ready | Person | PR marked ready for review; the check runs once |
| Check fails | Workflow | PR returned to draft; Metis fixes, reviews and pushes; the person marks it ready again |
| Human review, not an approval | Workflow | PR returned to draft; handled as above |
| Approval | Owner | Merge without squashing; the merge is the approval (ADR-014) |

### Workflow Design

| Item | Choice |
|---|---|
| `check.yml` triggers | `pull_request` into `main`: `opened`, `reopened`, `ready_for_review`; the check job is skipped while the PR is a draft (a run is listed but bills no minutes) |
| Push to a ready PR | No run, as the owner asked; with both matrix test jobs required on `main` (A-1), the new commit cannot merge until the PR is returned to draft and marked ready again |
| Failure handling | A second job in `check.yml`, run only when the check fails, converts the PR to draft with `gh pr ready --undo` and the workflow's token |
| Review handling | `review-to-draft.yml` on `pull_request_review: submitted`; acts when the reviewer is not a bot, the state is not `approved` and the PR is not a draft |
| Permissions | Check: `contents: read`. Draft jobs: `pull-requests: write`, no checkout, same-repository pull requests only |
| Cost | Draft jobs run in seconds on Ubuntu, only on those events; no model calls |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-23 | Which human reviews return a ready PR to draft? | Owner: changes requested and comment reviews; approvals and bot reviews do not |
| 2026-11-23 | Who returns the PR to draft: a small Actions job, or the assistant through `gh`? | Owner: a small Actions job |

## 3. Actions

| ID | Action | Assignee | Blocks | Done |
|---|---|---|---|---|
| A-1 | Require both matrix test jobs to pass before merging into `main` | Bwalker01 | | no |

### A-1: Required Checks

1. Mark pull request #4 ready once, so the check runs and GitHub lists its job names.
2. In the repository, open Settings, Rules, Rulesets, and create or edit a branch ruleset for `main`. Use a ruleset, not the classic branch rule: `kanon github protect` (A-4 in the Phase 1 plan) replaces the classic rule and would remove the checks.
3. Under "Require status checks to pass", add `ubuntu-latest / Python 3.11` and `windows-latest / Python 3.13`.

**Confirmed when:** a pull request without a passing check on its latest commit cannot be merged.

## 4. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| 1 | Lifecycle (f3fc649) | Kritos | Correct | F-1, F-2 | F-1: `synchronize` removed. F-2: the PR step moved before "stop". F-3: return to draft untested with the workflow token; open until the first failure or review. F-4: a single inline comment or reply also counts as a `commented` review; accepted, the owner may narrow it. F-5: required checks added as an owner action. F-7: draft jobs limited to same-repository PRs. Others: records updated. |
| 2 | Lifecycle (3e9527b) | Kritos | Correct | N-1 | N-1: stale Trigger row in the Windows work file; fixed. N-2, N-4: wording. N-5: skipped-draft and required-check behaviour are assessments, confirmed at the first GitHub run. |
| 3 | Lifecycle (9896a2a) | Kritos | Pass | None | Wording note applied. |
| M1 | Merge (1ca374d) | Kritos | Correct | F-1, F-2 | ADR renumbered to ADR-015 and fitted to ADR-014. F-2: A-1 uses a ruleset, since `kanon github protect` replaces the classic rule. F-3: `kanon github pr` opens ready; wording fixed. F-4: workflow token stated as a second identity, amending ADR-014. F-5: approval route stated in the summary. F-6: rule 14 updated. F-7: owner's message given its own sources section. F-1 is in the Windows work file. |

## 5. Decision

Pending.

## 6. Cost

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| plan, build, review | 11,686 | 13,814 | 54,794 | 2,210,123 | incomplete: $0.00 so far |
