---
name: ADR-003 Pantheon: one central marketplace
description: Agents and tools live in one central Git-based marketplace that accepts submissions and from which every Kanon instance pulls what it needs
type: decision
status: accepted
date: 2026-11-13
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-003
  - Pantheon
  - Marketplace
  - D3
---

# ADR-003: Pantheon: one central marketplace

## Context

Revision 1 asked how Kanon should include Antikas's projects (Pinax, AutoBuild,
Ergasterion): as dependencies, forks, or upstream collaboration.

## Decision

There is one central marketplace, the **Pantheon**, a public Git repository. New agents
and tools are submitted by pull request; each submission passes automatic checks, an
independent AI review, and a human maintainer's approval. Kanon instances search it and
pull entries in when a project needs them, at a pinned version recorded in `kanon.lock`.
Antikas's projects enter as Pantheon **tools** pointing at their PyPI releases, with credit.

## Evidence

- Owner answer 3.
- Claude Code plugin marketplaces are Git repositories with a catalogue file (foundation
  plan, section 14), a working precedent for a Git-hosted catalogue.
- Pinax, AutoBuild and Ergasterion are MIT-licensed (their `LICENSE` files).

## Consequences

- A second repository, `pantheon`, is needed by Phase 4.
- Bringing an entry into a project is a major gate (ADR-004).
- Copies are pinned and hashed, so projects keep working if the Pantheon changes.
