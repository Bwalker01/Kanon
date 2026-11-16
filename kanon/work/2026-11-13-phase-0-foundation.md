---
type: work
status: complete
updated: 2026-11-16
---

# Phase 0: Foundation

> **Summary:** Research, the decisions that define Kanon, the conduct standard and this
> repository's layout. Restructured on 2026-11-16 at the owner's request.
> **Decision:** Approved by the owner on 2026-11-16 (R-1).

## 1. Plan

Outputs of Phase 0, as delivered.

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
| Research and foundation plan, revision 4 | Approved | 2026-11-13 | Owner instruction "begin phase 0" (transcribed by the assistant; confirmed by R-1) |
| Decisions ADR-001 to ADR-009, conduct standard and layout | Approved | 2026-11-16 | Owner in chat: "R-1: All 9 decisions approved". Transcribed by the assistant; applies to commit `314a276` |

## 6. Cost

| Measure | Value | Source |
|---|---|---|
| Output tokens | 174,241 | Session log, deduplicated by message |
| Cache writes / reads | 1,366,710 / 30,671,400 | Session log, deduplicated by message |
| Estimated cost | about $19.36 | Claude Code's own running estimate (`cost-state`), API-equivalent; subscription billing differs |

**Correction (2026-11-16):** figures recorded earlier (356,378 output tokens) double-counted
replies that the log splits across several entries. Corrected above.
