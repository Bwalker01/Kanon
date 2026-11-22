---
type: review-list
status: current
updated: 2026-11-22
---

# Awaiting You

> **Summary:** Two decisions and six actions. Decide with the item number and **approve** or
> **changes:**; mark an action done by telling the assistant. Steps: `kanon/docs/owner-setup.md`.

## Decisions

### R-1: Owner Actions List

- **Decide:** approve tracking owner actions here, with steps in `kanon/docs/owner-setup.md`.
- **Read:** `kanon/work/2026-11-18-owner-actions.md`, section 1.

### R-2: Windows Test Portability

- **Decide:** approve merging `claude/windows-tests`; tests only, suite passes on Windows, Kritos passed it with notes.
- **Read:** `kanon/work/2026-11-22-windows-test-portability.md`, sections 1 and 3.

## Actions

| ID | Action | Steps | Needed before |
|---|---|---|---|
| A-1 | Generate the GitHub App key pair and install the App on `Bwalker01/Kanon` | Setup, section 1 | P1-10 |
| A-2 | Merge `claude/stoic-knuth-mud2jv` into `main` without squashing | Setup, section 2 | A-3, A-5 |
| A-3 | Protect `main`: pull request with one approval required | Setup, section 3 | P1-10 |
| A-4 | Point the "Kanon" cloud environment at `Bwalker01/Kanon` | Setup, section 4 | P1-10 |
| A-5 | Start a fresh session to prove the setup script | Setup, section 5 | Next session |
| A-6 | Optional: ask GitHub Support to purge the old commits | Setup, section 6 | No deadline |
