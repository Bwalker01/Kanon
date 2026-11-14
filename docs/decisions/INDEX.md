---
name: Decisions index
description: Every decision record for Kanon, one line each
type: index
tags:
  - type/index
  - project/kanon
aliases:
  - Decisions
  - ADRs
---

# Decisions

A decision record is never edited to change its meaning. A changed decision gets a new
record that supersedes the old one, and the old one moves to `docs/archive/`.

| Record | Decision | Summary |
|---|---|---|
| [ADR-001](ADR-001-agora-background.md) | Agora is background only | The original idea, Agora, sets no requirements for Kanon |
| [ADR-002](ADR-002-scope-requirements-to-code.md) | Scope: from requirements to working code | Kanon refines requirements, creates tickets and calls specialists and tools to produce working output, in every domain |
| [ADR-003](ADR-003-pantheon-central-marketplace.md) | Pantheon: one central marketplace | Agents and tools live in one central Git-based marketplace that accepts submissions and from which every Kanon instance pulls what it needs |
| [ADR-004](ADR-004-human-approval-at-major-gates.md) | Human approval at major gates | A person approves requirements, plans, decisions, documentation of record, Pantheon changes and merges; minor outputs are reviewed by the AI reviewer only |
| [ADR-005](ADR-005-claude-code-first.md) | Claude Code first, any assistant in principle | Claude Code is the first and only tested assistant until Phase 3; everything else stays assistant-neutral |
| [ADR-006](ADR-006-python-and-mit.md) | Python 3.11+ and the MIT licence | Kanon is written in Python 3.11 or later and released under the MIT licence |
| [ADR-007](ADR-007-prove-on-itself-first.md) | Prove Kanon on itself first | This repository is Kanon instance number one; an outside project comes once the core works |
| [ADR-008](ADR-008-names-kanon-and-pantheon.md) | Names: Kanon and the Pantheon | The engine is Kanon and the marketplace is the Pantheon, following Koine's Greek naming convention |
| [ADR-009](ADR-009-optional-github-mode-and-cost.md) | Optional GitHub mode, and a cost-conscious loop | GitHub Projects, branches and pull requests are an optional layer over the repository; the loop spends tokens and Actions minutes only where they earn their place |
| [ADR-010](ADR-010-koine-loop-and-disciplines.md) | Follow the Koine Loop and Koine-OS disciplines | Every significant output goes through plan, create, independent review and adjust, and the repository follows Koine-OS's knowledge disciplines |
| [ADR-011](ADR-011-agent-conduct-and-writing.md) | Agent conduct and writing | Agents ask early, push back, stay realistic, match each person's technical level and write without AI-writing patterns |
