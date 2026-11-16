---
type: work
status: awaiting-approval
updated: 2026-11-16
---

# Phase 0: Foundation

> **Summary:** Research, the decisions that define Kanon, the conduct standard and this
> repository's layout. Restructured on 2026-11-16 at the owner's request.
> **Decision needed:** Approve the decisions and layout (R-1 in `kanon/REVIEW.md`).

## 1. Outputs

| Output | Location |
|---|---|
| Decision records ADR-001 to ADR-009 | `kanon/decisions/` |
| Conduct and writing standard | `kanon/docs/conduct-and-writing.md` |
| Learnings L-001 and L-002 | `kanon/docs/learnings.md` |
| Owner sources, verbatim | `kanon/sources.md` |
| Research and foundation plan (archived) | `kanon/archive/2026-11-13-research-and-foundation-plan.md` |
| Repository front matter | `README.md`, `AGENTS.md`, `CLAUDE.md`, `LICENSE` |
| Review list and status page | `kanon/REVIEW.md`, `kanon/STATUS.md` |

## 2. Key Findings

- **Upstream projects:** Koine-OS (method), Pinax (Git-native tracker), AutoBuild (build and
  blind review) and Ergasterion (pipeline generator, no AI model) are MIT-licensed and usable.
- **Approvals:** the assistant can forge a local approval (L-001). ADR-003 and ADR-007 respond.
- **Token usage:** Claude Code records per-message usage in its session logs, so cost can be
  reported per step.
- **Process weight:** the Koine-OS layout became slow to navigate (L-002). ADR-009 responds.

## 3. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-13 | Seven scope questions (Agora, Ergasterion, upstream, approval scope, assistant, stack, first user) | Recorded in ADR-001, 003, 004, 005; sources section 2 |
| 2026-11-13 to 15 | Engine and marketplace names | Kanon and Pantheon (ADR-006) |
| 2026-11-14 | How technical level is set | Setup question, adjusted with confirmation |
| 2026-11-14 | Writing rule strictness | Strict for documents, guidance in chat |
| 2026-11-16 | Layout, work files, records to drop, Phase 0 handling | One `kanon/` folder; one file per work; drop daily log, indexes, tags; restructure first |

## 4. Review

- **Independent review:** none. Kanon's reviewer is built in Phase 1. The owner may request a
  reviewer subagent before deciding.
- **Mechanical checks:** frontmatter, links, dashes and listed phrases pass on all files.

## 5. Decision

| Item | Decision | Date | Basis |
|---|---|---|---|
| Research and foundation plan, revision 4 | Approved | 2026-11-13 | Owner instruction "begin phase 0" (recorded by the assistant; confirmed by approving R-1) |
| Decisions and layout | Pending | | |

## 6. Cost

Session total measured 2026-11-15 (all research, planning and Phase 0), from the Claude Code session
log: 356,378 output tokens; 1,857,478 cache-write tokens; 53,902,041 cache-read tokens;
501 uncached input tokens. Not separated by step; per-step reporting starts in Phase 1.
