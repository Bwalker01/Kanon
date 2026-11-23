---
type: work
status: in-progress
updated: 2026-11-23
---

# Windows Test Portability

> **Summary:** The test suite passes on Windows (199 passed, 1 skipped). Round 2 adds a pull request
> check on Ubuntu and Windows. One question on how often it runs is open.
> **Decision needed:** R-2 in `kanon/REVIEW.md`, after CI passes on pull request #4.

## 1. Plan

| Field | Value |
|---|---|
| Output | Test changes in `tests/`; one GitHub Actions workflow, `.github/workflows/check.yml` |
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

### Pull Request Check

| Item | Choice | Basis |
|---|---|---|
| Trigger | `pull_request` into `main`, on open, push and reopen; earlier runs on the same branch are cancelled | ADR-007: "One optional check runs once per pull request, without model calls." Running on each push departs from "once"; awaiting the owner (section 2) |
| Jobs | Ubuntu with Python 3.11 (the minimum in `pyproject.toml`) and Windows with Python 3.13 | The minimum version on Ubuntu and one current version on Windows; Python 3.12 and 3.14 are not tested (assessment: adequate for this project's size) |
| Steps | Full-depth checkout without stored credentials; `uv sync --locked`; `uv run pytest -q`; `uv run kanon verify` | `kanon verify` needs full history (Phase 1 plan, K-52) |
| Cost | No model calls; Actions minutes are free for public repositories, and `Bwalker01/Kanon` is public | `gh repo view` (2026-11-23); [GitHub Actions billing](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions) |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-22 | Fix the Windows test failures? | Owner: "Yes, fix them" |
| 2026-11-22 | Should `usage.default_log_dir` match Claude Code's drive-letter case (a `c--...` folder exists beside `C--...` folders on the owner's machine)? | Open; outside this work. Recorded for the usage code. |
| 2026-11-23 | Add CI checks on pull requests? | Owner: add capability to run CI checks on pull request creation, as part of this work |
| 2026-11-23 | ADR-007 says the check runs "once per pull request". Keep runs on each push (recommended, so fixes pushed to a pull request are checked), or run only when the pull request is opened? Default: each push. | Owner (2026-11-23): neither; the check runs when the pull request is marked ready, and drafts are skipped. Recorded in ADR-011 and `2026-11-23-pull-request-lifecycle.md`. |

## 3. Review

| Round | Reviewer | Verdict | Findings |
|---|---|---|---|
| 1 | Kritos | Pass with notes | F1: six test calls still used the default encoding; fixed. F2: drive-letter case in `default_log_dir`; recorded as a question. F3: work file not updated after the build; fixed. F4: Windows privacy untested and the `os.chmod` claim unsourced; source cited, gap stated in the summary. Kritos did not run the suite on Linux; the POSIX assessment comes from reading the diff. |
| 2 | Kritos | Correct | F1 (blocking): CI run 45204560417 failed on both jobs; `git pull` in a test needed a committer identity; fixed in the test and confirmed locally with an empty global git config. F2 (blocking, owner): per-push runs against ADR-007's "once"; question raised in section 2. F3 (blocking): R-2 was stale; reworded. F4, F6: Jobs and Cost rows corrected and sourced. F5: actions pinned by commit SHA to `checkout` v7.0.1 and `setup-uv` v10.3.3 (`setup-uv` publishes no major tag; run 45205703211 failed on `@v10`), credentials not persisted. F7: this row. |

## 4. Decision

Awaiting the owner (R-2).

## 5. Cost

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| plan, build, review | 5,890 | 5,090 | 42,606 | 1,252,978 | unavailable |
| round 2: CI check | 6,641 | 9,709 | 47,160 | 1,906,492 | incomplete: $0.00 so far |
