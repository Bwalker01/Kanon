---
type: decision
status: accepted
updated: 2026-11-16
---

# ADR-002: Method: the Koine Loop

> **Decision:** Every significant output is planned, created, independently reviewed and revised, for at most three rounds, before a person approves it at a gate.
> **Status:** Accepted by the owner, 2026-11-16 (R-1).

## Context

- The owner's brief requires the Koine Loop from Koine-OS: plan, create, review, adjust, repeat until clean.
- Koine-OS's own Claude Code adapter states that the loop cannot be enforced mechanically. Kanon is built to enforce it.

## Decision

- **Specification first.** Each piece of work states its inputs, output, acceptance checks and reviewer before work starts.
- **Independent review.** The reviewer uses a separate prompt and read-only tools, and never sees the creator's conversation.
- **Verdicts:** `pass`, `correct`, `escalate` or `park`, with each finding marked blocking or non-blocking.
- **Round limit:** three. After that, the person decides.
- **Paired roles.** Every generator has a named reviewer.
- **Retained Koine-OS disciplines:** single source of truth; ADDED, MODIFIED or REMOVED commit messages; a status page read first; recorded learnings; verbatim sources.
- **Departures from Koine-OS** (file layout, drafts, daily log) are set out in ADR-009.

## Basis

- Koine-OS `method/the-koine-loop.md` and `method/knowledge-discipline.md`.
- AutoBuild reviewer verdict rules (`docs/architecture.md`).
- Owner choice of three rounds (2026-11-14).

## Consequences

- `kanon verify` checks the loop mechanically from Phase 1.
- A loop that does not converge in three rounds is treated as a fault in the specification or the reviewer.
