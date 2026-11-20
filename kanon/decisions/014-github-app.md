---
type: decision
status: proposed
updated: 2026-11-20
---

# ADR-014: GitHub App Identity

> **Decision:** Kanon acts on GitHub only as a GitHub App that a person creates for their organisation; agents never act as a person, and a pull request's merge is the final approval.
> **Status:** Proposed, 2026-11-20; the owner decides at the group C review point. Amends ADR-007.

## Context

- ADR-007 chose an App or bot account so the owner approves under their own account.
- Cloud sessions already act as the owner through the GitHub connector and Git proxy (assessment, 2026-11-19).
- On 2026-11-20 this cloud session's agent proxy refused `GET /app`: GitHub App API paths cannot be used from Claude Code cloud sessions.

## Decision

- **Identity:** one App per organisation or person, created with `kanon github setup` (GitHub's manifest flow) on the person's own computer. `app_id` and `app_slug` live in `[github]` of `kanon/kanon.toml`; a standalone Kanon-managed App is a later phase.
- **Key:** `~/.config/kanon/github-app.pem` (mode 600) locally, or `KANON_APP_KEY` in an environment; never committed. Tokens last one hour, cover one repository and stay in memory.
- **Owner's login:** agents never use it. `kanon sync` denies the GitHub connector's writing tools and the guard blocks writing `gh` commands.
- **Approval:** `kanon github protect` requires a code owner's review on `main`, merge commits only, with no bypass. Merging the pull request is the approval; Kanon records "Approved on merge of pull request #N" when it opens it.
- **Where it runs:** GitHub mode runs on the person's computer; cloud sessions do everything else (owner, 2026-11-20).

## Basis

- Owner answers, 2026-11-19 and 2026-11-20 (`kanon/work/2026-11-16-phase-1-plan.md`, Questions).
- Tests against recorded GitHub responses (`tests/test_github.py`); the live check waits for owner action A-3.

## Consequences

- A session's clone and the cloud harness's own branch pushes still use the owner's connection.
- The key is readable by commands in any environment that holds `KANON_APP_KEY`.
- GitHub Enterprise Server differences are untested.
