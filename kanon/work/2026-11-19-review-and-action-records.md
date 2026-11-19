---
type: work
status: awaiting-approval
updated: 2026-11-19
---

# Review and Action Records

> **Summary:** Plan for P1-11, awaiting approval: let people tick action steps, add notes and comment on files or lines from GitHub (web, mobile, VS Code's GitHub Pull Requests extension) or plain Git, with the repository as the record and a short `kanon inbox` read for agents. Phase 1 item P1-11.
> **Decision needed:** Approve this plan and ADR-012 as set out in section 1.2. Below tier 3, host approvals are advisory; binding approval stays in chat or `kanon approve`. Tier 2 (issues) is optional item R-06: keep or defer it.

## 1. Plan

| Field | Value |
|---|---|
| Output | ADR-012; `kanon inbox`, `kanon done`, `kanon note`; a tier probe saved by `kanon init`; a host adapter interface with a Git-only adapter and a GitHub adapter (tiers 0 to 2); a Notes table in work files; Atlas and Metis prompt changes; P1-11 added to the phase-1 plan's item table, Order line and review points |
| Inputs | Owner requests, 2026-11-19 (`kanon/sources.md`, section 15); ADR-007; ADR-009; ADR-011; P1-05, P1-09 and P1-10 in `kanon/work/2026-11-16-phase-1-plan.md` |
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
- **Tiers** are chosen by `kanon init` from what the host and the person's token allow, and shown on the Desk:

| Tier | Needs | Ticks and notes | File and line comments | Approval |
|---|---|---|---|---|
| 0. Git only | Git | Work file steps, or `kanon done <work> A-1 "note"` | `kanon note <path>:<lines> "text"` into the work file's Notes table, pinned to a commit | Chat or `kanon approve` |
| 1. Pull requests | Push access to a branch in the repository, or forking allowed | Checklist in the pull request description | Pull request review comments | Chat or `kanon approve`; host replies are advisory |
| 2. Issues (R-06, optional) | Tier 1 and issues enabled | One issue per action, steps as checkboxes, comments as notes | As tier 1 | As tier 1 |
| 3. GitHub App | App installed by an admin | As tier 2 | As tier 1 | Approval review under the owner's account (P1-10) |

- **Identity below tier 3:** the person's own `gh` login. An agent using that login could post an `approve` comment or tick a box as the person, so:
  - Host approvals are never binding below tier 3. `kanon inbox` reports them as advisory. Binding approval stays in chat or `kanon approve` (P1-05, bound to a hash of the approved material, which refuses an agent's own approval attempt). GitHub does not let an author approve their own pull request, so review approvals are unavailable below tier 3.
  - A tick or note from an account other than the acting login, that is the assignee or a listed approver, is applied directly.
  - A tick or note from the acting login is written to the work file as **pending**, with its host ID, and shown on the Desk. It is applied when the person replies `done <work> <ID>` in chat, the existing Atlas confirmation (ADR-011). Agents may not issue that reply for the person.
- **Bot account:** ADR-007 also allows a machine-user account. It would make tier 1 approvals genuine without an App, but many enterprises forbid machine users (assessment); it is deferred to P1-10 as an alternative identity.
- **ADR-012** amends two parts of ADR-007 and none of ADR-009: the identity rule (the person's login is allowed below tier 3, with the limits above) and the read-back rule (ticks and notes are read back, only from an action's assignee or a listed approver; others are ignored).
- **Adapter interface:** `capabilities()`, `changes_since(time)` (ticks, notes, comments, approvals), `publish(work)`. GitLab and Bitbucket can be added later behind the same interface.
- **`kanon inbox`:** prints new changes, one line each, and applies them to work files. Each change, applied or pending, records its host ID in the work file, so a second run or a fresh clone with no `kanon/local/` repeats nothing. Pending items stay on the Desk, not in the inbox output. A cursor in `kanon/local/` only reduces `gh` calls.
- **Line notes** live in the work file's Notes table (one file per piece of work, ADR-009) and record the commit SHA they were written against. `kanon verify` maps the range to the current file through `git diff`: lines that only moved are re-anchored; lines that changed make the note stale; a missing commit (squash merge, shallow clone) makes it unverifiable. Stale and unverifiable are warnings, never failures.
- **No model calls** in any command; GitHub calls run locally through `gh`. Kanon starts no Actions itself. Opening pull requests or posting comments can trigger a repository's own workflows on those events; the probe lists such workflows so the person knows the cost. Actions minutes are used only by the repository's own workflows (assessment).
- **The Desk** shows the tier saved by `kanon init` and makes no `gh` call.
- **Shared with P1-10:** the pull request description generator and the pull request opening code are built once in R-04, using P1-09's branch names, and reused by P1-10, which adds only the App identity and approval read-back.

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
| Tiers 0 and 1 for GitHub and GitHub Enterprise; tier 2 as optional R-06 | Tier 3 App identity (P1-10) |
| Capability probe, saved by `kanon init` and shown on the Desk | GitLab and Bitbucket adapters (later phase) |
| Desk links to issues and pull requests | VS Code extension; GitHub Project board (Phase 2) |

### 1.5 Work Items

| ID | Item | Delivers |
|---|---|---|
| R-01 | ADR-012 | Tiers, identity below tier 3, advisory host approvals, pending ticks, read-back rule |
| R-02 | Tier 0 | `kanon done`, `kanon note`, an optional Notes section between Actions and Review, verify checks |
| R-03 | Adapter and probe | Interface, Git-only adapter, tier probe and workflow listing |
| R-04 | GitHub adapter, tier 1 | Pull requests through `gh`: description, checklist, review comments; recorded responses for tests |
| R-05 | `kanon inbox` and roles | Change summary, idempotent work file updates, Atlas and Metis prompts, Desk links |
| R-06 | Tier 2 (optional) | One issue per action, checkbox and comment read-back |

**Order and dependencies:** R-01, then R-02 and R-03, then R-04 and R-05, then R-06 if kept. P1-11 depends on P1-05 (binding `kanon approve`) and P1-09 (branch names), and P1-10 reuses R-04. The phase-1 Order becomes: P1-05 and P1-09 (group C), then P1-11 (groups D: R-01 to R-03, and E: R-04 to R-06), then P1-10 (group F), then P1-08. The group C review point covers P1-05 and P1-09; new review points follow groups E and F.

**Cost estimate (assessment):** about 1.5 times the group B build (P1-04 and P1-06), recorded in section 5 as work proceeds. Each session's `kanon inbox` makes one `gh` call per open pull request (plus one per open action issue at tier 2) and prints under 1,500 characters for 10 changes.

### 1.6 Acceptance

| Check | A wrong result fails because |
|---|---|
| `kanon done` and `kanon note` write records that `kanon verify` accepts; a malformed record fails | Tests for each field |
| Line notes: an untouched note is not stale; lines that only moved are re-anchored and not stale; changed lines make it stale; a missing commit makes it unverifiable; `verify` passes in every case | One test per case |
| Recorded responses: a ticked checkbox or a note in a pull request (and an issue, if R-06 is kept) from the assignee's own account, not the acting login, sets Done or adds the note in the correct work file and action | A wrong file, action or step fails the test |
| A tick or note from the acting login is recorded as pending and does not set Done until a `done <work> <ID>` reply; a later inbox run neither repeats nor drops it | Each condition asserted |
| Ticks or notes from an account that is neither the assignee nor a listed approver are ignored | Tested |
| A host `approve` comment never sets a work file's decision; it is reported as advisory | Tested |
| `kanon inbox` first run prints all 10 recorded changes (none needing confirmation) and applies them; a second run prints nothing and changes no file; a run with `kanon/local/` removed also repeats nothing | Each condition asserted |
| `kanon inbox` output for 10 changes, all present, is under 1,500 characters | Measured in a test |
| Probe selects tier 2, tier 1 or tier 0 for recorded responses with issues enabled, issues disabled, fork-only access, and no push or fork access; a missing API field falls back one tier | One test per case |
| Probe lists recorded workflows triggered by `pull_request` and `issue_comment`, and tier 1 is not used until the person accepts them | Tested |
| No command makes a model call or starts an Action through `gh` | Tests patch both and fail on any call |
| Tier 0 works with no network | Tests run with `gh` absent and `socket.connect` blocked |

### 1.7 Risks

| Risk | Handling |
|---|---|
| GitHub Enterprise Server versions differ in API fields | Probe reports unsupported fields; adapter falls back a tier |
| An agent acting as the person could forge a host approval or tick | Host approvals are advisory below tier 3; ticks under Kanon's own login need the person's confirmation (section 1.2) |
| Repository workflows triggered by pull requests or comments use Actions minutes | The probe lists them; the person decides before tier 1 is used |
| Host sync work may later need judgement (many people, many repositories) | Revisit a dedicated role with Pinax in Phase 2 |
| The owner's account cannot test GitHub Enterprise limits | Limits are simulated with recorded responses; untested on a real enterprise, stated in the result |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-19 | Which integration: GitHub-native, Claude Artifact, local server or VS Code extension? | GitHub-native as a starting point, without depending on GitHub |
| 2026-11-19 | How to work under GitHub Enterprise limits? | Tiers chosen by capability, with a Git-only floor |
| 2026-11-19 | New role for repository interaction? | None; routing added to Atlas and Metis |
| 2026-11-19 | Plan as P1-11 with tiers 0 to 2, tier 3 left to P1-10? | Yes |
| 2026-11-19 | Keep tier 2 (issues) now or defer it? Review K-311: tiers 0 and 1 meet every request; tier 2 adds sync work and notification noise. Recommendation: defer. Default: R-06 kept as optional | In the Decision needed line |

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| D1 | Plan (8d2829f) | Kritos (`kritos-reviewer` agent) | correct | K-300 to K-304 | Fixed in the plan: K-300 (agent could forge a host approval), K-301 (author cannot approve own pull request), K-302 (no read-back test), K-303 (inbox checks passed when empty), K-304 (line notes failed verify on edits), K-305 (cursor lost in fresh clones), K-306 (overlap with P1-10), K-307 (read-back rule), K-308 (repository workflows), K-309 (tier 1 needs), K-310 (VS Code path), K-311 (tier 2 optional), K-312 (network test); K-313 needs no change |
| D2 | Revised plan | Kritos (`kritos-reviewer` agent) | correct | K-320 to K-324 | Fixed in the plan after the final round: K-320 (ticks from the acting login), K-321 (pending items), K-322 (notes kept in the work file), K-323 (order against P1-05, P1-09, P1-10), K-324 (stale-note cases), K-325 to K-333; not independently reviewed. Owner decides at the review point |

## 4. Decision

Pending.

## 5. Cost

Recorded when work starts.
