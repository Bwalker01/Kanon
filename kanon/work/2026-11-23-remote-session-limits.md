---
type: work
status: in-progress
updated: 2026-11-23
---

# Remote Session Limits

> **Summary:** Investigation of why work cannot be completed in Claude Code cloud sessions, with fixes made here and fixes or workarounds proposed to the owner.
> **Decision needed:** Answer Q-1 (reading pull requests and CI with the owner's login) and Q-2 (Remote Control); owner actions A-1 and A-2 are on the Desk.

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
| F-1 | The GitHub App cannot sign in from a cloud session | Tested: `GET /app` refused on 2026-11-20, "Access to this GitHub API path is not permitted through this proxy" (ADR-014) | The agent proxy's GitHub path policy; environment settings control hosts only (environment documentation, network page) | Open pull requests from the owner's computer (owner, 2026-11-20); report the refusal to Anthropic (A-1); Q-2 covers using the owner's computer from a cloud session |
| F-2 | A cloud session cannot run commands on the owner's computer | Tested: `list_computer_folders` returned no folders on 2026-11-23 | No folder is shared through Remote Control; the environment documentation says sharing may not be available to every account | Q-2 |
| F-3 | Pushing any branch but the session's own needs the owner's permission in each session | This session's harness instruction: "Push to no other branch without explicit permission"; P1-10 needed a question on 2026-11-20 | The cloud harness's default | A-2 records a standing permission in the environment's setup script; whether the harness accepts it as explicit permission is an assessment until A-2's check passes |
| F-4 | The owner's GitHub login carries the clone and harness pushes, and cannot be removed | Tested: this session's command-line Git configuration holds the URL rewrites and credential settings (2026-11-23) | Claude's GitHub connection serves the session's Git traffic | Recorded limit (ADR-014); rule 14 and the connector deny stop agents opening, approving or merging pull requests with it |
| F-5 | Cloud sessions cannot read pull requests or CI results | Tested: `gh auth status` reports "The token in GH_TOKEN is invalid" (2026-11-23); the whole connector is denied since 9ba6245 | The connector, which acts as the owner, was the only reader; `gh` serves only search here (assessment, from this session's harness instructions) | Q-1 |
| F-6 | The installed `kanon` drifts from the repository after engine changes | On 2026-11-18 `kanon sync` left the guard hook unchanged after fixes until `uv tool install --force .` ran; later engine changes needed the same step (assessment: this session's commands, not a repository record) | `uv tool install` copies a snapshot; the setup script installs once per session | Mitigated: `kanon sync` in Kanon's own repository now reports a stale install with the command to refresh it (`stale_install`, tested). It still writes the stale files, the first refresh after this change is manual, and `kanon verify` does not check |
| F-7 | Environment variables apply only to new or resumed sessions | Tested: `KANON_APP_ID` was missing until the session was resumed (2026-11-20) | Containers read variables at start (assessment) | Resume or start a session after changing the environment |
| F-8 | Uncommitted or unpushed edits can be lost when the worker restarts | Two worker restarts in this session; L-003 | Only pushed commits survive a replaced container (assessment) | Commit after each step (rules 1 and 9, L-003); the harness's Stop hook asks for a push (`/root/.claude/launcher-settings.json`, harness level). No Kanon rule requires the push; a push rule can be added if the owner wants it |
| F-9 | The commit-signing helper lives in `/tmp` | Tested: `/tmp/code-sign` links to the environment runner (2026-11-23); L-004 | The harness places it there | The guard blocks deleting `/tmp` (L-004) |
| F-10 | A session started from `main` lacks protections still on a working branch | ADR-014, Consequences: pull request #4 was opened through the owner's account by a session started from `main` | Each session starts from the default branch | Closed for P1-05 to P1-10 by the merge of pull request #5 (8cd5211); remains for future work, so Kanon changes should reach `main` promptly |
| F-11 | New hosts need the owner's approval | `api.github.com` was added through an approved environment change on 2026-11-20 | The environment's limited network policy | Propose each host with evidence; the owner approves the card |
| F-12 | Secrets saved as environment variables are readable by every command | `KANON_APP_KEY` (owner accepted, 2026-11-20); network secrets only add headers (environment documentation, secrets page) | Environment design | Recorded limit (ADR-014) |
| F-13 | Long commands leave the foreground | Tested: a test run passing 120 seconds moved to the background on 2026-11-20 | The harness's command timeout | Keep waits in tests configurable (`setup(wait=...)`) and run the suite with a timeout |

Out of scope: the Desk, which a cloud session can send to the owner as a file (done in this session).

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-23 | Q-1: the owner decided on 2026-11-19 that agents never use the owner's GitHub login, and the code applies that to reading too. New information (F-5): cloud sessions therefore cannot see pull request reviews or CI results. Allowing the connector's reading tools would make those reads under the owner's login. Options: allow reading only, or stay fully denied. Recommendation: allow reading only; default: stay denied | Awaiting the owner |
| 2026-11-23 | Q-2: should a cloud session use the owner's computer through Remote Control (F-2)? That conflicts with rule 14 and ADR-014 (the person runs `kanon github pr`), and on that computer an agent could reach the owner's `gh` login and the App key; whether Kanon's guard and deny rules apply to commands sent to an attached computer is untested. Options: no; or yes, only for `kanon github pr` and `kanon github check` after the owner approves each attach, with ADR-014 amended. Recommendation: no until the guard is tested there; default: no | Awaiting the owner |

## 3. Actions

| ID | Action | Assignee | Blocks | Done |
|---|---|---|---|---|
| A-1 | Report the GitHub App path refusal to Anthropic | Bwalker01 | | no |
| A-2 | Give standing permission to push `kanon/*` branches | Bwalker01 | | no |

### A-1: Report the Proxy Refusal

1. In the Claude app, send feedback from a cloud session (`/feedback`, or the feedback option in the session menu).
2. Report that the cloud agent proxy refused `GET /app` on api.github.com ("Access to this GitHub API path is not permitted through this proxy"), and that GitHub App sign-in also needs `GET /repos/{owner}/{repo}/installation` and `POST /app/installations/{id}/access_tokens` (not tested).
3. Confirm: a later cloud session's `kanon github check` signs in.

### A-2: Standing Push Permission

1. In the Claude app, open the "Kanon" environment's settings and edit the setup script line that runs `kanon profile`. Agents may propose this change but never apply it without the owner's approval, and never add such a preference themselves.
2. Add `--preference "Cloud sessions may push kanon/* branches of Bwalker01/Kanon."` after the four existing `--preference` options, keeping them, since the list is replaced, not extended.
3. Start a new cloud session on the environment.
4. Confirm: `.claude/rules/kanon-person.md` lists the preference, and the session pushes a `kanon/*` branch without asking. If it still asks, the harness does not accept the preference as permission and F-3 stays open.

## 4. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| 1 | Findings, actions, `stale_install` (b5f32c8) | Kritos (`kritos-reviewer` agent) | correct | K-500 to K-502 | K-500 (push permission unproven and unsafe), K-501 (Remote Control conflicts with rule 14, now Q-2), K-502 (Q-1 reopened an owner answer without citing it) and non-blocking K-503 to K-511 fixed |

## 5. Decision

Pending.

## 6. Cost

Recorded when work starts.

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| Investigation, fix and review round 1 | 21,601 | 16,792 | 79,485 | 7,852,456 | not yet calculated (Claude Code has not updated its estimate) |
