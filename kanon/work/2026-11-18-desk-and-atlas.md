---
type: work
status: awaiting-approval
updated: 2026-11-18
---

# Desk and Atlas

> **Summary:** Replace the committed review list and status page with a generated, per-person Desk, maintained by a new role, Atlas, so parallel branches never conflict.
> **Decision needed:** Approve this design (R-1 in `kanon/REVIEW.md`; it replaces the earlier R-1).

## 1. Plan

| Field | Value |
|---|---|
| Output | Atlas role; `kanon desk`; generated `kanon/local/DESK.md`, `desk.html` and `STATUS.md`; committed `kanon/docs/roadmap.md`; an Actions section in work files; ADR-011 |
| Inputs | Owner requests, 2026-11-18 (`kanon/sources.md`, section 12) |
| Acceptance | See section 1.5 |
| Creator | Claude Code (builder session) |
| Reviewer | Kritos (independent subagent) |
| Group round limit | 2 (owner, 2026-11-16) |

### 1.1 Problem

- `kanon/REVIEW.md` and `kanon/STATUS.md` are committed, but every branch edits them. Two features in progress at once will conflict on both files.
- `REVIEW.md` is one person's view: their decisions and actions. Committing it shares a personal list with everyone.
- `kanon/docs/owner-setup.md` duplicates actions that belong with the work that needs them.

### 1.2 Committed Record and Generated Views

| Content | Where | Committed |
|---|---|---|
| Decisions awaiting approval | The work file: status `awaiting-approval` and its "Decision needed" line | Yes |
| Owner actions, with steps | The work file that needs them, in a new optional Actions section | Yes |
| Late fixes awaiting review | The work file's Review table (rows marked for the owner) | Yes |
| Phase plan | `kanon/docs/roadmap.md` (changes rarely) | Yes |
| The person's Desk | `kanon/local/DESK.md` and `kanon/local/desk.html` | No |
| Project status | `kanon/local/STATUS.md`: work in progress from work files, recent changes from commit messages | No |

Every branch then carries only its own work files. Switching branches changes the Desk to match.

### 1.3 Atlas

Atlas holds what rests on the person's shoulders. A thirteenth archetype, extending the twelve in Koine-OS.

- **Role prompt** `kanon/docs/roles/atlas.md`; skill `kanon-atlas`.
- **Collects** the decisions the person may approve (listed approvers), the actions assigned to their GitHub username, and items marked for owner review.
- **Orders** them by what blocks what: each action names the actions or work it blocks.
- **Renders** the Desk with `kanon desk`, which `kanon init` and `kanon sync` also run.
- **Opens** the Desk for the person whenever a decision or action is added.
- **Marks** an action done in its work file when the person confirms it; the commit records that.

### 1.4 The Desk Page

`kanon/local/desk.html` is one self-contained file with no server and no external resources.

| Section | Contents |
|---|---|
| Decide | Each decision with its summary, an expandable "read" panel, and a button that copies the reply (for example `R-1 approve`) |
| Do | Actions in dependency order, each with step checklists and a progress bar |
| Review later | Fixes made after a final review round, grouped by work file |
| Status | Work in progress and recent changes |

- **Ticks** are saved in the browser only, for convenience; done is recorded when the person tells the agent.
- **Decisions** still return through chat or `kanon approve`, so approval rules are unchanged.
- **Themes:** light and dark; readable at phone width.
- `DESK.md` holds the same content as plain Markdown for any viewer.

### 1.5 Acceptance

| Check | A wrong result fails because |
|---|---|
| Two branches each add an action and a decision; they merge with no conflict in any Kanon file | A conflict fails the test |
| `kanon/local/` is never tracked; `kanon verify` reports it if forced in | Tests for both |
| The Desk lists only items for the current person, in dependency order | A fixture with two people and a blocking chain |
| `desk.html` loads no external resource | A test scans for `http` in `src` and `href` attributes |
| Removing an action from a work file removes it from the Desk on the next `kanon desk` | Regeneration test |

### 1.6 This Repository

- `kanon/REVIEW.md`, `kanon/STATUS.md` and `kanon/docs/owner-setup.md` are removed. Phases move to `roadmap.md`; the open owner actions move, with their steps, into a work file `kanon/work/2026-11-18-repository-setup.md`.
- ADR-011 supersedes the "one list" rule in ADR-003 and the `REVIEW.md` and `STATUS.md` entries in ADR-009.

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-18 | Commit `REVIEW.md` and `STATUS.md`? | Neither; status generated, roadmap committed |
| 2026-11-18 | Name for the personal list | `DESK.md`, maintained by a new archetype, Atlas |
| 2026-11-18 | How interactive should the Desk be? | A self-contained page with no server |

## 3. Review

Not yet reviewed.

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
