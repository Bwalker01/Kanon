---
type: work
status: complete
updated: 2026-11-18
---

# Repository Setup

> **Summary:** One-off owner actions that set up `Bwalker01/Kanon` for Phase 1: the GitHub App, the merge into main, branch protection and the cloud environment.
> **Decision needed:** None.

## 1. Plan

| Field | Value |
|---|---|
| Output | A repository ready for P1-09 and P1-10 |
| Creator | Claude Code (builder session) |
| Reviewer | Owner (confirms each action) |

## 2. Questions

| Date | Question | Answer |
|---|---|---|

## 3. Actions

| ID | Action | Assignee | Blocks | Done |
|---|---|---|---|---|
| A-1 | Generate the GitHub App key pair and install the App on `Bwalker01/Kanon` | Bwalker01 | | yes |
| A-2 | Merge the working branch into `main` without squashing | Bwalker01 | A-3 | yes |
| A-3 | Protect `main`: pull request with one approval required | Bwalker01 | | yes |
| A-4 | Point the "Kanon" cloud environment at `Bwalker01/Kanon` | Bwalker01 | A-5 | yes |
| A-5 | Start a fresh session to prove the setup script | Bwalker01 | | yes |
| A-6 | Optional: ask GitHub Support to purge the rewritten commits | Bwalker01 | | yes |

### A-1: GitHub App

1. Open the App's settings (Developer settings, GitHub Apps, Edit), then Credentials, Key pairs, and generate a key pair.
2. Store the downloaded key outside every repository with permissions 600.
3. Under Install App, install on `Bwalker01/Kanon` only.
4. Confirm: the App appears under the repository's Settings, GitHub Apps.

### A-2: Merge into main

1. Open a pull request from the working branch into `main`.
2. Merge with a merge commit or rebase; never squash, because `kanon verify` reads commit history.
3. Confirm: `main` contains `src/kanon/sync.py`.

### A-3: Protect main

1. Create a ruleset for `main` requiring a pull request with one approval.
2. Keep the Kanon Agent App off the bypass list.
3. Confirm: a direct push to `main` is refused.

### A-4: Cloud environment

1. In the "Kanon" environment's settings, replace `Bwalker01/Mercatus` with `Bwalker01/Kanon` under Repositories.
2. Confirm: new sessions on the environment have the `Bwalker01/Kanon` checkout.

### A-5: Setup script

1. Start a fresh session on the "Kanon" environment with the repository selected.
2. Ask the assistant to read `~/.cache/kanon-setup.log`; it names the folder and lists the files `kanon init` kept or created.
3. Confirm: the log names the repository folder.

### A-6: Purge rewritten commits

1. Ask GitHub Support to remove cached views of unreachable commits in `Bwalker01/Kanon`.
2. Confirm: GitHub Support replies that the views are removed.

## 4. Review

Not yet reviewed.

## 5. Decision

The owner confirmed every action complete on 2026-11-18. The A-5 session had no checkout, so the
install itself remains unproven. The PATH order it reported was corrected in the "Kanon" cloud
environment's setup script on 2026-11-18, through an environment change the owner approved; that
script lives in the environment's settings, not in this repository.

## 6. Cost

Not measured.
