---
type: work
status: in-progress
updated: 2026-11-25
---

# Agent Commit Identity

> **Summary:** Part of Phase 1 completion: agents commit as the Kanon App (`kanon-agent[bot]`), so the owner's review of an
> App pull request counts and merging needs no bypass. `kanon sync` sets the identity for agent sessions only.
> **Decision needed:** None. Plan approved by Bwalker01 on 2026-11-25.

## 1. Plan

| Field | Value |
|---|---|
| Output | `src/kanon/sync.py` (identity in `.claude/settings.local.json`), `src/kanon/github.py` (`check`, `setup`, record commit), tests, a README line |
| Inputs | The owner's report (section 2); pull requests #6, #9, #10 and #11 read through the App on 2026-11-25; the "Main Protection" ruleset read through the App on 2026-11-25; ADR-014 ("Owner's login") |
| Acceptance | See 1.2 |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### 1.1 Design

| Part | Choice |
|---|---|
| Cause: commits | Every commit on pull requests #6, #9, #10 and #11 is authored and committed as `Bwalker01`, since agents commit with the computer's Git identity. |
| Cause: pusher | The App pushes, so the last pusher is the App, and the ruleset's `require_last_push_approval` is false. |
| Cause: ruleset | The "Main Protection" `pull_request` rule, read 2026-11-25: 1 approval, `require_code_owner_review` true, `dismiss_stale_reviews_on_push` true, `required_review_thread_resolution` true, `require_extra_approval_for_unattributed_changes` true, merge commits only. Classic branch protection on `main` is off (`GET /repos/Bwalker01/Kanon/branches/main`, `protection.enabled` false, 2026-11-25), so only the ruleset applies. |
| Cause: observed | GitHub showed the owner as the last commit's author and did not count the owner's review (owner, section 2). The rule GitHub applied is inferred from that report; GitHub's documentation read on 2026-11-25 does not describe it (assessment). |
| Rule under test | The approver must not be the author of the pull request's last commit (assessment from the owner's report). If GitHub instead excludes anyone who authored any commit, earlier owner commits on the branch still block, and the outcome table says what follows. |
| Simpler option, rejected | Authoring only the "Approved on merge" record commit as the App: agents commit review notes, cost rows and fixes after `kanon github pr` runs, so the last commit would often still be the owner's. |
| Identity | Author and committer `<app_slug>[bot] <<bot_user_id>+<app_slug>[bot]@users.noreply.github.com>`, here `kanon-agent[bot] <357858083+kanon-agent[bot]@users.noreply.github.com>`. The form is the one GitHub uses for its own Actions bot (`41898282+github-actions[bot]@users.noreply.github.com`); 357858083 was read with `GET /users/kanon-agent%5Bbot%5D` on 2026-11-25. |
| Setting | `[github] bot_user_id` in `kanon/kanon.toml`. The owner adds it here (A-1). `kanon github setup` overwrites `app_id`, `app_slug` and `bot_user_id` for the App it creates, looking the ID up, and keeps every other `[github]` key; if the lookup fails, it removes any existing `bot_user_id`, since that ID belongs to the earlier App, and prints `check`'s hint. When only `bot_user_id` is missing or differs, `check` prints `bot_user_id = N` with "under [github]"; when `app_id` or `app_slug` also differ and `[github]` exists, it says "replace the [github] table with" before the block, so a paste never adds a second table. |
| Agent sessions | `kanon sync` (new `ensure_identity`, beside `ensure_guard_hook` and `ensure_permissions`, run only when the hook is in place) sets `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL` in the `env` object of `.claude/settings.local.json` (git-ignored), keeping other keys. `ensure_identity` reads `kanon/kanon.toml` itself, so a parse error is distinguished from a missing setting. Kanon's form is a name matching `^[a-z0-9-]+\[bot\]$` and an email matching `^\d+\+[a-z0-9-]+\[bot\]@users\.noreply\.github\.com$`, compared case-sensitively. Policy (rule 12): the four keys are decided together; if every present key is absent or in Kanon's form, Kanon writes or removes all four, and if any holds another value, Kanon changes none of them and prints a note naming that key. Keys in Kanon's form are removed when `bot_user_id` is removed. A `kanon.toml` that fails to parse, an `env` that is not an object, or a `bot_user_id` that is not a positive integer leaves everything untouched, with a note. A missing `bot_user_id` prints a note naming A-1. Claude Code's settings documentation describes `env` as variables applied to every session (assessment); live check L-1 confirms it. |
| Record commits | The record commit `kanon github pr` makes is authored as the App when `bot_user_id` is set, through the four variables in that `git commit`'s environment. |
| Not changed | Existing history (no rewrite); the `Co-Authored-By` trailer; commits the owner makes in their own terminal, except Kanon's record commit (previous row). |
| Limit: attribution | Attribution only: an agent can override the variables, and the owner's merge stays the approval (ADR-014). Kanon never reads commit authors. |
| Limit: reach | The settings `env` also reaches commands the owner runs inside a Claude Code session and hooks, which would commit as the App (assessment). |
| Limit: cloud pusher | Harness pushes run as the owner (F-4 of `2026-11-23-remote-session-limits.md`), so cloud pull requests still have the owner as pusher; under the rule under test the pusher does not matter, so the fix is expected to work for them too (assessment, untested). |
| Limit: cloud signing | The cloud signing helper (F-9) is untested with a bot committer and might refuse to sign, failing the commit. |
| Risk | `require_extra_approval_for_unattributed_changes` is documented for unattributed Copilot pull requests only; whether it applies to bot-authored commits is untested. With one approver, an extra required approval would bring back the bypass. If it applies, the owner decides whether to turn it off, and the live test repeats. |
| Branches | Plan branch `kanon/agent-commit-identity/plan`, cut from `main` at 2b586b3. One item, `AC-1`, on `kanon/agent-commit-identity/AC-1`. |
| Sequence | 1. Kritos passes the plan. 2. The owner approves it and does A-1. 3. AC-1 built, reviewed by Kritos, merged; `kanon sync` run. 4. Live checks L-1 and L-2 (1.3, A-2); their results are recorded in section 4 and committed by the L-1 session, so that commit is the pull request's last. 5. `kanon github pr`, `notes` and `ready`. 6. The owner approves the pull request on GitHub without the bypass and copies the merge box's text into chat (L-3, A-3); the outcome table in 1.4 gives the next step. Nothing is pushed after that approval, since `dismiss_stale_reviews_on_push` would dismiss it. 7. The owner merges, which approves the result; `kanon github pr` has already written the Decision row. 8. L-3's result reaches `main` through the next App pull request, the cloud-session-parity plan branch, which records it in its own Review section and itself repeats L-3 with all of its last commits made under the new identity. |

