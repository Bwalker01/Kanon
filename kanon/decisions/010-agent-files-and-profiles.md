---
type: decision
status: accepted
updated: 2026-11-18
---

# ADR-010: Agent Files and Profiles

> **Decision:** Generated agent files are kept out of Git and rebuilt by `kanon sync`; personal profiles live outside every repository.
> **Status:** Accepted by the owner, 2026-11-18 (R-1). Supersedes parts of ADR-005 and ADR-009.

## Context

- Profiles in the committed `kanon/kanon.toml` collide in teams and publish personal data.
- Kanon edited `AGENTS.md` and `CLAUDE.md`, which projects may own and commit themselves.
- Design and evidence: `kanon/work/2026-11-17-agent-files-and-profiles.md`.

## Decision

- **Committed:** `kanon/` (the project record) and `kanon/kanon.toml` (shared settings; approvers by GitHub username).
- **Generated, ignored:** `.claude/rules/kanon.md`, `.claude/rules/kanon-person.md`, Kanon's skills and reviewer agent, listed in a marked `.gitignore` block.
- **Profiles:** `KANON_PROFILE` (JSON or TOML), `KANON_PROFILE_FILE`, or `~/.config/kanon/profile.toml`.
- **Never touched:** a project's own `AGENTS.md` and `CLAUDE.md`; `CLAUDE.local.md` is never created.

## Basis

- Owner request and approval (`kanon/sources.md`, section 10).
- Claude Code memory documentation, read 2026-11-17: rules files load alongside project files; `CLAUDE.local.md` suppresses `AGENTS.md`.

## Consequences

- ADR-005: `CLAUDE.md` no longer imports `AGENTS.md`; Kanon's instructions arrive through `.claude/rules/`.
- ADR-009: `AGENTS.md` and `CLAUDE.md` are not part of Kanon's layout.
- The conduct standard's profile location changed accordingly (2026-11-18).
- A fresh clone needs one `kanon sync`; assistants that read only `AGENTS.md` wait for Phase 5.
