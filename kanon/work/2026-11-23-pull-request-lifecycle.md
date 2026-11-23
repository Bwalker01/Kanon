---
type: work
status: awaiting-approval
updated: 2026-11-23
---

# Pull Request Lifecycle

> **Summary:** Pull requests are opened as drafts only for completed, reviewed work; CI runs when one
> is marked ready; a CI failure or a human review that is not an approval returns it to draft.
> **Decision needed:** R-3 (ADR-011) in `kanon/REVIEW.md`. The return to draft is untested on GitHub.

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
| `check.yml` triggers | `pull_request` into `main`: `opened`, `reopened`, `ready_for_review`; the check job is skipped while the PR is a draft (a run is listed but bills no minutes) |
| Push to a ready PR | No run, as the owner asked; with both matrix test jobs required in the `main` ruleset (A-3), the new commit cannot merge until the PR is returned to draft and marked ready again |
| Failure handling | A second job in `check.yml`, run only when the check fails, converts the PR to draft with `gh pr ready --undo` |
| Review handling | `review-to-draft.yml` on `pull_request_review: submitted`; acts when the reviewer is not a bot, the state is not `approved` and the PR is not a draft |
| Permissions | Check: `contents: read`. Draft jobs: `pull-requests: write`, no checkout, same-repository pull requests only |
| Cost | Draft jobs run in seconds on Ubuntu, only on those events; no model calls |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-23 | Which human reviews return a ready PR to draft? | Owner: changes requested and comment reviews; approvals and bot reviews do not |
| 2026-11-23 | Who returns the PR to draft: a small Actions job, or the assistant through `gh`? | Owner: a small Actions job |

## 3. Review

| Round | Reviewer | Verdict | Findings |
|---|---|---|---|
| 1 | Kritos | Correct | F-1 (blocking): the check also ran on pushes to a ready PR; `synchronize` removed, ADR-011 states it replaces ADR-007's "once". F-2 (blocking): the PR step came after "stop"; now step 10, before Prepare the decision. F-3: return to draft untested with `GITHUB_TOKEN`; open, tested at the first failure or review. F-4: a single inline comment or a reply also counts as a `commented` review and returns the PR to draft; accepted, owner may narrow it in R-3. F-5: A-3 and setup section 3 now require both check jobs. F-6, F-10: R-2, R-3, STATUS and summary updated. F-7: draft jobs limited to same-repository PRs; fork limit stated in ADR-011. F-8: none required. F-9: ADR-007 and P1-10 annotated on acceptance. |
| 2 | Kritos | Correct | All round 1 findings resolved as recorded. N-1 (blocking): stale Trigger row in the Windows work file; fixed. N-2: R-2 now follows R-3. N-3: PR #4 is a draft; it is marked ready after the push, which starts the check. N-4: "both matrix test jobs". N-5: skipped-draft and required-check behaviour are assessments, confirmed at the first GitHub run with F-3. |
| 3 | Kritos | Pass | N-1, N-2 and N-4 confirmed. Note applied: ADR-011 now says "both matrix test jobs". |

## 4. Decision

Awaiting the owner (R-3).

## 5. Cost

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| plan, build, review | 11,686 | 13,814 | 54,794 | 2,210,123 | incomplete: $0.00 so far |