### 1.2 Acceptance

| Check | Confirmed by |
|---|---|
| With `bot_user_id` set, `sync` writes the four variables, keeps other keys, and a second run changes nothing | Test |
| Keys in Kanon's form are removed when `bot_user_id` is removed; an owner-set value is kept with a note; with one key owner-set and the others in Kanon's form, no key changes; a name differing from Kanon's form only in case counts as owner-set; a `kanon.toml` that fails to parse , an `env` that is not an object, or a `bot_user_id` that is not a positive integer leaves everything untouched with a note; a missing `bot_user_id` prints the A-1 note; the name follows `app_slug` | Tests, one per case |
| Without the guard hook in place, `ensure_identity` does not run | Test |
| A commit made under the written variables has the App as author and committer, even with `user.*` set in Git config | Test in a temporary repository |
| `check` prints `bot_user_id = N` alone when only it is missing, a "replace the [github] table with" block when `app_id` also differs and `[github]` exists, nothing when all match | Tests with `call` patched |
| `setup` writes `bot_user_id`, overwrites the three App keys when run again for a different App, keeps other `[github]` keys, and removes an existing `bot_user_id` when the lookup fails | Tests |
| The record commit is authored as the App when `bot_user_id` is set | Test |
| L-1 and L-2 recorded with their results before step 5 | Section 4 of this file |
| L-3 recorded with the merge box's text | Review section of `2026-11-25-cloud-session-parity.md`, merged by the next App pull request |
| `uv run pytest -q` and `uv run kanon verify` pass | Command output |

### 1.3 Live Checks

| ID | Who | Check | Pass |
|---|---|---|---|
| L-1 | A new Claude Code session in this folder, started after step 3 | `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT`, then the same from a Kritos subagent | Both show `kanon-agent[bot]` |
| L-2 | The owner, in their own terminal | `git var GIT_AUTHOR_IDENT` | Shows the owner |
| L-3 | The owner, on GitHub | The pull request's last commit, made by the L-1 session with no variables typed, is authored by `kanon-agent[bot]`; the owner approves | The approval counts and the merge box needs no bypass |

### 1.4 Outcomes of L-3

| Result | Meaning | Next step |
|---|---|---|
| Approval counts | The last commit's author was the cause; the fix works | Merge without the bypass |
| Approval does not count; GitHub names unattributed changes or asks for another approval | The ruleset's unattributed-changes setting applies to bot commits | Owner decides whether to turn it off; L-3 repeats |
| Approval does not count; GitHub names the owner as a commit author | GitHub excludes any commit author, and earlier owner commits on the branch block | The rule is recorded; the owner decides between merging with the bypass and a new work file built entirely by an App-identity session, which would repeat L-3 |
| L-1 fails | Claude Code did not apply the settings `env` | Stop; record it; the owner decides between another mechanism and the bypass |
| L-2 fails | The settings `env` reaches the owner's own terminal | Stop; `kanon sync` removes the keys (bot_user_id removed); record it |
| Any other result | Not explained by the rows above | Record the merge box's text; the owner decides |

### 1.5 Work Items

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
| A-1 | Add the App's bot user ID to `kanon/kanon.toml` | Bwalker01 | | yes |
| A-2 | Check the owner's terminal identity (L-2) | Bwalker01 | | no |
| A-3 | Approve the pull request on GitHub and report the merge box (L-3) | Bwalker01 | | no |

