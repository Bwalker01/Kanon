---
name: ADR-006 Python 3.11+ and the MIT licence
description: Kanon is written in Python 3.11 or later and released under the MIT licence
type: decision
status: accepted
date: 2026-11-13
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-006
  - Language
  - Licence
  - D6
---

# ADR-006: Python 3.11+ and the MIT licence

## Context

Revision 1 proposed Python 3.11+ and MIT, and asked the owner to confirm.

## Decision

Kanon is a Python package (`kanon-engine` on PyPI, command `kanon`) for Python 3.11 or
later, released under the MIT licence.

## Evidence

- Owner answer 6.
- Pinax requires Python 3.10+ and AutoBuild 3.11+ (`pyproject.toml` of each), so Kanon can
  import both directly.
- All four upstream projects are MIT-licensed.

## Consequences

- `LICENSE` added at the repository root in Phase 0.
- Package and command names come from ADR-008.
