# Kanon

This project uses Kanon. At the start of every session, read `kanon/STATUS.md` and
`kanon/REVIEW.md`. The person's instructions are in `.claude/rules/kanon-person.md`.

| Path | Contents |
|---|---|
| `kanon/REVIEW.md` | Items awaiting the owner's decision. Nothing else. |
| `kanon/STATUS.md` | Work in progress, recent changes. |
| `kanon/decisions/` | Decision records. The source of truth for decisions. |
| `kanon/work/` | One file per piece of work: Summary, Plan, Questions, Review, Decision, Cost. |
| `kanon/docs/` | Standards, role prompts, learnings and documentation of record. |
| `kanon/archive/` | Superseded documents with reference value. |

Roles, in `kanon/docs/roles/`: Metis coordinates (skill `kanon-metis`), Kritos reviews
(subagent `kritos-reviewer`), Clio records (skill `kanon-clio`), Mnemon keeps context
(skill `kanon-mnemon`).

## Rules

1. **Plan first.** Create the work file with `kanon new`, fill its Plan, and commit it on its own before producing anything significant.
2. **Ask early.** Ask when information is missing; record the question and answer in the work file.
3. **Challenge.** Raise flaws, costs and simpler options before acting, with evidence. The person decides.
4. **No self-review.** A separate reviewer, without access to the creator's conversation, reviews all output.
5. **No self-approval.** Add the item to `kanon/REVIEW.md` and stop. Only an approver listed in `kanon/kanon.toml` approves.
6. **Open review material** for the person when requesting a decision, in the assistant's file viewer.
7. **One file per piece of work.** Revise in place; Git holds earlier versions.
8. **Run `kanon verify`** before committing.
9. **Commit messages** start with ADDED, MODIFIED or REMOVED and give a one-line reason.
10. **Be economical.** Read summaries before full files; run free checks before model reviews.
11. **Never commit personal data.** Profiles stay outside the repository. Generated agent files are listed in the Kanon block of `.gitignore`; `kanon sync` rebuilds them.

## Conduct and Writing Standard

The project's standard, from `kanon/docs/conduct-and-writing.md`, follows in full.

$conduct
