---
name: Phase 0 plan
description: What Phase 0 produces, who reviews it, and the gate it ends at
type: plan
status: complete-awaiting-gate
date: 2026-11-13
tags:
  - type/plan
  - project/kanon
  - stage/phase-0
aliases:
  - Phase 0
---

# Phase 0: foundation

**Source:** [foundation plan](../2026-11-13-kanon-foundation/plan.md), section 10, Phase 0.
**Started by:** the owner ("begin phase 0", 2026-11-13).

## What Phase 0 produces

| Output | Path | Gate type |
|---|---|---|
| Record of the owner's approval of the foundation plan | `plans/2026-11-13-kanon-foundation/approval.md` | Record |
| The owner's original brief and answers, verbatim | `docs/sources/2026-11-13-owner-brief.md` | Source (not reviewed) |
| Decision records ADR-001 to ADR-010 (owner decisions D1 to D9, plus the Koine Loop from the original brief) | `docs/decisions/` | **Major: decisions** |
| This repository laid out as Kanon instance number one | `AGENTS.md`, `CLAUDE.md`, `README.md`, `LICENSE`, `docs/**`, `plans/INDEX.md` | **Major: documentation of record** |
| First learning (approval forgery probe) | `docs/learnings/` | Minor |
| Phase 1 slice plan | `plans/2026-11-13-phase-1-context-loop-gates/plan.md` | **Major: plan** |
| Gate summary for the owner | `plans/2026-11-13-phase-0-foundation/gate.md` | The gate |

## Who produces and who reviews

- **Producer:** Claude Code (this session), acting as coordinator and scribe.
- **Independent review:** none in Phase 0. Kanon's reviewer does not exist until Phase 1,
  and this session does not start subagents unless the owner asks. The gate says so
  plainly instead of presenting a self-check as a review (Koine anti-pattern: "letting the
  generator self-review"). The owner can ask for an independent reviewer pass before
  approving.
- **Approval:** the owner, at the Phase 0 gate.

## Stop point

Phase 0 ends at `gate.md`. Nothing in Phase 1 starts until the owner approves.
