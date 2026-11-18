---
type: review-list
status: current
updated: 2026-11-18
---

# Awaiting You

> **Summary:** One decision and five actions. Decide with the item number and **approve** or
> **changes:**; mark an action done by telling the assistant. Steps: `kanon/docs/owner-setup.md`.

## Decisions

### R-1: Desk and Atlas

- **Decide:** approve replacing this file and `STATUS.md` with a generated, per-person Desk kept by a new role, Atlas.
- **Read:** `kanon/work/2026-11-18-desk-and-atlas.md`, sections 1.2 to 1.6. Replaces the earlier R-1.

## Actions

| ID | Action | Steps | Needed before |
|---|---|---|---|
| A-1 | Generate the GitHub App key pair and install the App on `Bwalker01/Kanon` | Setup, section 1 | P1-10 |
| A-3 | Protect `main`: pull request with one approval required | Setup, section 3 | P1-10 |
| A-4 | Point the "Kanon" cloud environment at `Bwalker01/Kanon` | Setup, section 4 | P1-10 |
| A-5 | Start a fresh session to prove the setup script | Setup, section 5 | Next session (now possible) |
| A-6 | Optional: ask GitHub Support to purge the old commits | Setup, section 6 | No deadline |
