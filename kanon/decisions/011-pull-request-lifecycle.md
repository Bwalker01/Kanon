---
type: decision
status: proposed
updated: 2026-11-23
---

# ADR-011: Pull Request Lifecycle

> **Decision:** Pull requests carry only completed, reviewed work. They open as drafts; CI runs when one is marked ready; a CI failure or a human review that is not an approval returns it to draft.
> **Status:** Proposed. Awaiting owner approval (see `kanon/REVIEW.md`). Amends the Actions bullet of ADR-007.

## Context

- A check on every push spends Actions minutes on work that later fails Kritos review and changes anyway.
- ADR-007 allows one optional check per pull request and runs all GitHub operations locally through `gh`.
- Owner instruction: `kanon/sources.md`, section 12. Design: `kanon/work/2026-11-23-pull-request-lifecycle.md`.

## Decision

- **Before pushing:** all Kritos reviews, corrections and record updates are finished. Nothing is pushed while findings are open.
- **Opening:** the pull request is the last step of a piece of work, opened as a draft.
- **Ready:** Metis marks it ready for review once the work is complete and ready to merge into `main`. The check runs then.
- **Back to draft:** a failing check, or a human review that requests changes or comments, returns the pull request to draft. Approvals and bot reviews do not.
- **Again:** after the fix and its review, Metis marks it ready, and the check runs again.
- **Actions:** one check workflow, skipped on drafts, and small jobs that return a pull request to draft. No model calls. This replaces "all GitHub operations run locally through `gh`" for these two events only.

## Basis

- Owner instruction and answers, `kanon/sources.md`, section 12.
- The return to draft must happen when no assistant session is open, so it runs in Actions (owner's choice).

## Consequences

- `.github/workflows/check.yml` and `.github/workflows/review-to-draft.yml`; Metis procedure step for pull requests.
- P1-10 (pull requests through the GitHub App) follows this lifecycle; its "no Actions minutes" check is relaxed to these workflows.
- Requiring the check in the `main` ruleset (A-3) blocks a merge of a commit that the check has not passed.
