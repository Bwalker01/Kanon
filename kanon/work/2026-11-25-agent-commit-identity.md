---
type: work
status: planning
updated: 2026-11-25
---

# Agent Commit Identity

> **Summary:** Part of Phase 1 completion: agents commit as the Kanon App (`kanon-agent[bot]`), so the owner's review of an
> App pull request counts and merging needs no bypass. `kanon sync` sets the identity for agent sessions only.
> **Decision needed:** None until Kritos passes the plan; then approve it (`kanon approve agent-commit-identity --plan` or a reply).

## 1. Plan

| Field | Value |
|---|---|
| Output | `src/kanon/sync.py` (identity in `.claude/settings.local.json`), `src/kanon/github.py` (`check` line, record commit identity), tests, a README line |
| Inputs | The owner's report (section 2); pull requests #6, #9, #10 and #11 read through the App on 2026-11-25; ADR-014 ("Owner's login"); the "Main Protection" ruleset read through the App on 2026-11-25 |
| Acceptance | See 1.2 |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### 1.1 Design

| Part | Choice |
|---|---|
| Cause | Every commit on the App's pull requests #6, #9, #10 and #11 is authored and committed as `Bwalker01`, because agents commit with the computer's Git identity (`user.name`, `user.email`). GitHub showed the owner as the author of the last commit, so the owner's review did not count towards the one required approval and the merge needed the owner's bypass (owner, section 2). |
| Identity | Author and committer `kanon-agent[bot] <357858083+kanon-agent[bot]@users.noreply.github.com>`. 357858083 is the App's bot user ID, read through the App with `GET /users/kanon-agent%5Bbot%5D` on 2026-11-25; GitHub links commits to an account by its no-reply address (assessment, from GitHub's no-reply address format). |
| Setting | `[github] bot_user_id` in `kanon/kanon.toml`, written by the owner (A-1), since agents never edit that file. `kanon github check` prints the line to add when it is missing or differs, as it does for `app_id` (K-411). |
| Agent sessions | `kanon sync` adds `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL` to the `env` object of `.claude/settings.local.json` (git-ignored, already written by `kanon sync`), keeping other settings, and updates them when they differ. Claude Code applies that `env` to the session's commands, so the owner's own terminal keeps the owner's identity (assessment, from Claude Code's settings documentation; confirmed by test step 4). It takes effect from the next session. Without `bot_user_id`, `sync` writes nothing and prints a note naming A-1. Cloud sessions get the same entries, because the setup script runs `kanon init`, which runs `sync` (assessment). |
| Record commits | The commit `kanon github pr` makes for the "Approved on merge" row is authored as the App when `bot_user_id` is set, whoever runs the command, since it is Kanon's own record. |
| Not changed | Existing history (no rewrite); the `Co-Authored-By` trailer; commits the owner makes in their own terminal. |
| Limits | Attribution only: an agent can still override the variables, so this is not a control; the owner's merge stays the approval (ADR-014). Cloud commit signing uses a helper tied to the owner (F-9 of `2026-11-23-remote-session-limits.md`), so bot-authored cloud commits may show as unverified; the ruleset does not require signatures (read 2026-11-25). |
| Risk | The ruleset has `require_extra_approval_for_unattributed_changes: true`. GitHub documents an extra approval for unattributed Copilot pull requests only; whether it also applies to bot-authored commits is untested. Test step 4 shows it; if it applies, the owner decides whether to turn the setting off. |
| Branches | Plan branch `kanon/agent-commit-identity/plan`, cut from `main` at 2b586b3. One item, `AC-1`, on `kanon/agent-commit-identity/AC-1`. |
| Sequence | 1. Kritos passes the plan. 2. The owner approves it and does A-1. 3. AC-1 built and reviewed by Kritos, then merged. 4. Live test: from step 3 on, the assistant commits with the four variables set in each command (this session predates the setting), so this work's pull request is the first with no commit by the owner; the owner reviews and approves it on GitHub without the bypass and reports whether the approval counted. 5. `kanon github pr`, `notes` and `ready`; the owner merges, which approves the result. |

### 1.2 Acceptance

| Check | Confirmed by |
|---|---|
| With `bot_user_id` set, `kanon sync` writes the four variables into `settings.local.json`, keeps every other key, and a second run changes nothing | Test |
| Without `bot_user_id`, `sync` writes no variables and prints the A-1 note | Test |
| A commit made under the written `env` has the App as author and committer | Test in a temporary repository |
| `kanon github check` prints the `bot_user_id` line when it is missing or differs, and nothing when it matches | Tests with `call` patched |
| The "Approved on merge" record commit is authored as the App when `bot_user_id` is set | Test |
| On this work's pull request, every commit after step 3 is authored by `kanon-agent[bot]`, and the owner's approval counts without the bypass | The owner's report at step 4, recorded in section 4 |
| `uv run pytest -q` and `uv run kanon verify` pass | Command output |

### 1.3 Work Items

| ID | Item | Delivers |
|---|---|---|
| AC-1 | App commit identity | `sync` and `github` changes, tests, README line |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-25 | What did GitHub show when the owner's approval did not count? | Owner: "it showed as being me on the last commit of the branch so my review didn't count toward the 1. i had to enable bypass on merging the pr." |
| 2026-11-25 | Plan the fix? | Owner: "plan the commit as app fix" |

## 3. Actions

| ID | Action | Assignee | Blocks | Done |
|---|---|---|---|---|
| A-1 | Add the App's bot user ID to `kanon/kanon.toml` | Bwalker01 | | no |

### A-1: Bot User ID in kanon.toml

1. After approving the plan, open `kanon/kanon.toml` on the branch `kanon/agent-commit-identity/plan`.
2. Under `[github]`, below `app_slug`, add the line `bot_user_id = 357858083` and commit it with a message starting `MODIFIED:`.
3. Confirm: reply `done agent-commit-identity A-1`; once AC-1 is built, `kanon github check` prints no `bot_user_id` line.

## 4. Review

Not yet reviewed.

## 5. Decision

Pending.

## 6. Cost

Recorded when work starts.