### A-1: Bot User ID in kanon.toml

Sequence step 3 waits for this action.

1. After approving the plan, open `kanon/kanon.toml` on the branch `kanon/agent-commit-identity/plan`.
2. Under `[github]`, below `app_slug`, add the line `bot_user_id = 357858083` and commit it with a message starting `MODIFIED:`.
3. Confirm: open `https://api.github.com/users/kanon-agent%5Bbot%5D` in a browser and check that `id` is 357858083; reply `done agent-commit-identity A-1`.

### A-2: Owner Terminal Identity

Sequence step 5 waits for this action.

1. After the assistant reports that AC-1 is merged and `kanon sync` has run, open a terminal outside Claude Code in the Kanon folder.
2. Run `git var GIT_AUTHOR_IDENT`.
3. Confirm: the output starts with the owner's own name and email, not `kanon-agent[bot]`; reply `done agent-commit-identity A-2` with the name shown.

### A-3: Approval on GitHub

Sequence step 7 waits for this action.

1. When the assistant gives the pull request link after `kanon github ready`, open it on GitHub and approve it without enabling the bypass.
2. Copy the text of the merge box at the bottom of the pull request, including any line about required approvals.
3. Confirm: reply `done agent-commit-identity A-3` with that text; the outcome table in 1.4 gives the next step.

## 4. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| P1 | Plan (b5a2f92) | Kritos (`kritos-reviewer` agent) | correct | C-1, C-2 | C-1: live check L-1 tests that Claude Code applies the settings `env`, in a new session and a subagent. C-2: the rule under test is stated, the "no owner commit" claim removed, and the outcome table added. Non-blocking C-3 (ruleset recorded, simpler option rejected), C-4 (`setup` writes and keeps keys), C-5 (no duplicate table), C-6 (edge cases and policy), C-7 and C-8 (limits), C-9 (A-1 confirmable now; step 3 waits for it) and C-10 (format sourced) applied. |
| P2 | Plan fixes (87e3eaa) | Kritos (`kritos-reviewer` agent) | correct | C-11 | C-11: Kanon changes or removes the identity keys only when absent or in its own form; an unreadable `kanon.toml` leaves them untouched. Non-blocking C-12 ("replace the table" wording), C-13 (L-2 and catch-all rows, merge box text), C-14 (nothing pushed after the approval; L-3 recorded after merge), C-15 (record commit exception), C-16 (`setup` overwrites the App keys; lookup failure), C-17 (A-1 note restored; documentation cited), C-18 (cloud expectation) and C-19 (classic protection off, read through the App) applied. |
| P3 | Plan fixes (d621c04) | Kritos (`kritos-reviewer` agent) | correct | C-20 | Round limit reached. C-20: L-1 and L-2 recorded before step 5; L-3 reaches `main` through the cloud-session-parity pull request; the Decision row is written by `kanon github pr`. Non-blocking C-21 (Kanon's form as patterns; four keys decided together; mixed-case test), C-22 (`ensure_identity` reads `kanon.toml`), C-23 (`setup` removes a stale `bot_user_id`), C-24 (Actions A-2 and A-3), C-25 (owner decides after the "any commit author" outcome) and C-26 (Cause and Limits split) applied. These fixes were not independently reviewed: owner decides between approving the plan and a round P4.. Owner reviewed 2026-11-25 |
| R1 | AC-1 (2a44a2f) | Kritos (`kritos-reviewer` agent) | pass | None | All test rows of 1.2 met. Non-blocking D-1 (unusual `[github]` layouts gave a duplicate table), D-2 (setup lookup failure untested), D-3 (CRLF), D-4 (validation untested), D-5 (missing slug) and D-6 (README wording) applied in 2b4e715. |
| R2 | AC-1 fixes (2b4e715) | Kritos (`kritos-reviewer` agent) | pass | None | D-1 to D-6 resolved. Non-blocking D-7 (setup refusal and CLI untested), D-8 (no instruction to remove an earlier App's `bot_user_id`), D-9 (problem text discarded), D-10 and D-11 (tests) and D-12 (formatting) applied in 4b35f59. |
| R3 | AC-1 fixes (4b35f59) | Kritos (`kritos-reviewer` agent) | pass | None | D-7 to D-12 resolved, each confirmed by a mutation run. Non-blocking D-13 (the refusal message names `kanon.toml` twice), D-14 (the removal instruction is printed inside the key block) and D-15 (`setup` does not say when `bot_user_id` is missing; `check` prints it) recorded as known limits of the setup output; round limit reached, so no further change. |

## 5. Decision

| Item | Decision | Date | Basis |
|---|---|---|---|
| Plan | Approved | 2026-11-25 | Owner in chat: "identity plan approved.". Transcribed by the assistant for Bwalker01; commit `43c9ab4`; material: plan; sha256:32866b5d8a608cee9aa148d378c0d63d8196f823683cf9924f9800362abdf470 |

## 6. Cost

Recorded when work starts.
