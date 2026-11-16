---
type: decision
status: proposed
updated: 2026-11-16
---

# ADR-005: Assistants and Technology

> **Decision:** Claude Code is supported first; the method stays assistant-neutral. Kanon is a Python 3.11+ package under the MIT licence.
> **Status:** Proposed. Awaiting owner approval (see `kanon/REVIEW.md`).

## Context

- The brief requires the engine to work with whichever AI assistant is connected.
- Pinax requires Python 3.10+ and AutoBuild 3.11+; all upstream projects are MIT-licensed.

## Decision

- **First assistant:** Claude Code. Others are added through thin adapters, never a second copy of the method.
- **Root instructions:** `AGENTS.md`, read by most coding agents; `CLAUDE.md` imports it.
- **Package:** `kanon-engine` on PyPI, command `kanon`, Python 3.11+, managed with `uv`.
- **Licence:** MIT.

## Basis

- Owner answers 5 and 6; `uv` by default (2026-11-14).
- Koine-OS adapter guidance: wrappers of at most 30 lines.
- AGENTS.md convention (`agentsmd/agents.md`).

## Consequences

- Kanon can import Pinax and AutoBuild directly.
- Support for other assistants is scheduled for Phase 5.
