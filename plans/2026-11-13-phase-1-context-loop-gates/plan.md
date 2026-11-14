---
name: Phase 1 slice plan
description: The next slice in full - kanon init, templates, the Koine Loop as Claude Code skills, tamper-evident approvals, kanon verify, token measurement, and one requirement run end to end in this repository
type: plan
status: awaiting-owner-approval
date: 2026-11-13
tags:
  - type/plan
  - project/kanon
  - stage/phase-1
aliases:
  - Phase 1
  - Phase 1 slice
---

# Phase 1: context layer, loop and gates

Shape follows AutoBuild's `autobuild-plan` skill: a decision brief, one block of owner
inputs, the next slice in full, and one line for each later item.

## 1. Decision brief

**Outcome.** After Phase 1, running `kanon init` in an empty Git repository gives it the
Kanon layout, instructions for Claude Code, and four core roles. A person can then ask
Claude Code for something and watch it go through the Koine Loop: refined into a
requirement, approved at a gate, planned, approved again, drafted, reviewed by an
independent reviewer, corrected, approved, and filed as documentation. `kanon verify`
fails if any step was skipped. Example: in this repository, the owner asks for a
`kanon status` command; the result is an approved requirement, an approved plan, the code,
its review files, its documentation, and a record of what each step cost in tokens.

**Where things stand.** Phase 0 laid out this repository by hand and recorded ten
decisions. No code exists. Two probes in Phase 0 changed the design:

1. **Approvals.** The assistant can obtain a terminal (`script`) and can write files, so a
   local approval cannot prove a person gave it (learning, 2026-11-13). Phase 1 therefore
   builds **tamper-evident** approvals: each records a hash of exactly what was approved,
   and `kanon verify` rejects an approval whose material has changed since. Claude Code
   permission rules are added to make forging harder, and Phase 1 tests and documents what
   they do and do not stop. Tamper-proof approval waits for GitHub mode with a separate
   identity (Phase 3, ADR-009).
2. **Token use.** Claude Code 2.1.323 writes per-message token usage (input, output, cache
   writes, cache reads) to its session log under `~/.claude/projects/`. Kanon can read it
   to report cost per loop step. The format is internal and undocumented, so Kanon reads
   it defensively and reports "unknown" rather than guessing if it changes.

**Scope.** In: the Python package and command; templates; `init`; `verify`; `approve`; the
four core roles as Claude Code skills; usage reporting; one real run. Out: Pinax tickets
and the roster (Phase 2), GitHub (Phases 2 and 3), the Pantheon (Phase 4), engine mode
(Phase 3).

**Authority.** The owner approves this plan and each major gate. Within the approved scope,
the builder chooses routine implementation details (libraries, internal structure) and
records significant ones in the build documentation. A change to outcome, scope,
architecture or a gate goes back to the owner.

**Uncertainty.** What Claude Code permission rules can block (P1-05). Whether skill
auto-invocation is reliable enough (Koine reports about 70%; plans therefore name skills
explicitly). How much the loop costs per step (measured in P1-07, not assumed).

**Acceptance and rollback.** Phase 1 is done when P1-08 passes. Everything is on the
working branch until the owner approves; rollback is not merging it.

## 2. Owner inputs

Asked as questions on 2026-11-14 rather than left for the gate (ADR-011); the record is in
[questions.md](questions.md).

| # | Input | Answer |
|---|---|---|
| O1 | Your approver identity, written `role@host` like Pinax actors | Default: `owner@<your machine name>` |
| O2 | Copyright holder name in `LICENSE` | Default: `Bwalker01` |
| O3 | Rename the GitHub repository from `Mercatus` to `kanon` | **Rename now** (owner does it in GitHub settings; references updated after) |
| O4 | Independent reviewer subagents in this session | **Allowed** |
| O5 | Review round limit | **3** |
| O6 | The requirement(s) to run end to end in P1-08 | **Both:** `kanon status` (dashboard summary and open gates), then `kanon questions` (open questions across plan folders) |
| O7 | Packaging tool for development | Default: `uv` |

## 3. Next slice, in full

Each item: what it delivers, what it depends on, the paths it may change, how acceptance
is checked (designed so a wrong result fails), and when to stop and ask.

### P1-01 Package skeleton

- **Delivers:** the `kanon-engine` package (Python 3.11+, MIT) with a `kanon` command
  offering `--version` and `--help`; a test suite; a `pre-commit` style local check script.
- **Depends on:** nothing.
- **Item nature:** repository.
- **Declared paths:** `pyproject.toml`, `src/kanon/**`, `tests/**`.
- **Acceptance:** `pipx install .` in a fresh environment, then `kanon --version` prints
  the version in `pyproject.toml`; the test suite passes; a test that the version is read
  from one place fails if a second hard-coded version is added.
