---
type: doc
status: current
updated: 2026-11-18
---

# Owner Setup Steps

> **Summary:** Step-by-step instructions for the actions listed in `kanon/REVIEW.md` that only the
> owner can perform. Complete them in the order given; each section states how completion is confirmed.

## 1. Finish the GitHub App

The App "Kanon Agent" exists (Client ID `Iv23liMYmfn7dkDjKo5i`).

1. Open https://github.com/settings/apps, select **Edit** next to Kanon Agent, then **Credentials** and the **Key pairs** tab.
2. Generate a key pair. The browser downloads a `.pem` file; GitHub keeps no copy.
3. Store it outside every repository, for example `~/.config/kanon/github-app.pem`, readable only by you (`chmod 600`).
4. In the App's menu, select **Install App**, then **Install** on your account, **Only select repositories**, and `Bwalker01/Kanon`.

**Confirmed when:** the App appears under the repository's Settings, **GitHub Apps**. Do not send the key in chat.

## 2. Merge This Branch into main

`main` lacks everything since Phase 0, including `kanon sync`, which new cloud sessions need.

1. Open a pull request from `claude/stoic-knuth-mud2jv` into `main`, or ask the assistant to open it.
2. Merge it with **Create a merge commit** or **Rebase and merge**. Do not squash: `kanon verify` reads commit history to check that plans came before builds.

**Confirmed when:** `main` contains `src/kanon/sync.py`.

## 3. Protect main

Do this after step 2.

1. In the repository, open **Settings**, **Rules**, **Rulesets**, and create a branch ruleset for `main` (or use **Branches** for a classic rule).
2. Require a pull request before merging, with one approval.
3. Require status checks to pass: `ubuntu-latest / Python 3.11` and `windows-latest / Python 3.13` (ADR-011). They appear in the list after the check has run once.
4. Do not add the Kanon Agent App to the bypass list.

**Confirmed when:** a direct push to `main` is refused, and a pull request without a passing check cannot be merged.

## 4. Point the Cloud Environment at the Renamed Repository

The cloud environment "Kanon" still lists `Bwalker01/Mercatus`, and this session's GitHub API access is tied to that name.

1. In the Claude app, open the environment settings for "Kanon" and replace `Bwalker01/Mercatus` with `Bwalker01/Kanon` under **Repositories**.
2. Start the next session with `Bwalker01/Kanon` selected.

**Confirmed when:** the assistant can read pull requests on `Bwalker01/Kanon`.

## 5. Check the Cloud Setup Script

After steps 2 and 4, start a fresh session on the "Kanon" environment and ask the assistant to read `~/.cache/kanon-setup.log`.

**Confirmed when:** the log names the repository folder and `kanon init` lists the generated files.

## 6. Optional: Purge Old Commits

The branch history was rewritten on 2026-11-18 to remove profile data. GitHub may still serve the old
commits to anyone holding their hashes. If that matters, ask GitHub Support to remove cached views of
unreachable commits in `Bwalker01/Kanon`.
