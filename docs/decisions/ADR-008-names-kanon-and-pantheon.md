---
name: ADR-008 Names: Kanon and the Pantheon
description: The engine is Kanon and the marketplace is the Pantheon, following Koine's Greek naming convention
type: decision
status: accepted
date: 2026-11-13
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-008
  - Naming
  - D8
---

# ADR-008: Names: Kanon and the Pantheon

## Context

The working name Mercatus is Latin and itself means "marketplace". The owner asked for
names in Koine's Greek convention: a fitting name for a marketplace of mythology-named
agents and tools, and an engine name that is a common ancient Greek word, at most six
letters, easy to spell and say, close to the project's purpose.

## Decision

- **Engine: Kanon** (κανών): a measuring rod; a rule or standard; the root of "canon", the
  agreed body of authoritative texts. Package `kanon-engine`, command `kanon`.
- **Marketplace: Pantheon**, a Git repository named `pantheon`.
- **Pantheon agents** carry a mythological name and a plain role, shown together
  (for example "Kritos, reviewer"); names come first from Koine's twelve archetypes. Tools
  keep their upstream names.

## Evidence

- Owner choices ([owner brief](../sources/2026-11-13-owner-brief.md), section 3).
- PyPI and GitHub checks on 2026-11-13, recorded in the foundation plan, section 11:
  `kanon` is taken on PyPI and `kanon-engine` is free; about 1,200 GitHub repositories use
  the name, the largest with 71 stars, none notable in AI agents.
- Koine-OS calls a specification "a measurement surface" (`method/the-koine-loop.md`).
- Pattern of a suffixed package with a short command: `pinax-tracker` and
  `ergasterion-factory`.

## Consequences

- The GitHub repository is still `Bwalker01/Mercatus`; only the owner can rename it.
- Some people may type "canon"; documentation spells the name out where it matters.
