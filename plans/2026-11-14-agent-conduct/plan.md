---
name: Agent conduct and writing plan
description: Make how agents talk, ask, push back, adapt to the user and write part of Kanon's basis, starting with this repository's own instructions
type: plan
status: complete-awaiting-gate
date: 2026-11-14
tags:
  - type/plan
  - project/kanon
  - topic/conduct
aliases:
  - Agent conduct
---

# Agent conduct and writing

**Asked for by:** the owner, 2026-11-14 (saved in `docs/sources/2026-11-14-owner-conduct-request.md`).

## Outputs

| Output | Path | Gate |
|---|---|---|
| The owner's request, verbatim | `docs/sources/2026-11-14-owner-conduct-request.md` | Source |
| This repository's agent instructions, rewritten to the new standard | `AGENTS.md` | Owner asked for it directly; confirmed at the Phase 0 gate |
| The conduct and writing standard, which every Kanon agent follows | `docs/standards/conduct-and-writing.md` | **Major: documentation of record** |
| Decision record | `docs/decisions/ADR-011-agent-conduct-and-writing.md` | **Major: decision** |
| Phase 1 plan changes so the engine builds it in | `plans/2026-11-13-phase-1-context-loop-gates/plan.md` | **Major: plan** |

## Inputs

The owner's request; Koine-OS `prompts/reviewers/writing-quality-reviewer.md` (AI-writing
fingerprints, practitioner voice, earned claims); the owner's answers to the questions
asked during this work.

## Review

No independent reviewer exists yet (Phase 1). The free mechanical checks (frontmatter,
links, dashes, banned phrases) run on every changed file. The owner reviews at the gate.

## Questions asked before building, not after

How Kanon learns each person's technical level; how strict the writing rules are; whether
this joins the Phase 0 gate.
