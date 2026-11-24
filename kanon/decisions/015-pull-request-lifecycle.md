---
type: decision
status: proposed
updated: 2026-11-23
---

# ADR-015: Pull Request Lifecycle

> **Decision:** Pull requests carry only completed, reviewed work. They open as drafts; CI runs when one is marked ready; a CI failure or a human review that is not an approval returns it to draft.
> **Status:** Proposed. Awaiting owner approval (`kanon/work/2026-11-23-pull-request-lifecycle.md`). Amends the Actions bullet of ADR-007 and ADR-014's "only as a GitHub App" (proposed), on which it depends.

## Context

- A check on every push spends Actions minutes on work that later fails Kritos review and changes anyway.
- ADR-007 allows "one optional check runs once per pull request" and runs GitHub operations locally through `gh`.
- ADR-014: agents never act as the person on GitHub; pull requests are opened by the person or `kanon github pr`.
- Owner instruction: `kanon/sources.md`, section 18.

## Decision

- **Before pushing:** all Kritos reviews, corrections and record updates are finished. Nothing is pushed while findings are open.
- **Opening:** the pull request is the last step of a piece of work, opened as a draft by the person on GitHub. `kanon github pr` opens it ready until draft support is built.
- **Ready:** the person marks it ready once the work is complete and ready to merge into `main`. The check runs then, and not on later pushes.
- **Back to draft:** a failing check, or a human review that requests changes or comments, returns the pull request to draft. Approvals and bot reviews do not.
- **Again:** after the fix, its review and a push, the person marks it ready, and the check runs again.
- **Actions:** one check workflow, skipped on drafts, and small jobs that return a pull request to draft using the workflow's own token (the GitHub Actions app), never the person's login; this is a second identity beside ADR-014's App, for that one action, amending ADR-014's "Kanon acts on GitHub only as a GitHub App". No model calls. This replaces ADR-007's "runs once per pull request" with once per ready state.

## Basis

- Owner instruction and answers, `kanon/sources.md`, section 18.
- The return to draft must happen when no assistant session is open, so it runs in Actions (owner's choice).

## Consequences

- `.github/workflows/check.yml` and `.github/workflows/review-to-draft.yml`; Metis procedure step 11.
- Requiring both matrix test jobs on `main` blocks merging a commit pushed after the check ran; it must be returned to draft and marked ready again (owner action in the work file). The requirement lives in a ruleset, because `kanon github protect` replaces the classic branch rule and would drop it.
- Rule 14 (`rules-kanon.md`) states the push and draft steps alongside Metis step 11.
- Pull requests from forks get a read-only token, so they are not returned to draft automatically.
- Draft and ready support in `kanon github pr` is not built; until then the person does both on GitHub.
- On acceptance, ADR-007 and ADR-014 are annotated as amended by this record.
