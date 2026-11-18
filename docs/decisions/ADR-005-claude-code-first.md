---
name: ADR-005 Claude Code first, any assistant in principle
description: Claude Code is the first and only tested assistant until Phase 3; everything else stays assistant-neutral
type: decision
status: accepted
date: 2026-11-13
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-005
  - Claude Code
  - Assistants
  - D5
---

# ADR-005: Claude Code first, any assistant in principle

## Context

The brief asked for an engine that works "through whatever AI model is connected to it".
Revision 1 asked which assistant to support first.

## Decision

Claude Code is supported first. The method lives in plain files and the `kanon` command,
with `AGENTS.md` as the root context and thin assistant-specific wrappers, so another
assistant needs an adapter, never a second copy of the method.

## Evidence

- Owner answer 5.
- Koine-OS `adapters/claude-code/README.md`: thin wrappers of at most 30 lines pointing at
  neutral prompts.
- AGENTS.md is read by many coding agents; the nearest file in the directory tree takes
  precedence (`agentsmd/agents.md`).
- AutoBuild runs one contract through Claude Code, Codex and Copilot adapters.

## Consequences

- `CLAUDE.md` in every instance points at `AGENTS.md` rather than repeating it.
- Other assistants are added when someone needs them (Phase 5).
