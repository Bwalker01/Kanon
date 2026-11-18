---
type: learnings
status: current
updated: 2026-11-18
---

# Learnings

> **Summary:** Lessons from building and using Kanon that apply beyond the task that produced
> them. Newest first.

## L-004: Cleanup Commands Must Name What They Delete (2026-11-18)

- **Finding:** A reviewer's cleanup loop deleted every folder that `find /tmp -maxdepth 1 -name 'tmp*'` returned. `find` returns its own starting folder, and `/tmp` matched `tmp*`, so all of `/tmp` was deleted, including the session's commit-signing helper. Commits failed for the rest of the container's life.
- **Cause:** Cleanup by pattern instead of by exact path, allowed by a reviewer prompt that said only "remove them".
- **Rule:** Delete only paths you created, by exact path. The Kanon guard hook blocks deletions of shared locations for every agent, subagents included (`kanon/work/2026-11-18-destructive-command-guard.md`).

## L-003: Record Only What Is Committed (2026-11-18)

- **Finding:** A review record listed three fixes as done; the commit held none of them.
- **Cause:** Edits were lost in a worker restart before being committed, and the record was written from memory rather than from the commit.
- **Rule:** Commit immediately after each change, and write review records from `git show --stat`, never from memory.

## L-002: Process Weight Must Scale With the Project (2026-11-16)

- **Finding:** The Koine-OS layout produced 41 documents across 18 folders before any code
  existed. Navigation and review became slow, and reviews required reading many files.
- **Cause:** One folder per piece of work, separate draft and review files, daily logs and an
  index in every folder.
- **Rule:** Records that duplicate Git history are not kept. Each piece of work is one file.
  Everything awaiting the person appears on their generated Desk. See ADR-009 and ADR-011.

## L-001: Local Approvals Can Be Forged (2026-11-13)

- **Finding:** The assistant's shell is not a terminal, but the standard `script` command
  provides one. The assistant can also write files directly.
- **Test:** `python3 -c "import sys; print(sys.stdin.isatty())"` returned `False`; the same
  command run through `script -qc` returned `True`.
- **Consequence:** A terminal-only check does not prevent the assistant from approving. A
  pull request opened under the owner's login cannot be approved by the owner.
- **Rule:** Local approvals are tamper-evident (hashed), not tamper-proof. Proof requires the
  assistant to act under its own identity. See ADR-003 and ADR-007.
