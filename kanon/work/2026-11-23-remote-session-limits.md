---
type: work
status: in-progress
updated: 2026-11-23
---

# Remote Session Limits

> **Summary:** Investigation of why work cannot be completed in Claude Code cloud sessions, with fixes made here and fixes or workarounds proposed to the owner.
> **Decision needed:** None yet.

## 1. Plan

| Field | Value |
|---|---|
| Output | Section 1.3 Findings: each limit with evidence, cause, and a fix made, proposed or a workaround; any fixes Kanon can make itself, with tests |
| Inputs | Owner request, 2026-11-23 (`kanon/sources.md`, section 18); this session's record (P1-05 to P1-10, learnings L-001 to L-004); the environment documentation; read-only probes in this session |
| Acceptance | Every finding cites a test, a probe or a documented source, or is labelled an assessment; no probe retries a proxy denial or works around a policy; each proposed fix names who acts and how success is confirmed |
| Creator | Claude Code (cloud session) |
| Reviewer | Kritos (`kritos-reviewer` agent) |

### 1.1 Scope

| In scope | Out of scope |
|---|---|
| GitHub access, network policy, secrets, branch and push rules, session restarts, installed-version drift, signing, connecting the owner's computer | Changing Anthropic's proxy policy (reported only); work the local session is doing in parallel |

### 1.2 Method

1. List every failure met in remote sessions from 2026-11-16 to 2026-11-23, from work files, learnings and commit history.
2. Read the environment documentation for each area.
3. Run read-only probes only; no retries of refusals.
4. Fix what Kanon can fix, with tests; propose the rest as owner actions or questions.

### 1.3 Findings

| # | Limit | Evidence | Cause | Fix or workaround |
|---|---|---|---|---|
| F-1 | The GitHub App cannot sign in from a cloud session | `GET /app` refused on 2026-11-20: "Access to this GitHub API path is not permitted through this proxy" (ADR-014) | The agent proxy's GitHub path policy; not an environment setting (environment documentation lists hosts only) | Proposed: open pull requests from the owner's computer (owner, 2026-11-20); or attach that computer to a cloud session with Remote Control (F-2); and report the policy to Anthropic (owner action A-1) |
| F-2 | A cloud session cannot run commands on the owner's computer | `list_computer_folders` returned no folders on 2026-11-23 | No folder is shared through Remote Control in the Claude desktop app; documentation says the feature is not yet available to every account | Proposed: owner shares the Kanon clone in the desktop app (A-2); a cloud session can then run `kanon github pr` there after the owner approves the attach |
| F-3 | Pushing any branch but the session's own needs the owner's permission in each session | Harness instruction for this session: "Push to no other branch without explicit permission"; P1-10 needed a question on 2026-11-20 | The cloud harness's default; a durable instruction from the owner counts as permission | Proposed: a standing permission for `kanon/*` branches in the owner's profile preferences (A-3), which every session reads in `.claude/rules/kanon-person.md` |
| F-4 | The owner's GitHub login is used for the clone and harness pushes, and cannot be removed | `git config` in this session: URL rewrites and credentials come from the command-line environment, set by the harness (probe, 2026-11-23) | Claude's GitHub connection serves the session's Git traffic | Recorded limit (ADR-014). Rule 14 and the connector deny stop agents opening, approving or merging pull requests with it |
| F-5 | Cloud sessions can no longer read pull requests or CI results | `gh auth status`: "The token in GH_TOKEN is invalid" (probe, 2026-11-23); the whole GitHub connector is denied since 9ba6245 | `gh` is served only for search; the connector was the only reader, and it acts as the owner | Question Q-1: allow the connector's reading tools, or keep it fully denied and have the owner or a local session relay results |
| F-6 | The installed `kanon` drifts from the repository after engine changes | On 2026-11-18 `kanon sync` left the guard hook unchanged after fixes until `uv tool install --force .` ran; every engine change since needed the same manual step (this session's commands) | `uv tool install` copies a snapshot at session start; later edits are not picked up | Fixed here: `kanon sync` in Kanon's own repository reports a stale install with the command to refresh it (`stale_install`, tested) |
| F-7 | Environment variables and setup scripts apply only to new sessions | Environment documentation; `KANON_APP_ID` was missing until the session was resumed (2026-11-20) | Containers read variables at start | Workaround: after changing the environment, resume or start a session before relying on it |
| F-8 | Uncommitted edits can be lost when the worker restarts | Two worker restarts in this session; L-003 (edits lost, then recorded as done) | The container is replaced; only pushed commits survive | Existing rule: commit and push after each step; the Stop hook asks for it. No further fix |
| F-9 | The commit-signing helper lives in `/tmp` | `/tmp/code-sign` links to the environment runner (probe, 2026-11-23); L-004 | The harness places it there; a session restart restores it | The guard blocks deleting `/tmp` (L-004); no further fix |
| F-10 | A session started from `main` lacks protections still on a working branch | Pull request #4, opened through the owner's account on 2026-11-23 | Each session starts from the default branch | Workaround: merge Kanon changes to `main` promptly; the setup script reinstalls Kanon from the checkout at each start |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-23 | Q-1: should cloud sessions use the GitHub connector's reading tools (pull requests, CI results) with the owner's login, or stay fully denied? Recommendation: allow reading only; default: stay denied | Awaiting the owner |

## 3. Actions

| ID | Action | Assignee | Blocks | Done |
|---|---|---|---|---|
| A-1 | Report the GitHub App path refusal to Anthropic | Bwalker01 | | no |
| A-2 | Share the Kanon clone with cloud sessions through Remote Control | Bwalker01 | | no |
| A-3 | Give standing permission to push `kanon/*` branches | Bwalker01 | | no |

### A-1: Report the Proxy Refusal

1. In the Claude app, send feedback from this session (`/feedback`, or the feedback option in the session menu).
2. Say that the cloud agent proxy refuses GitHub App API paths (`GET /app`, `GET /repos/{owner}/{repo}/installation`, `POST /app/installations/{id}/access_tokens`), so a GitHub App cannot sign in from Claude Code cloud sessions.
3. Confirm: a later cloud session's `kanon github check` signs in.

### A-2: Share the Clone

1. In the Claude desktop app on your computer, open Settings, Claude Code, Remote Control.
2. Add your local Kanon clone as a shared folder.
3. Confirm: in a cloud session, ask the assistant to list your computer's folders; the clone appears. The feature may not be available to every account yet.

### A-3: Standing Push Permission

1. Run `kanon profile --preference "Cloud sessions may push kanon/* branches of Bwalker01/Kanon."`, adding your other preferences again, since the option replaces the list (see `kanon profile --help`).
2. Run `kanon sync`, then update the "Kanon" environment's setup script line that runs `kanon profile`, so new sessions get the same preference.
3. Confirm: `.claude/rules/kanon-person.md` lists the preference in a new session.


## 4. Review

Not yet reviewed.

## 5. Decision

Pending.

## 6. Cost

Recorded when work starts.
