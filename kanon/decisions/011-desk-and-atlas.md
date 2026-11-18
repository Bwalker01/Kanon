---
type: decision
status: accepted
updated: 2026-11-18
---

# ADR-011: Desk and Atlas

> **Decision:** Nothing volatile or personal is committed: decisions and owner actions live in work files, and each person's Desk is generated from them by a new role, Atlas.
> **Status:** Accepted by the owner, 2026-11-18 (R-1). Supersedes parts of ADR-003 and ADR-009.

## Context

- Committed `REVIEW.md` and `STATUS.md` conflict when several branches are in progress.
- `REVIEW.md` held one person's decisions and actions.
- Design: `kanon/work/2026-11-18-desk-and-atlas.md`.

## Decision

- **Decisions:** a work file with status `awaiting-approval` and a "Decision needed" line.
- **Actions:** an optional Actions section in the work file that needs them, with steps.
- **Desk:** `kanon desk` generates `kanon/local/DESK.md`, `desk.html` and `STATUS.md` for the current person and branch; `kanon/local/` is never committed.
- **Roadmap:** `kanon/docs/roadmap.md`, committed.
- **Atlas:** a thirteenth archetype, extending Koine-OS, that keeps the Desk.

## Basis

- Owner requests and choices (`kanon/sources.md`, section 12).

## Consequences

- ADR-003: the "one list" is the generated Desk, built from work files.
- ADR-009: `REVIEW.md` and `STATUS.md` leave the layout; `kanon/local/` and the roadmap join it.
- The Desk page keeps ticks in the browser only; decisions still return through chat or `kanon approve`.
