---
type: decision
status: proposed
updated: 2026-11-19
---

# ADR-013: Recorded Approvals

> **Decision:** An approval counts when the approver runs `kanon approve`, or when the assistant records the approver's exact chat words with `kanon transcribe`. Both are hashed and labelled.
> **Status:** Proposed, 2026-11-19; the owner decides at the group C review point. Amends ADR-003.

## Context

- ADR-003 says the assistant never records an approval. In cloud sessions the owner has no terminal, so every approval so far was a chat reply transcribed by the assistant.
- Local records cannot prove who made them (L-001); a separate identity makes them tamper-proof (ADR-007, P1-10).

## Decision

- **Forms:** "approved by" (the approver ran `kanon approve`) and "transcribed" (the assistant ran `kanon transcribe --quote` with the approver's words). Each Decision row names its form.
- **Material:** the work file without its frontmatter, summary block, Actions, Decision and Cost sections; up to the Plan for a plan approval, up to the Review for a result. An item approval (`--item P1-05`) covers only that item's Work Items row, Plan subsections naming it and Review rows naming it, and leaves the status alone (owner, K-340). The row records its SHA-256 and the commit.
- **Checks:** `kanon verify` fails when the latest approval of each plan, result or item no longer matches its hash, when a recorded approval's hash is missing or malformed, names an approver missing from `approvers`, or, for complete work, has no hash and is dated after 2026-11-19.
- **Refusals:** `kanon sync` writes Claude Code deny rules for `kanon approve`, `kanon request-changes` and edits to `kanon/kanon.toml`; both commands also refuse when `CLAUDECODE` is set. The guard blocks project writes by `kritos-reviewer` (K-29).

## Basis

- Owner answer, 2026-11-19: both forms count, labelled (`kanon/work/2026-11-16-phase-1-plan.md`, Questions).
- Tested in this session on 2026-11-19: `kanon approve` was refused by the deny rule; the hook input names the subagent (`agent_type`).

## Consequences

- Remaining bypasses, all tamper-evident only: file edits through the shell (including of `.claude/settings.local.json`, which holds the deny rules), running Kanon with `CLAUDECODE` unset, a forged transcription, a forged hashless row dated on or before 2026-11-19, and reviewer writes made by programs a command starts or through variables the guard cannot resolve.
- The edit deny rules were written but not exercised live; tests confirm they are written.
