---
type: work
status: awaiting-approval
updated: 2026-11-23
---

# Pull Request Draft Support

> **Summary:** `kanon github pr` opens pull requests as drafts; new `kanon github ready` and `kanon github draft`
> mark the App's pull request ready or return it to draft, as the App, for the ADR-015 lifecycle.
> **Decision needed:** Review and merge pull request #6 on GitHub; the merge is the approval.

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
| Assistant sessions | Allowed (question 1): `run_github` keeps refusing only `setup` and `protect`; a test confirms `pr`, `ready` and `draft` are not refused. |
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
| `setup` and `protect` stay refused in an assistant session; `ready` and `draft` are not | Test through `main([...])` with `CLAUDECODE=1` |
| `uv run pytest -q` and `uv run kanon verify` pass | Command output |
| Kritos passes the work | Section 3 |

Not covered: a live run against GitHub. The App is not yet installed on the owner's computer (A-3 in `kanon/work/2026-11-16-phase-1-plan.md`).

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-23 | May an assistant session run `kanon github pr`, `ready` and `draft` itself? They act as the App and the merge stays the person's approval. Recommended: allow. Default: person only. | Owner, 2026-11-23: allow agents. `setup` and `protect` stay refused. |

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| 1 | Build (3895860) | Kritos | Pass | None | 1: rule 14 names `draft`; fixed. 2: a closed cached pull request is passed over, and the open one is found into any base; fixed with a test. 3: drafts need a paid plan on private repositories (assessment); recorded in ADR-015. 4: Enterprise Server GraphQL URL; recorded as unsupported in ADR-015. 5: missing `node_id` reported as `GitHubError`; fixed with a test. 6: CLI refusal and draft mutation tested. 7: work file records; filled here. 8: README mentions drafts and the commands. |
| 2 | Fixes (a29c90f) | Kritos | Pass | None | All round 1 findings confirmed fixed or recorded; no regressions. |

## 4. Decision

| Item | Decision | Date | Basis |
|---|---|---|---|
| Result | Approved on merge of pull request #6 | 2026-11-24 | https://github.com/Bwalker01/Kanon/pull/6; a code owner's review is required to merge |

## 5. Cost

From the Plan commit (645f18c); reading before it is not counted.

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| plan, build, review | 18,623 | 10,108 | 77,374 | 3,502,663 | unavailable |
