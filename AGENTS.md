# Kanon: instructions for AI agents

This repository builds **Kanon**, and is also Kanon's first instance: it is developed with
its own method. Read this file first, then [the dashboard](docs/status/dashboard.md).

## Where things are

- `docs/INDEX.md`: map of all documentation. Use INDEX files and frontmatter
  `description` fields to find what you need before opening full documents.
- `docs/status/dashboard.md`: current state. Read it at the start of every session.
- `docs/decisions/`: decision records. They are the source of truth for decisions.
- `docs/sources/`: raw material. Do not work from it directly; work from what it was
  compiled into.
- `plans/YYYY-MM-DD-topic/`: one folder per piece of work, holding its plan, drafts,
  reviews and approvals.

## Rules

1. **Plan before producing.** Write `plans/<date>-<topic>/plan.md` naming the output, its
   inputs, its reviewer and where it will go, before creating anything significant.
2. **Write outputs to files, not chat.** Drafts are `draft-v1.md`, `draft-v2.md`; never
   overwrite a draft.
3. **Never review your own output.** Review is done by a separate reviewer with its own
   instructions and no access to the creator's conversation.
4. **Never record an approval.** Only the owner approves major gates (ADR-004). Prepare a
   `gate.md` summary and stop.
5. **Archive, never delete.** Superseded files move to `docs/archive/` with a note saying
   when, why and what replaced them.
6. **Frontmatter on every document:** `name`, `description`, `type`, `tags`, `aliases`.
   List every new document in its folder's `INDEX.md`.
7. **Commit messages start with ADDED, MODIFIED or REMOVED** and give a one-line reason.
8. **Append to `docs/daily/<today>.md`** what was done; never edit earlier entries.
9. **Ask, do not guess.** If information is missing, stop and ask the owner.
10. **Be economical.** Read summaries before full files; run free checks before asking for
    a model review; do not repeat a check on unchanged material.
