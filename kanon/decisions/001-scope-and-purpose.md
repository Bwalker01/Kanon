---
type: decision
status: accepted
updated: 2026-11-16
---

# ADR-001: Scope and Purpose

> **Decision:** Kanon turns a person's requirements into delivered, documented work through specialist agents and tools. It is proven on its own repository first.
> **Status:** Accepted by the owner, 2026-11-16 (R-1).

## Context

- The owner's brief asks for a context engine that any repository can adopt, which grows with the project and delivers what the owner specifies.
- "Agora" was an earlier idea with no written record. It is background only.
- Ergasterion is a deterministic pipeline generator with no AI model inside. It is a tool, not an agent.

## Decision

- **Pipeline:** intake, refine requirement, plan, create tickets, assign specialists, build, review, document, release.
- **Domain:** unrestricted. Software, proofs of concept, security, automation and data products are all in scope.
- **Specialists:** the marketplace holds *agents* (roles) and *tools* (programs agents run). See ADR-004.
- **Proving ground:** this repository is Kanon's first instance. An outside project follows in Phase 5.

## Basis

- Owner brief and answers 1, 2 and 7 (`kanon/sources.md`, sections 1 and 2).
- Ergasterion `README.md`; a source search found no model calls.

## Consequences

- The requirement-to-release pipeline is the engine's primary flow.
- Each phase is demonstrated in this repository before it is considered complete.