- **Stop and ask if:** the name `kanon-engine` is no longer free on PyPI.

### P1-02 Templates and the frontmatter schema

- **Delivers:** templates for requirement, feature, build, fix, idea, decision, plan,
  draft, review, gate, approval, questions log, daily log, dashboard and INDEX; one schema
  saying which frontmatter fields each document type requires; a person profile (level,
  the person's own description, areas they know well) in the `kanon.toml` template
  (ADR-011).
- **Depends on:** P1-01.
- **Declared paths:** `src/kanon/templates/**`, `src/kanon/schema.py`, `tests/**`.
- **Acceptance:** every template validates against the schema; for each required field, a
  test removes it and the validation fails naming that field; the review template contains
  the verdict values `pass`, `correct`, `escalate`, `park` and a blocking flag per finding
  (AutoBuild's rules); every template passes the writing check from P1-04.
- **Stop and ask if:** a document type needs a field not in Koine's minimum set plus the
  type-specific ones above.

### P1-03 `kanon init`

- **Delivers:** a command that lays out a repository as in foundation plan section 3.1:
  `AGENTS.md` (or a marked Kanon section appended to an existing one), `CLAUDE.md`
  importing it, `docs/**` with INDEX files, `docs/standards/conduct-and-writing.md`,
  `plans/INDEX.md`, `kanon.toml`, and the Claude Code files from P1-06. It asks the person
  running it the technical-level question (ADR-011) and writes their profile; with
  `--non-interactive` it records the level as unset and agents ask at first contact.
- **Depends on:** P1-02 (P1-06 for the Claude Code files; init ships without them until
  P1-06 lands).
- **Declared paths:** `src/kanon/init.py`, `src/kanon/templates/**`, `tests/**`.
- **Acceptance:** in an empty temporary Git repository, `kanon init` creates exactly the
  expected file list (compared against a fixed list, so an extra or missing file fails);
  running it twice changes nothing; an existing `AGENTS.md` keeps its original text
  byte-for-byte above the Kanon section; no existing file is ever overwritten or deleted.
- **Stop and ask if:** a target repository has a layout that conflicts with Kanon's folder
  names.

### P1-04 `kanon verify`

- **Delivers:** mechanical checks from foundation plan section 5.1 that need no Pinax or
  Pantheon: plan committed before its first draft (from Git history); every draft has a
  review by a role other than its creator; every major-gate output has a valid approval;
  loops over the round limit were escalated; frontmatter present and valid; every
  document listed in its folder's INDEX; the writing check from the conduct and writing
  standard (em and en dashes, the listed phrases; the standard itself is exempt from the
  phrase list); a question first raised in a `gate.md` that is not in the plan folder's
  `questions.md`. Clear messages naming file, line and rule. A Git pre-commit hook that
  runs it, installed by `init`.
- **Depends on:** P1-02.
- **Declared paths:** `src/kanon/verify/**`, `src/kanon/hooks/**`, `tests/**`.
- **Acceptance:** a fixture repository that follows every rule passes. For **each** rule, a
  copy of that fixture breaking exactly that rule fails, with a message naming the rule.
  This repository (Phase 0 content) is run through it; any failure is either fixed or
  listed as a known exception in the build documentation.
- **Stop and ask if:** a rule cannot be checked from files and Git history alone.

### P1-05 Tamper-evident approvals and permission rules

- **Delivers:** `kanon approve <plan-folder>` and `kanon request-changes <plan-folder>`,
  which record the decision, the approver (O1), the time, the commit, and a hash of every
  file the gate covers. `kanon verify` rejects an approval whose files have changed since.
  `init` writes Claude Code permission rules that deny the assistant `kanon approve` and
  edits to `approval.md` files.
- **Depends on:** P1-03, P1-04.
- **Declared paths:** `src/kanon/approve.py`, `src/kanon/verify/**`,
  `src/kanon/templates/claude/**`, `tests/**`, `docs/learnings/**`.
- **Acceptance:** (a) changing one character in approved material makes `verify` fail and
  name the file; (b) in a Claude Code session in this repository, asking the assistant to
  approve a gate is refused by the permission rules, recorded with the exact prompt and
  response; (c) the ways the rules can still be bypassed are tested and written up in the
  approval learning. Nothing is claimed that was not tested.
- **Stop and ask if:** Claude Code's rules cannot cover file edits by path, which would
  change how much protection Phase 1 can offer.

### P1-06 The four core roles as Claude Code skills

- **Delivers:** runtime-neutral role prompts (coordinator Metis, reviewer Kritos, scribe
  Clio, context keeper Mnemon) in `src/kanon/prompts/`; thin Claude Code wrappers in Agent
  Skills format; the reviewer as a Claude Code subagent with read-only tools that receives
  the specification, the draft or diff and check results, and never the creator's
  conversation. Every role prompt carries the conduct and writing standard and reads the
  person's profile. The reviewer runs a writing review on prose documents against the
  standard's reviewer list. The coordinator asks questions as gaps appear and logs them in
  `questions.md`; it suggests a profile change when the conversation shows a mismatch and
  never makes one without the person's confirmation.
- **Depends on:** P1-02.
- **Declared paths:** `src/kanon/prompts/**`, `src/kanon/templates/claude/**`, `tests/**`.
- **Acceptance:** every skill passes the Agent Skills naming rules (lowercase, hyphens,
  at most 64 characters, matches its folder); every wrapper is at most 30 lines and
  points at its prompt by path (Koine's rule); every generator names its paired reviewer;
  the reviewer definition grants no write tools; every role prompt references the conduct
  standard by path rather than copying it; the reviewer's writing review fails a test
  document seeded with three listed patterns and passes a clean one. Each check has a test
  that fails when the rule is broken.
- **Stop and ask if:** Claude Code cannot keep a subagent from seeing the parent
  conversation.

### P1-07 Token usage per loop step

- **Delivers:** `kanon usage <plan-folder>`, which reads the Claude Code session logs for
  the time window of each loop step and writes `usage.md` in the plan folder: input,
  output, cache-write and cache-read tokens per step and in total. If a log is missing or
  its format is unrecognised, the step reads "unknown" with the reason.
- **Depends on:** P1-01.
- **Declared paths:** `src/kanon/usage.py`, `tests/**`.
- **Acceptance:** on a recorded sample log (trimmed and anonymised), totals equal
  independently computed values; a log with an unknown field layout gives "unknown", not
  zero; a step with no matching messages gives zero with a note.
- **Stop and ask if:** session logs cannot be matched to loop steps by time and working
  directory.

### P1-08 One requirement, end to end, in this repository

- **Delivers:** the two requirements from O6, each carried through the whole loop with
  Kanon itself: `kanon status` first, then `kanon questions`. The second run is compared
  with the first for rounds, questions and tokens.
- **Depends on:** P1-03 to P1-07.
- **Declared paths:** whatever the approved plan for O6 declares, plus `docs/**` and
  `plans/**`.
- **Acceptance (Phase 1 "done when"):** the plan folder contains, in committed order: the
  requirement, its approval, the plan, its approval, draft or code, at least one review by
  the reviewer subagent, a correction if the review asked for one, the documentation
  update, the final approval, `questions.md` with every question asked during the run, and
  `usage.md`. `kanon verify` passes, including the writing check on every new document. Removing any one of
  those files makes `kanon verify` fail. An attempt by the assistant to approve its own
  gate is refused.
- **Stop and ask if:** the loop does not converge within the round limit; the owner then
  decides.

**Order:** P1-01 → (P1-02, P1-07) → (P1-03, P1-04, P1-06) → P1-05 → P1-08.

**Gates in this slice:** for each O6 requirement, the owner approves the requirement, its plan, and its final
output (P1-08); the build documentation for P1-01 to P1-07 is approved as one gate before
P1-08 starts, keeping gates few (ADR-004, ADR-009 cost rules).

## 4. Later items, one line each

- **Phase 2:** Pinax built in; plans become tickets; roster and capability matching;
  onboarding flow; optional GitHub Project board (no Actions minutes).
- **Phase 3:** engine mode with a Claude Code harness port; AutoBuild as the software
  builder's tool; ticket and feature branches; pull requests with generated breakdown and
  reviewer notes; Kanon's own GitHub identity; per-ticket token budgets.
- **Phase 4:** the `pantheon` repository; submission checks, AI review and maintainer
  approval; `kanon pantheon search`, `add`, `update`; `kanon.lock`; first entries.
- **Phase 5:** first outside project; four-weekly review; other assistants.

## 5. Configuration

- **Validator** (the one command that must pass): `python -m pytest -q` plus
  `kanon verify` once it exists.
- **Models:** builder and coordinator on the session's model; reviewer subagent on the same
  model by default (O4). Whether a different reviewer model helps is measured, not assumed.
- **Design checks** the reviewer applies to every item: no file is ever deleted or
  overwritten by Kanon; no check is claimed that has no failing test; nothing reads
  `docs/sources/` as working input; no model call where a file read would do.
- **Reviewer severity:** a finding is **blocking** only if the reviewer would not accept
  the change as it stands (AutoBuild's rule); everything else is non-blocking and recorded.
