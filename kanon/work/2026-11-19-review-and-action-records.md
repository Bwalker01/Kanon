---
type: work
status: awaiting-approval
updated: 2026-11-19
---

# Review and Action Records

> **Summary:** Let people tick action steps, add notes and comment on files or lines from GitHub, VS Code or plain Git, with the repository as the record and a short `kanon inbox` read for agents. Phase 1 item P1-11.
> **Decision needed:** Approve this plan, including ADR-012 amending the identity rule in ADR-007, before any build starts.

## 1. Plan

| Field | Value |
|---|---|
| Output | ADR-012; `kanon inbox`, `kanon done`, `kanon note`, `kanon hosts`; a host adapter interface with a Git-only adapter and a GitHub adapter (tiers 0 to 2); review notes files; Atlas and Metis prompt changes; roadmap entry P1-11 |
| Inputs | Owner requests, 2026-11-19 (`kanon/sources.md`, section 15); ADR-007; ADR-011; P1-10 in `kanon/work/2026-11-16-phase-1-plan.md` |
| Acceptance | See section 1.6 |
| Creator | Claude Code (builder session) |
| Reviewer | Kritos (`kritos-reviewer` agent) |
| Group round limit | 2 (owner, 2026-11-16) |

### 1.1 Problem

- The Desk page is a read-only snapshot. Ticks stay in one browser, and notes cannot be returned except by chat.
- Review notes cannot be attached to a file or to specific lines.
- Agents must not re-read large pages to learn what changed; each read costs tokens.
- A design tied to GitHub fails where an enterprise disables issues or Projects, forbids GitHub Apps, or grants users limited permissions (owner, 2026-11-19).

### 1.2 Design

- **Source of truth:** the repository, as in ADR-007. Hosts are optional places to tick, note and comment; `kanon inbox` copies their changes back into work files.
- **Tiers,** chosen by `kanon init` from what the host and the person's token allow, and reported by `kanon hosts`:

| Tier | Needs | Ticks and notes | File and line comments | Approval |
|---|---|---|---|---|
| 0. Git only | Git | Work file steps, or `kanon done <work> A-1 "note"` | `kanon note <path>:<lines> "text"` into `kanon/reviews/<work>.md` | Chat or `kanon approve` |
| 1. Pull requests | Permission to open a pull request | Checklist in the pull request description | Pull request review comments | `approve` comment or pull request review |
| 2. Issues | Issues enabled | One issue per action, steps as checkboxes, comments as notes | As tier 1 | As tier 1 |
| 3. GitHub App | App installed by an admin | As tier 2 | As tier 1 | Approval review under the owner's account (P1-10) |

- **Identity below tier 3:** the person's own `gh` login. GitHub does not let an author approve their own pull request (ADR-007), so an `approve` comment from an approver listed in `kanon/kanon.toml` counts instead. ADR-012 records this amendment.
- **Adapter interface:** `capabilities()`, `changes_since(time)` (ticks, notes, comments, approvals), `publish(work)`. GitLab and Bitbucket can be added later behind the same interface.
- **`kanon inbox`:** prints only changes since its last run, as one line each, and applies ticks and decisions to work files. The last-read time is kept in `kanon/local/`.
- **No model calls** in any command; GitHub calls run locally through `gh` and use no Actions minutes (ADR-007).

### 1.3 Roles

No new role. The host sync is mechanical; each judgement fits an existing role.

| Event | Role | Change to its prompt |
|---|---|---|
| Ticks, action notes, approvals | Atlas | Run `kanon inbox` at session start and route its output |
| Comments on files or lines | Metis | Turn owner comments into Review findings |
| Approved work merged | Clio | None |

### 1.4 Scope

| In scope | Out of scope |
|---|---|
| Tiers 0 to 2 for GitHub and GitHub Enterprise | Tier 3 App identity (P1-10) |
| `kanon hosts` capability probe | GitLab and Bitbucket adapters (later phase) |
| Desk links to issues and pull requests | VS Code extension; GitHub Project board (Phase 2) |

### 1.5 Work Items

| ID | Item | Delivers |
|---|---|---|
| R-01 | ADR-012 | Tiers, identity below tier 3, `approve` comment rule |
| R-02 | Tier 0 | `kanon done`, `kanon note`, `kanon/reviews/` format, verify checks |
| R-03 | Adapter and probe | Interface, Git-only adapter, `kanon hosts` |
| R-04 | GitHub adapter | Tiers 1 and 2 through `gh`, with recorded responses for tests |
| R-05 | `kanon inbox` and roles | Change summary, work file updates, Atlas and Metis prompts, Desk links |

### 1.6 Acceptance

| Check | A wrong result fails because |
|---|---|
| `kanon done` and `kanon note` record ticks, notes and line ranges that `kanon verify` accepts | A malformed record or a line range outside the file fails verify |
| A probe with issues disabled selects tier 1; with no pull request permission, tier 0 | Recorded `gh` responses for each case; a wrong tier fails |
| `kanon inbox` run twice prints nothing the second time | Repeated output fails the test |
| `kanon inbox` output for 10 changes stays under 1,500 characters | Measured in a test |
| An `approve` comment counts only from a listed approver | A comment from any other account is ignored, tested |
| No command makes a model call or starts a GitHub Action | Tests patch both and fail on any call |
| Tier 0 works with no network | Tests run with `gh` absent |

### 1.7 Risks

| Risk | Handling |
|---|---|
| GitHub Enterprise Server versions differ in API fields | Probe reports unsupported fields; adapter falls back a tier |
| An `approve` comment is weaker evidence than a review | Recorded with the comment URL and author; tier 3 remains the strong form |
| Host sync work may later need judgement (many people, many repositories) | Revisit a dedicated role with Pinax in Phase 2 |
| The owner's account cannot test GitHub Enterprise limits | Limits are simulated with recorded responses; untested on a real enterprise, stated in the result |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-19 | Which integration: GitHub-native, Claude Artifact, local server or VS Code extension? | GitHub-native as a starting point, without depending on GitHub |
| 2026-11-19 | How to work under GitHub Enterprise limits? | Tiers chosen by capability, with a Git-only floor |
| 2026-11-19 | New role for repository interaction? | None; routing added to Atlas and Metis |
| 2026-11-19 | Plan as P1-11 with tiers 0 to 2, tier 3 left to P1-10? | Yes |

## 3. Review

Not yet reviewed.

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
