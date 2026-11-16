---
type: decision
status: proposed
updated: 2026-11-16
---

# ADR-008: Agent Conduct and Writing

> **Decision:** Agents ask early, challenge weak proposals, stay realistic and match each person's technical level. Documents are concise, professional and free of AI-writing patterns.
> **Status:** Proposed. Awaiting owner approval (see `kanon/REVIEW.md`).

## Context

- The owner asked for agents that behave as candid peers and for documents that read naturally and professionally, with clear structure.

## Decision

- **Standard:** `kanon/docs/conduct-and-writing.md` applies to every agent.
- **Questions** are asked when information is missing, not at the gate, and recorded in the work file.
- **Technical level** is set by a question at setup and adjusted only with the person's confirmation.
- **Documents** follow a fixed layout with a summary block, length limits and a professional tone. Strictly checked.
- **Chat** is brief, friendly and professional, and points to `REVIEW.md` instead of restating it.

## Basis

- Owner requests (`kanon/sources.md`, sections 6 and 7) and answers of 2026-11-14.
- Koine-OS writing-quality reviewer (credited in the standard).

## Consequences

- `kanon verify` applies the mechanical writing checks; the reviewer applies the rest.
