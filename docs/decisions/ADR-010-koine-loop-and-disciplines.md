---
name: ADR-010 Follow the Koine Loop and Koine-OS disciplines
description: Every significant output goes through plan, create, independent review and adjust, and the repository follows Koine-OS's knowledge disciplines
type: decision
status: accepted
date: 2026-11-13
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-010
  - Koine Loop
  - Disciplines
---

# ADR-010: Follow the Koine Loop and Koine-OS disciplines

## Context

The original brief asked that the engine "follow the Koine loop, as defined in Antikas'
koine-os project", with documentation at its heart.

## Decision

- **The loop:** specify and plan first; create; an independent reviewer with a different
  prompt and no access to the creator's transcript reviews against the specification;
  adjust into a new file; at most three rounds before a person decides. Every iteration is
  committed under `plans/YYYY-MM-DD-topic/`.
- **Every generator ships with a paired reviewer.**
- **Knowledge disciplines:** single source of truth; archive, never delete; ADDED, MODIFIED
  or REMOVED in commit messages; required frontmatter (`name`, `description`, `type`,
  `tags`, `aliases`); append-only daily log; INDEX.md drill-down; status dashboard read
  first; learnings as first-class content; a sources inbox compiled before use; forcing
  functions; intent kept separate from readiness.
- Koine-OS is adopted the way it asks to be adopted: as a copied method, credited, not as a
  dependency.

## Evidence

- Original brief ([owner brief](../sources/2026-11-13-owner-brief.md), section 1).
- Koine-OS `method/the-koine-loop.md`, `method/knowledge-discipline.md`, `README.md`
  ("the supported model is ownership of a copy").

## Consequences

- This repository follows the disciplines from Phase 0.
- `kanon verify` (Phase 1) checks the loop and the disciplines mechanically, which Koine's
  own Claude Code adapter says it cannot do.
