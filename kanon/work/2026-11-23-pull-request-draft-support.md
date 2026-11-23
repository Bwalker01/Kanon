---
type: work
status: planning
updated: 2026-11-23
---

# Pull Request Draft Support

> **Summary:** `kanon github pr` opens pull requests as drafts; new `kanon github ready` and `kanon github draft`
> mark the App's pull request ready or return it to draft, as the App, for the ADR-015 lifecycle.
> **Decision needed:** None yet.

## 1. Plan

| Field | Value |
|---|---|
| Output | `src/kanon/github.py`, `src/kanon/cli.py`, `tests/test_github.py`; rule 14 (`src/kanon/templates/rules-kanon.md`); Metis step 11 (`kanon/docs/roles/metis.md` and `src/kanon/templates/roles/metis.md`); ADR-015 |
| Inputs | ADR-014; ADR-015 (proposed, `kanon/work/2026-11-23-pull-request-lifecycle.md`); the existing `kanon github` commands (P1-10) |
| Acceptance | See 1.2 |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### 1.1 Design

| Item | Choice |
|---|---|
| Opening | `open_or_update` creates the pull request with `"draft": true`. On a later run it updates the title and description with `PATCH` and leaves the draft state unchanged. |
| Description | Running `kanon github pr <work>` again pushes the plan branch and rewrites the description from the work file, as today. No separate command. |
| Ready and draft | `kanon github ready <work>` and `kanon github draft <work>` find the pull request (cache, then the open pull request for `kanon/<work>/plan`), read its `node_id` over REST and call the GraphQL mutation `markPullRequestReadyForReview` or `convertPullRequestToDraft` through the App installation token. |
| Only the App's pull request | Both commands refuse a pull request that is closed, merged, or not opened by the App (`user.login` is not `<app slug>[bot]`). A pull request already in the wanted state is reported and left alone. |
| Errors | GraphQL answers `200` with an `errors` list on failure; the module raises `GitHubError` with GitHub's message. Tokens never appear in output (K-410). |
| Identity | No `gh`, no person's login. The App's token is the only credential, as for `pr`, `notes` and `sync`. |
| CI trigger | Assessment, untested on GitHub: a `ready_for_review` event caused by an App installation token starts workflows (only the workflow's own `GITHUB_TOKEN` is exempt), so `check.yml` runs when the App marks the pull request ready. |
| Assistant sessions | Decided by question 1 (section 2). Allowed: `run_github` keeps refusing only `setup` and `protect`. Person only: `pr`, `ready` and `draft` are added to the refused set, with a test. |
| Records | Rule 14, Metis step 11 (both copies) and ADR-015 replace "opens it ready until draft support is built" with the new commands and the answer to question 1. |
| Base | PR #4 (`claude/windows-tests`) is not merged, and it holds ADR-015, so this branch starts from it. The pull request for this work goes into `main` after PR #4, or into `claude/windows-tests` if the owner prefers. |

### 1.2 Acceptance

| Check | Confirmed by |
|---|---|
| A new pull request is created with `draft: true` | Test against recorded responses |
| A second `pr` run sends `PATCH` with title and body only | Test |
| `ready` and `draft` send the right GraphQL mutation with the pull request's `node_id` | Tests |
| Closed, merged or non-App pull requests are refused; no-op when already in state | Tests |
| GraphQL `errors` become a `GitHubError` | Test |
| Assistant-session rule matches question 1 | Test through `main([...])` with `CLAUDECODE=1` |
| `uv run pytest -q` and `uv run kanon verify` pass | Command output |
| Kritos passes the work | Section 3 |

Not covered: a live run against GitHub. The App is not yet installed on the owner's computer (A-3 in `kanon/work/2026-11-16-phase-1-plan.md`).

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-23 | May an assistant session run `kanon github pr`, `ready` and `draft` itself? They act as the App and the merge stays the person's approval. Recommended: allow. Default: person only. | Pending |

## 3. Review

Not yet reviewed.

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
