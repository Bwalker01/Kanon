---
name: ADR-009 Optional GitHub mode, and a cost-conscious loop
description: GitHub Projects, branches and pull requests are an optional layer over the repository; the loop spends tokens and Actions minutes only where they earn their place
type: decision
status: accepted (amendment awaiting owner approval)
date: 2026-11-13
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-009
  - GitHub mode
  - Cost
  - D9
---

# ADR-009: Optional GitHub mode, and a cost-conscious loop

## Context

The owner asked for optional GitHub support: Projects to track tickets and where tools are
in their production, branches merged into reviewable pull requests with a breakdown in the
description and reviewer notes underneath, care with Actions minutes for small groups, and
a token-conscious loop throughout.

## Decision

- **The repository stays the source of truth** (Pinax tickets, `docs/`, `plans/`). GitHub
  is a human-readable mirror written by Kanon; only approvals, change requests and fields
  the owner chooses are read back.
- **One branch per ticket, one pull request per approved plan**, with a description built
  from Kanon's own files (no model call) and the AI reviewer's notes as a comment review.
- **No Actions minutes by default:** everything runs from the user's machine through `gh`.
  One optional verification workflow runs once per pull request with no model calls.
- **Cost rules** from foundation plan section 8: free checks before paid ones, progressive
  loading, files not transcripts, plan only the next slice, capped review rounds, a model
  per role, batched minor reviews, per-ticket token budgets that pause work, cost shown.

**Amendment (Phase 0, pending owner approval at the Phase 0 gate):** GitHub does not let the
author of a pull request approve it. If Kanon opens pull requests with the owner's own
login, the owner is the author and **cannot approve them**, which breaks the approval gate
in foundation plan section 7.3. It also means anything Kanon does on GitHub is
indistinguishable from the owner. Therefore, in GitHub mode Kanon acts through its **own
GitHub identity**, preferably a GitHub App installed on the repository, or a dedicated bot
account. Branch protection on `main` then requires the owner's review, which the assistant
cannot give. Solo use without a separate identity falls back to local, tamper-evident
approvals (ADR-004).

## Evidence

- Owner request ([owner brief](../sources/2026-11-13-owner-brief.md), section 4).
- `gh` 2.89 provides `project item-add`, `item-edit`, `field-create` (checked locally);
  they need the `project` token scope.
- GitHub changelog, 2025-12-16: Actions stays free on standard runners for public
  repositories. The private-repository allowance could not be confirmed (docs.github.com
  blocked in this session).
- Koine discipline 1 (single source of truth); Pinax ADR-004 (tracker is not a knowledge
  base); AutoBuild per-seat models, usage meters and correction limits.

## Consequences

- Phase 2 adds the Project board; Phase 3 adds branches, pull requests and the separate
  identity.
- Phase 1 must find out what token usage Claude Code reports before per-ticket budgets are
  promised.
- Foundation plan section 7.3 is superseded on the point of who opens pull requests.
