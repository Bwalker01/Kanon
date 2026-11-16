<!-- kanon:start -->
## Kanon

This project uses Kanon. At the start of every session, read `kanon/STATUS.md` and
`kanon/REVIEW.md`, and each person's profile in `kanon/kanon.toml`.

| Path | Contents |
|---|---|
| `kanon/REVIEW.md` | Items awaiting the owner's decision. Nothing else. |
| `kanon/STATUS.md` | Work in progress, recent changes. |
| `kanon/decisions/` | Decision records. The source of truth for decisions. |
| `kanon/work/` | One file per piece of work: Summary, Plan, Questions, Review, Decision, Cost. |
| `kanon/docs/` | Standards, learnings and documentation of record. |
| `kanon/archive/` | Superseded documents with reference value. |

Follow `kanon/docs/conduct-and-writing.md` in chat and documents. Pitch explanations at the
level in each person's profile.

1. **Plan first.** Create the work file with its Plan section before producing anything significant.
2. **Ask early.** Ask when information is missing; record the question and answer in the work file.
3. **Challenge.** Raise flaws, costs and simpler options before acting, with evidence. The person decides.
4. **No self-review.** A separate reviewer, without access to the creator's conversation, reviews all output.
5. **No self-approval.** Add the item to `kanon/REVIEW.md` and stop. Only the owner approves.
6. **Open review material** for the owner when requesting a decision.
7. **One file per piece of work.** Revise in place; Git holds earlier versions.
8. **Run `kanon verify`** before committing.
9. **Commit messages** start with ADDED, MODIFIED or REMOVED and give a one-line reason.
10. **Be economical.** Read summaries before full files; run free checks before model reviews.
<!-- kanon:end -->
