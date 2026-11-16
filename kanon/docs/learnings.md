---
type: learnings
status: current
updated: 2026-11-16
---

# Learnings

> **Summary:** Lessons from building and using Kanon that apply beyond the task that produced
> them. Newest first.

## L-002: Process Weight Must Scale With the Project (2026-11-16)

- **Finding:** The Koine-OS layout produced 41 documents across 18 folders before any code
  existed. Navigation and review became slow, and reviews required reading many files.
- **Cause:** One folder per piece of work, separate draft and review files, daily logs and an
  index in every folder.
- **Rule:** Records that duplicate Git history are not kept. Each piece of work is one file.
  Everything awaiting a decision appears in `REVIEW.md`. See ADR-009.

## L-001: Local Approvals Can Be Forged (2026-11-13)

- **Finding:** The assistant's shell is not a terminal, but the standard `script` command
  provides one. The assistant can also write files directly.
- **Test:** `python3 -c "import sys; print(sys.stdin.isatty())"` returned `False`; the same
  command run through `script -qc` returned `True`.
- **Consequence:** A terminal-only check does not prevent the assistant from approving. A
  pull request opened under the owner's login cannot be approved by the owner.
- **Rule:** Local approvals are tamper-evident (hashed), not tamper-proof. Proof requires the
  assistant to act under its own identity. See ADR-003 and ADR-007.
