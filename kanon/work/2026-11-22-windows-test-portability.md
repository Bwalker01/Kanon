---
type: work
status: in-progress
updated: 2026-11-23
---

# Windows Test Portability

> **Summary:** Fixes the 9 original Windows failures and adds a pull request check. After merging `main`,
> 30 Windows failures from `main`'s newer code remain (492 passed); the owner chose to fix them here.
> **Decision needed:** None until review passes; then merging pull request #4 is the approval.

## 1. Plan

| Field | Value |
|---|---|
| Output | Test changes in `tests/`; one GitHub Actions workflow, `.github/workflows/check.yml`; round 3: Windows fixes in `src/kanon/guard.py`, the guard hook command in `src/kanon/sync.py`, and tests from `main` |
| Inputs | Local run on Windows 11, Python 3.13.7: 9 failed, 191 passed (2026-11-22); owner request for CI on pull requests (2026-11-23); ADR-007 |
| Acceptance | All tests pass on Windows and Ubuntu in CI on pull request #4; no assertion is weakened on POSIX; `kanon verify` passes in CI with full history |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### Causes and Fixes

| Tests | Cause | Fix |
|---|---|---|
| Five in `test_verify.py` | Tests write text without `encoding`, so Windows writes cp1252; `verify` reads UTF-8 | Pass `encoding="utf-8"` to every text read and write in `tests/` |
| `test_init_writes_shared_files_and_generated_files` | `files_in` builds paths with `str()`, giving backslashes | Use `as_posix()` |
| `test_profile_sources_and_precedence`, `test_profile_folder_is_private` | Windows `os.chmod` sets only the read-only flag ([Python `os.chmod` documentation](https://docs.python.org/3/library/os.html#os.chmod)), so POSIX mode bits cannot be asserted | Assert the mode bits on POSIX only; the profile folder relies on the user profile's ACL on Windows (assessment) |
| `test_default_log_dir_follows_claude_code_naming` | Expected value assumes a POSIX path; on Windows the path resolves to `C:\home\user\Mercatus` | Use a platform-appropriate example path; the code already matches Claude Code's Windows naming (observed folder `C--Users-...-Kanon`) |

### Round 3: Failures From `main` (30)

| Tests | Cause | Fix |
|---|---|---|
| 25 in `test_guard.py` | The guard judges Bash commands but uses `os.path`, which on Windows applies Windows path rules (`\home\user`), so project and protected paths never match | Use POSIX path rules on every platform; convert Windows paths (`C:\Users\x`, `C:/Users/x`) to the Git Bash form (`/c/Users/x`); compare case-insensitively on Windows; treat `rm.exe` as `rm` |
| Guard hook command (local finding) | It runs `python3`, which on Windows can be the Microsoft Store stub, so the guard silently never runs | Try `python3`, `python` and `py` in turn and use the first that runs |
| Others in `test_guard.py`, `test_branch.py`, `test_github.py`, `test_init.py` | To be diagnosed: text written without `encoding`, POSIX permission bits, a Windows path written into a shell script | Fix the tests, or the code where a test exposes a real defect |

### Pull Request Check

| Item | Choice | Basis |
|---|---|---|
| Trigger | `pull_request` into `main`, when opened, reopened or marked ready; drafts skipped; no run on push | ADR-015 (owner, 2026-11-23), amending ADR-007's "once per pull request" |
| Jobs | Ubuntu with Python 3.11 (the minimum in `pyproject.toml`) and Windows with Python 3.13 | The minimum version on Ubuntu and one current version on Windows; Python 3.12 and 3.14 are not tested (assessment: adequate for this project's size) |
| Steps | Full-depth checkout without stored credentials; `uv sync --locked`; `uv run pytest -q`; `uv run kanon verify` | `kanon verify` needs full history (Phase 1 plan, K-52) |
| Cost | No model calls; Actions minutes are free for public repositories, and `Bwalker01/Kanon` is public | `gh repo view` (2026-11-23); [GitHub Actions billing](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions) |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-22 | Fix the Windows test failures? | Owner: "Yes, fix them" |
| 2026-11-22 | Should `usage.default_log_dir` match Claude Code's drive-letter case (a `c--...` folder exists beside `C--...` folders on the owner's machine)? | Open; outside this work. Recorded for the usage code. |
| 2026-11-23 | Add CI checks on pull requests? | Owner: add capability to run CI checks on pull request creation, as part of this work |
| 2026-11-23 | ADR-007 says the check runs "once per pull request". Keep runs on each push (recommended, so fixes pushed to a pull request are checked), or run only when the pull request is opened? Default: each push. | Owner (2026-11-23): neither; the check runs when the pull request is marked ready, and drafts are skipped. Recorded in ADR-015 and `2026-11-23-pull-request-lifecycle.md`. |
| 2026-11-23 | Owner: update the branch from `main` and fix the local configuration (`kanon/sources.md`, section 19). | Done: `main` merged (1ca374d); `kanon sync` and `kanon init` installed the guard, Atlas skill and git hooks; uv added to the user PATH; `core.autocrlf=input` for this repository. Not done: the guard runs `python3`, which is the Microsoft Store stub on this machine, so it does not run; 82 files keep CRLF until checked out again. |
| 2026-11-23 | After the merge, 30 tests fail on Windows in `main`'s code (25 `test_guard`, 2 `test_branch`, 2 `test_github`, 1 `test_init`), so the Windows check job fails. Fix them in this work (recommended), or narrow this work and stop requiring the Windows job until separate work fixes them? Default: fix them here. | Owner: "Fix them here" |

## 3. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| 1 | Test fixes (d118f54) | Kritos | Pass with notes | None | F1: six test calls still used the default encoding; fixed. F2: drive-letter case in `default_log_dir`; recorded as a question. F3: work file not updated after the build; fixed. F4: Windows privacy untested and the `os.chmod` claim unsourced; source cited, gap stated in the summary. Kritos did not run the suite on Linux; the POSIX assessment comes from reading the diff. |
| 2 | Check workflow (89c1357) | Kritos | Correct | F1, F2, F3 | F1: CI run 45204560417 failed on both jobs; `git pull` in a test needed a committer identity; fixed in the test and confirmed locally with an empty global git config. F2 (blocking, owner): per-push runs against ADR-007's "once"; question raised in section 2. F3 (blocking): the decision entry was stale; reworded. F4, F6: Jobs and Cost rows corrected and sourced. F5: actions pinned by commit SHA to `checkout` v7.0.1 and `setup-uv` v10.3.3 (`setup-uv` publishes no major tag; run 45205703211 failed on `@v10`), credentials not persisted. F7: this row. |
| M1 | Merge (1ca374d) | Kritos | Correct | F-1, F-2 | F-1: 30 Windows failures from `main` make the Acceptance row unreachable; summary corrected, scope question raised. F-2 (lifecycle work): required checks moved to a ruleset. F-5: decision route stated. Others in the lifecycle work file. |

## 4. Decision

| Item | Decision | Date | Basis |
|---|---|---|---|
| Windows test portability | Approved on merge of pull request #4 | 2026-11-23 | ADR-014: the merge is the approval; pending until the merge commit is in history |

## 5. Cost

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| plan, build, review | 5,890 | 5,090 | 42,606 | 1,252,978 | unavailable |
| round 2: CI check | 6,641 | 9,709 | 47,160 | 1,906,492 | incomplete: $0.00 so far |
