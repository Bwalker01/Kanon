# Kanon: instructions for AI agents

This repository builds **Kanon**, and is also Kanon's first instance, so it is developed
with its own method. Read this file first, then [the dashboard](docs/status/dashboard.md).

## Where things are

- `docs/INDEX.md`: map of all documentation. Use INDEX files and frontmatter
  `description` fields to find what you need before opening full documents.
- `docs/status/dashboard.md`: current state. Read it at the start of every session.
- `docs/decisions/`: decision records. They are the source of truth for decisions.
- `docs/standards/conduct-and-writing.md`: how to work with people and how to write.
  Follow it in chat and in every document.
- `docs/sources/`: raw material. Do not work from it directly; work from what it was
  compiled into.
- `plans/YYYY-MM-DD-topic/`: one folder per piece of work, holding its plan, drafts,
  reviews and approvals.

## Working with the owner

Pitch explanations at the level in each person's profile.

- **Ask early.** When something you need is missing or ambiguous, ask as soon as you hit
  it, before building on a guess. Group questions that arrive together; do not hold them
  all for the gate. Do not ask what you can find out yourself.
- **Make questions answerable.** One decision per question, the options, your
  recommendation and why, and what happens by default.
- **Push back.** If a request has a flaw, a cheaper route, or a cost the owner may not
  have seen, say so plainly before doing it, with the evidence. Then do what the owner
  decides.
- **Be realistic.** Say what will not work, what is uncertain and what is untested. Never
  promise what a check cannot guarantee.
- **Talk like a colleague.** Plain, direct and friendly. Short where short will do. No
  flattery, no filler, no apologising for things that need no apology.

## Rules

1. **Plan before producing.** Write `plans/<date>-<topic>/plan.md` naming the output, its
   inputs, its reviewer and where it will go, before creating anything significant.
2. **Write outputs to files, not chat.** Drafts are `draft-v1.md`, `draft-v2.md`; never
   overwrite a draft.
3. **Never review your own output.** Review is done by a separate reviewer with its own
   instructions and no access to the creator's conversation.
4. **Never record an approval.** Only the owner approves major gates (ADR-004). Prepare a
   `gate.md` summary and stop.
5. **Open everything the owner needs at a gate.** When asking for approval, send
   `gate.md` and every file it asks the owner to approve or links to, rendered for
   reading in the owner's app (in Claude Code: send them as rendered files). Send files
   from their current paths, never from paths that have since moved.
6. **Write like a person.** Follow the writing rules in
   `docs/standards/conduct-and-writing.md`: no em or en dashes, none of the listed
   AI-writing patterns, varied sentences, concrete claims with their source.
7. **Archive, never delete.** Superseded files move to `docs/archive/` with a note saying
   when, why and what replaced them.
8. **Frontmatter on every document:** `name`, `description`, `type`, `tags`, `aliases`.
   List every new document in its folder's `INDEX.md`.
9. **Commit messages start with ADDED, MODIFIED or REMOVED** and give a one-line reason.
10. **Append to `docs/daily/<today>.md`** what was done; never edit earlier entries.
11. **Be economical.** Read summaries before full files; run free checks before asking for
    a model review; do not repeat a check on unchanged material.
