---
type: decision
status: accepted
updated: 2026-11-16
---

# ADR-007: GitHub Mode and Cost Control

> **Decision:** GitHub Projects, branches and pull requests form an optional layer over the repository. Tokens and Actions minutes are spent only where they add value.
> **Status:** Accepted by the owner, 2026-11-16 (R-1).

## Context

- The owner asked for optional GitHub support: tickets and tool progress on a Project board, branches merged into reviewable pull requests with a breakdown and reviewer notes, minimal Actions usage and a token-conscious loop.
- GitHub does not allow a pull request's author to approve it.

## Decision

- **Source of truth:** the repository. GitHub mirrors it; only approvals, change requests and owner-edited fields are read back.
- **Branches:** one per ticket, merged into one pull request per approved plan. The description is generated from Kanon's files without a model call; reviewer notes are posted beneath.
- **Identity:** in GitHub mode Kanon acts through its own GitHub App or bot account, so the owner can approve under their own account.
- **Actions:** none by default; all GitHub operations run locally through `gh`. One optional check runs once per pull request, without model calls.
- **Cost rules:** free checks before model calls; summaries before full files; files instead of transcripts; only the next slice planned in full; three review rounds; a model chosen per role; per-ticket token budgets; cost shown on every work file.

## Basis

- Owner request (`kanon/sources.md`, section 4).
- `gh` 2.89 Project commands verified locally.
- Claude Code session logs record per-message token usage (verified 2026-11-13).

## Consequences

- Project board in Phase 2; branches, pull requests and Kanon's identity in Phase 3.
