---
name: ADR-004 Human approval at major gates
description: A person approves requirements, plans, decisions, documentation of record, Pantheon changes and merges; minor outputs are reviewed by the AI reviewer only
type: decision
status: accepted (amendment awaiting owner approval)
date: 2026-11-13
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-004
  - Gates
  - Approval
  - D4
---

# ADR-004: Human approval at major gates

## Context

The original brief asked for explicit human approval after independent review. Koine-OS
requires human approval at stage boundaries, not on every output. Revision 1 asked which
the owner wanted.

## Decision

A person approves at **major gates**, shown the material clearly, and either approves or
requests changes. Major gates: refined requirements, plans, decision records, documentation
of record (features, builds, fixes), bringing in or changing Pantheon entries, and merges,
releases and deployments. **Minor outputs** (daily log, dashboard, INDEX files, ticket
status, drafts) are reviewed by the independent reviewer only and listed in a daily
summary. The split is configurable per project.

**Amendment (Phase 0, pending owner approval at the Phase 0 gate):** an approval recorded
inside the repository can be forged by the assistant, because the assistant can write files
and can obtain a terminal (see the first learning). Therefore:

1. A local approval is **tamper-evident, not tamper-proof**: it records the approver, the
   time and a hash of the exact material approved, so any later change invalidates it, and
   `kanon verify` reports it. Kanon does not claim more than this.
2. A **tamper-proof** approval needs an identity the assistant does not hold. In GitHub
   mode that is the owner's own GitHub review, which only works if Kanon acts on GitHub
   under a **separate identity** (ADR-009).

## Evidence

- Owner answer 4.
- Koine-OS `method/00-overview.md`, "Stop points".
- Probe on 2026-11-13 ([learning](../learnings/2026-11-13-local-approvals-can-be-forged.md)).

## Consequences

- Phase 1 builds `kanon approve` with a content hash and `kanon verify` checks it.
- Phase 1 tests what Claude Code permission rules can and cannot stop, and documents the
  residual risk rather than hiding it.
