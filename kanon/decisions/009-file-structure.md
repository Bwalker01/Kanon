---
type: decision
status: accepted
updated: 2026-11-16
---

# ADR-009: File Structure

> **Decision:** All Kanon files live in one `kanon/` folder, each piece of work is a single file, and records that duplicate Git history are not kept.
> **Status:** Accepted by the owner, 2026-11-16 (R-1).

## Context

- The owner found the Koine-OS layout slow to navigate: too many folders and files, and no single place showing what needs review.
- Kanon is added to other projects' repositories, so it must not spread folders across their root.

## Decision

- **Layout:** `kanon/REVIEW.md`, `kanon/STATUS.md`, `kanon/sources.md`, and folders `decisions/`, `work/`, `docs/`, `archive/`. `AGENTS.md` and `CLAUDE.md` stay at the root so assistants find them.
- **Work files:** one per piece of work, with sections Summary, Plan, Questions, Review, Decision and Cost. Earlier versions live in Git history.
- **Not kept:** draft files, daily logs, per-folder indexes (unless a folder exceeds about ten files), tags and aliases.
- **Frontmatter:** `type`, `status`, `updated`.
- **Archive:** only superseded documents with lasting reference value; everything else relies on Git history.

## Basis

- Owner request and choices (`kanon/sources.md`, section 7).
- Koine-OS minimum viable OS: "three to five" skills, not thirty.

## Consequences

- Departs from Koine-OS conventions on drafts, daily logs and indexes. ADR-002 retains the loop itself.
- `kanon init` creates this layout from Phase 1.
- `AGENTS.md` and `CLAUDE.md` superseded by ADR-010: they are not part of Kanon's layout.
