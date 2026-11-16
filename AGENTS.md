# Kanon: Agent Instructions

This repository builds Kanon and is its first instance. At the start of every session, read
`kanon/STATUS.md` and `kanon/REVIEW.md`.

## Layout

| Path | Contents |
|---|---|
| `kanon/REVIEW.md` | Items awaiting the owner's decision. Nothing else. |
| `kanon/STATUS.md` | Phases, recent changes, register. |
| `kanon/decisions/` | Decision records. The source of truth for decisions. |
| `kanon/work/` | One file per piece of work: Summary, Plan, Questions, Review, Decision, Cost. |
| `kanon/docs/` | Standards, learnings and documentation of record. |
| `kanon/sources.md` | The owner's words, verbatim. Reference only; work from the decisions. |
| `kanon/archive/` | Superseded documents with reference value. |

## Working With the Owner

Pitch explanations at the level in each person's profile. Follow `kanon/docs/conduct-and-writing.md` in chat and documents.

- **Ask early.** Ask when information is missing, before building on assumptions. Record the
  question and answer in the work file.
- **Challenge.** Raise flaws, costs and simpler options before acting, with evidence. The
  owner decides.
- **Be realistic.** Separate tested results from expectations.
- **Keep chat short.** Point to `kanon/REVIEW.md` or a specific section; do not restate documents.

## Rules

1. **Plan first.** Create the work file with its Plan section before producing anything significant.
2. **One file per piece of work.** Revise in place; Git holds earlier versions.
3. **No self-review.** Reviews are performed by a separate reviewer without access to the creator's conversation.
4. **No self-approval.** Add the item to `kanon/REVIEW.md` and stop. Only the owner approves (ADR-003).
5. **Open review material.** When requesting a decision, open `kanon/REVIEW.md` and the files it names, from their current paths, rendered for reading.
6. **Document layout.** Frontmatter (`type`, `status`, `updated`), a title, a summary block of at most three lines, short sections, tables over prose. Formal, professional tone.
7. **Writing checks.** No em or en dashes; none of the phrases or patterns listed in the conduct standard.
8. **Update `kanon/STATUS.md`** with significant changes.
9. **Commit messages** start with ADDED, MODIFIED or REMOVED and give a one-line reason.
10. **Be economical.** Read summaries before full files; run free checks before model reviews; do not repeat checks on unchanged material.
