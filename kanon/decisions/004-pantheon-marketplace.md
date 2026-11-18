---
type: decision
status: accepted
updated: 2026-11-16
---

# ADR-004: Pantheon Marketplace

> **Decision:** Agents and tools are held in one central Git-based marketplace, the Pantheon, which accepts submissions and from which projects pull what they need.
> **Status:** Accepted by the owner, 2026-11-16 (R-1).

## Context

- The owner asked for a central marketplace with simple submission and on-demand retrieval.
- Pinax, AutoBuild and Ergasterion are MIT-licensed and published on PyPI.

## Decision

- **Repository:** `pantheon`, public, Git-based.
- **Entries:** agents (instructions with a paired reviewer, in Agent Skills format) and tools (install command, health check, permissions).
- **Submission:** pull request, automatic checks, independent AI review, maintainer approval.
- **Adoption:** proposed by the coordinator, approved by the owner, copied in at a pinned version and hash recorded in `kanon.lock`.
- **Antikas's projects** enter as tools pointing at their PyPI releases, with credit.

## Basis

- Owner answer 3.
- Claude Code plugin marketplaces are Git repositories with a catalogue file: a working precedent.
- Agent Skills specification (`agentskills/agentskills`).

## Consequences

- The `pantheon` repository is required by Phase 4.
- Pinned copies keep projects working when the marketplace changes.
