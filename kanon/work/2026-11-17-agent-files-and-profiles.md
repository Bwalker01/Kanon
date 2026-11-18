---
type: work
status: in-progress
updated: 2026-11-18
---

# Agent Files and Profiles

> **Summary:** Keep every Kanon-generated agent file and every personal profile out of Git, so teams never overwrite each other and nothing personal is published.
> **Decision:** Design approved by the owner on 2026-11-18 (R-1). Build in progress.

## 1. Plan

| Field | Value |
|---|---|
| Output | ADR-010; `kanon sync`; profile store; changes to `kanon init`, templates and this repository |
| Inputs | Owner request (`kanon/sources.md`, section 10); Claude Code memory documentation (2026-11-17) |
| Acceptance | See section 1.4 |
| Creator | Claude Code (builder session) |
| Reviewer | Kritos (independent subagent) |
| Group round limit | 2 (owner, 2026-11-16) |

### 1.1 Problem

- `kanon/kanon.toml` holds each person's profile and is committed. In a team, profiles collide on push; in a public repository, they are published.
- Kanon writes `AGENTS.md`, `CLAUDE.md` and `.claude/` files that are committed. In a project with its own instruction files, Kanon would be editing files the team owns.
- The upstream author removed his own agent instructions from four public repositories on 2026-09-01 ("keep owner agent instructions private"), the same risk.

### 1.2 Evidence (Claude Code memory documentation, read 2026-11-17)

| Fact | Consequence |
|---|---|
| `.claude/rules/*.md` files load automatically, alongside `CLAUDE.md` and `AGENTS.md` | Kanon can deliver its instructions without touching a team's own files |
| A `CLAUDE.local.md` stops Claude Code reading `AGENTS.md` unless imported | Kanon must not create `CLAUDE.local.md` |
| `~/.claude/CLAUDE.md` and `~/.claude/rules/` hold personal instructions for all projects | Personal settings belong outside the repository |
| Imports from outside the project require a one-time approval | Kanon writes content into the project instead of importing from the home folder |

### 1.3 Design

| Kind | Location | In Git | Written by |
|---|---|---|---|
| Project record: decisions, work, docs, roles, conduct standard, `REVIEW.md`, `STATUS.md`, sources | `kanon/` | Yes | Agents and people, through the loop |
| Shared settings: round limit, exceptions, approvers by GitHub username | `kanon/kanon.toml` | Yes | People, by decision |
| Kanon's agent instructions, rendered for this assistant | `.claude/rules/kanon.md` | No | `kanon sync` |
| The person's instructions, rendered from their profile | `.claude/rules/kanon-person.md` | No | `kanon sync` |
| Kanon's skills and reviewer agent | `.claude/skills/kanon-*`, `.claude/agents/kritos-reviewer.md` | No | `kanon sync` |
| Personal profile: level, preferences, name | `~/.config/kanon/profile.toml`, or the `KANON_PROFILE` environment variable | Never | The person, once |

- **`kanon sync`** regenerates every ignored file from the installed package, `kanon/kanon.toml` and the profile. It is safe to run at any time and runs after `kanon init`.
- **`.gitignore`** gets a marked Kanon block listing exactly the generated paths. Kanon never ignores or edits a project's own `AGENTS.md` or `CLAUDE.md`.
- **Profiles** live outside every repository, so they apply to all of a person's projects and never collide. In cloud sessions, which start from a fresh copy, the profile comes from the `KANON_PROFILE` environment variable set once in the cloud environment, and the environment's setup script runs `kanon sync`.
- **Approvers** are listed in `kanon/kanon.toml` by GitHub username only; this is public information and each person is one line, so merges rarely conflict.

### 1.4 Acceptance

| Check | A wrong result fails because |
|---|---|
| After `kanon init` and `kanon sync`, `git status` shows no generated agent file as untracked | Any generated file outside the ignore block appears |
| Two clones with different profiles commit and merge with no conflict and no profile in history | A profile in any committed file is found by a history search |
| A project's existing `AGENTS.md` and `CLAUDE.md` are byte-identical after init and sync | Any change to them fails a checksum |
| No `CLAUDE.local.md` is ever created | A test asserts its absence |
| A fresh clone plus `kanon sync` reproduces the generated files exactly | Byte comparison with the original clone |
| `KANON_PROFILE` takes precedence over the profile file; with neither, agents ask at first contact | Tests for each source |

### 1.5 This Repository

- Untrack `AGENTS.md`, `CLAUDE.md` and `.claude/`; they become generated. Developer notes move to `CONTRIBUTING.md`.
- The owner's profile moves to the cloud environment's `KANON_PROFILE` variable; the environment setup script installs Kanon and runs `kanon sync`. Both changes need the owner's approval in the environment prompt.

### 1.6 Limits

- **Fresh clones** have no agent instructions until `kanon sync` runs once. Mitigated by the cloud setup script and a line in `README.md`; a person cloning locally runs it once.
- **Other assistants** that read only `AGENTS.md` (Codex, Copilot) receive nothing until Phase 5 adds a generator for them.

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-17 | Where should personal profiles live? | Out of Git, for every user, including in live team environments; all agent files ignored |
| 2026-11-17 | Split agent instructions into the owner's and Kanon's standard? | Yes |
| 2026-11-18 | Earlier commits hold the owner's old profile: accept or rewrite history? (K-64) | Rewrite the branch history |

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| 1 | Build and migration | Kritos (`kritos-reviewer` agent) | correct | K-56, K-57, K-58 | K-56, K-57, K-59 to K-63, K-68, K-69 fixed; K-64 to the owner |
| 2 | Round 1 fixes | Kritos (`kritos-reviewer` agent) | correct | K-70 | K-70: the round 1 record wrongly listed K-58, K-65 and K-66 as fixed (edits lost in a worker restart, then recorded without checking the commit). All three, K-72 and K-74 to K-76 fixed after the final round; not independently reviewed. Owner decides at the review point |

**Deviation from the plan (K-67):** cloud setup scripts cannot read the environment's saved
variables, so the owner's profile is written by the setup script with `kanon profile` instead of
coming from `KANON_PROFILE`. Both keep the profile outside the repository.

## 4. Decision

| Item | Decision | Date | Basis |
|---|---|---|---|
| Design | Approved | 2026-11-18 | Owner in chat: "R-1 approve". Transcribed by the assistant; applies to commit `68c10e8` |

## 5. Cost

Recorded when work starts.
