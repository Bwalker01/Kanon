---
type: decision
status: accepted
updated: 2026-11-18
---

# ADR-003: Human Approval

> **Decision:** A person approves every major output from a single review list. Approvals are tamper-evident locally and tamper-proof only through a separate identity.
> **Status:** Accepted by the owner, 2026-11-16 (R-1).

## Context

- The owner asked for explicit approval on plans, decisions and documentation, presented clearly.
- A Phase 0 test showed the assistant can obtain a terminal and write files, so a locally stored approval cannot prove who gave it.

## Decision

- **Major outputs (owner approves):** requirements, plans, decisions, documentation of record, marketplace additions or changes, merges and releases.
- **Minor outputs (reviewer only):** status updates, ticket changes, intermediate work. Listed in `STATUS.md`.
- **One list:** `kanon/REVIEW.md` holds every decision awaiting the owner and every action only the owner can take, each with a link to what to read or the steps to follow (owner, 2026-11-18).
- **Local approvals** record the approver, time, commit and a hash of the approved material; any later change is detected.
- **Tamper-proof approvals** require the assistant to act under its own identity (ADR-007).

## Basis

- Owner answer 4 (`kanon/sources.md`, section 2).
- Learning L-001 (`kanon/docs/learnings.md`).

## Consequences

- The assistant never records an approval.
- The residual risk of a forged local approval is documented, not hidden.
- Superseded in part by ADR-011: the review list and status page are generated per person.
- Amended by ADR-013 (proposed): the assistant may record an approval only as a labelled transcription of the approver's words.
