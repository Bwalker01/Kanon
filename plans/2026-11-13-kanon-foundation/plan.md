---
name: Kanon foundation plan
description: Research findings on Koine-OS, Pinax, AutoBuild and Ergasterion, and a phased plan for building Kanon, an importable context engine with a marketplace of specialist agents run through the Koine Loop
type: plan
status: draft-v4-awaiting-owner-approval
revision: 4
date: 2026-11-13
tags:
  - type/plan
  - project/kanon
  - stage/foundation
aliases:
  - Kanon plan
  - Oikos plan
  - Mercatus plan
  - Foundation plan
---

# Kanon: research findings and foundation plan

> **Status:** revision 4, for the owner's approval. The owner's answers and decisions are
> recorded in section 11 and folded into every section they affect. Section 13 lists what
> changed. Nothing is built yet.
>
> **Names** (owner decision D8): the engine is **Kanon** (κανών, a measuring rod; a rule or
> standard; the root of "canon", the agreed body of authoritative texts). It keeps the
> project's documentation of record and the standard every review measures against.
> The marketplace is the **Pantheon**. Both replace
> the working name Mercatus, which is Latin and itself means "marketplace". The GitHub
> repository is still called `Mercatus` until the owner renames it.
>
> **How to read this:** each claim about an existing project is marked **[Evidence]** with
> the file it comes from. Each design choice is marked **[Proposal]** with the evidence
> that supports it. Anything I could not confirm is marked **[Unverified]** or listed as an
> open question. I have not filled gaps with guesses.

---

## 1. Summary

Kanon can be built, and most of the hard parts already exist as working, MIT-licensed
code and method by Georgios Antikatzidis (GitHub `antikas`):

| Need in your brief | What already exists | What is missing |
|---|---|---|
| Shared project context and documentation | Koine-OS method: 11 knowledge disciplines, plan folders, dashboards, daily logs, frontmatter, INDEX drill-down | It is a pack of Markdown you copy by hand. Nothing installs it or enforces it. |
| Independent review before anything is accepted | Koine Loop (paired generator and reviewer); AutoBuild's blind reviewer seat | Koine's own Claude Code adapter says the loop is **not** mechanically enforced |
| Human approval | Koine stage stop points; AutoBuild's plan stage stops for the owner; Pinax `decision` gate | No single, recorded "approved by a person" step for every output |
| Tracking work across agents and people | Pinax: Git-native event-log tracker | Nothing |
| Agents that build code | AutoBuild: harness-neutral build campaigns (Claude Code, Codex, Copilot) | Nothing |
| A marketplace of specialists added on demand | Koine's 12 role archetypes (a vocabulary only); the Agent Skills open standard (a package format) | The registry, the onboarding process, and the trust rules |
| Importable into any repo, works with any model | Pinax and AutoBuild install from PyPI; AutoBuild's harness adapters | A single `init` that sets up everything at once |

**Kanon's job is the missing column:** an installable engine that sets up the context
layer in any repository, enforces the Koine Loop with a recorded human approval at the
end, keeps human-readable documentation current, and onboards specialist agents from a
catalogue as the project needs them.

Two findings from revision 1, now settled by the owner (section 11):

1. **Ergasterion is not an agent harness.** It is a deterministic generator that turns
   YAML declarations into dbt data pipelines, with no AI model inside. **Decision:** the
   marketplace holds two kinds of entry, *agents* (specialist roles) and *tools*
   (programs agents call). Ergasterion is a tool; a data-product engineer agent uses it.
   Everything (data, proofs of concept, security, automation, and so on) is in scope.
2. **"Agora" was an idea, not a repository.** It is background only and sets no
   requirements.

---

## 2. Research findings

All four repositories were cloned on 2026-11-13. Versions are as found that day.

### 2.1 Koine-OS (`antikas/koine-os`, MIT, snapshot v2026.04)

**What it is.** [Evidence: `README.md`] "An open-source pack of methods, prompts, and
templates" for teams using AI daily. "This is a pack, not a product. There is nothing to
install and nothing to host." Teams copy it into their own repository and own the copy.

**The Koine Loop.** [Evidence: `method/the-koine-loop.md`]

> prompt → create → review → adjust → (loop until clean)

- Generators work from a **specification, not intent**. A specification names its
  inputs, the transformation, the output shape, and the reviewer's checks.
- The plan is written to `plans/YYYY-MM-DD-topic/plan.md` **before** the generator runs.
- Each draft is a new file (`draft-v1.md`, `draft-v2.md`); each review is its own file
  (`review-<reviewer>.md`) with pass/fail, findings, required changes and optional
  improvements. The reviewer does not rewrite the draft.
- Three non-negotiable conventions: every generator ships with at least one reviewer;
  every iteration is committed; loops converge in three or four iterations or the setup
  is broken.
- Named anti-pattern: "Letting the generator self-review." Generator and reviewer are
  different prompts even if the same model runs both.

**Where the human sits.** [Evidence: `method/00-overview.md`, "Stop points"] Each stage
ends with a plan file "that the team lead must explicitly approve before the next stage
begins." In the loop itself, the reviewer can be "a person, another AI agent, or both"
[Evidence: `README.md`].

> **Note on your brief:** you described the Koine Loop as "an independent subagent
> reviewer reviews all agent output ... before passing back to a human user for explicit
> approval." That is a **stricter version** of what Koine-OS documents: Koine requires a
> separate reviewer always, and human approval at stage boundaries and plan
> authorisation. Kanon would make *both* mandatory for every output. That is
> compatible with Koine, but it is a choice we are making, not something Koine already
> says. (Settled by owner decision D4: human approval at major gates, section 5.2.)

**What Koine admits it cannot enforce.** [Evidence: `adapters/claude-code/README.md`]
"Skills cannot enforce specifications at the runtime level", "No mechanical enforcement
of the Koine Loop convergence limit", and if a generator runs without its reviewer
"nothing in Claude Code will catch it." The adapter also reports skill auto-invocation at
"approximately 70 percent reliability" (the author's figure; I have not measured it), and
so requires reviewers to be named explicitly in plan files.

This is the strongest argument for Kanon being an **engine** rather than another pack:
an engine can refuse to promote output that has no review file or approval record.

**Knowledge disciplines.** [Evidence: `method/knowledge-discipline.md`] Eleven rules:
single source of truth; archive, never delete; ADDED/MODIFIED/REMOVED commit notation;
required YAML frontmatter (`name`, `description`, `type`, `tags`, `aliases`); append-only
daily log; INDEX.md drill-down; status dashboard read first in every session; learnings as
first-class content; a `sources/` inbox compiled before use; forcing functions (tie each
discipline to a ritual); intent-readiness separation (decided is not the same as
available).

**Role archetypes.** [Evidence: `method/agent-archetypes.md`] Twelve Greek-named
capabilities (Mnemon the rememberer, Kritos the reviewer, Chiron the autonomous builder,
Paideia the educator, Hygeia the auditor, Calliope the long-form writer, Metis the
planner, Echo the note-taker, Daedalus the craftsman, Clio the historian, Hermes the
integrator, Prometheus the foreseer). Key idea: "An agent is defined by what it does (its
capability), not by which tool runs it." The vocabulary is offered, not required. This
maps directly onto your marketplace idea.

**Minimum viable OS.** [Evidence: `method/00-overview.md`] "Ship three to five skills. Not
thirty." "It will not guess: The method interviews." Both support your "blank slate"
requirement.

**Runtimes.** Adapters exist for Claude Code and GitHub Copilot. Wrappers are thin (at most
30 lines) and point at runtime-neutral prompts by path.

### 2.2 Pinax (`antikas/pinax-tracker`, MIT, v0.2.2, Python 3.10+, on PyPI)

[Evidence: `README.md`, `DESIGN.md`, `docs/decisions/`]

- A Git-native tracker. Work items live as an append-only JSONL event log under
  `.ergon/log/`; the board (`.ergon/board.md`) and item pages are generated Markdown,
  committed so people can read them without the tool.
- Commands: `init`, `add`, `claim`, `done --briefing FILE`, `block --gate
  scope|decision|destructive|proposal`, `park`, `dep add`, `ready`, `next`, `status`,
  `verify`, `replay`, `dispatch`.
- Actors are written as `role@host`. Claims resolve deterministically when two agents
  claim one item; claims expire (24 hours by default).
- Each state change is committed and pushed immediately so other clones see it.
- **Deliberate boundary** [Evidence: ADR-004]: Pinax records delivery state only and
  "does not index or synthesise a separate knowledge base." Durable knowledge belongs
  elsewhere. **Kanon is that elsewhere.**

**Role in Kanon:** the work ledger. Every task an agent or person does is a Pinax item.
Its `decision` gate can hold an item until a person approves it.

### 2.3 AutoBuild (`antikas/autobuild-factory`, MIT, v0.9.4, Python 3.11+, on PyPI)

[Evidence: `README.md`, `docs/architecture.md`, `skills/`]

- Runs a build campaign over a ready queue (Pinax or a `BACKLOG.md` table). Each item: a
  **fresh builder** in an isolated Git worktree, the project's validator (tests), then a
  **fresh, blind reviewer** that "sees the approved request, changed files and test
  evidence without the builder transcript", with read-only tools.
- Reviewer verdicts: `pass`, `correct`, `escalate`, `park`. Each finding is marked
  blocking or not. Default limit: two correction rounds. `escalate` starts a specialist
  seat. Anything other than `pass` parks the item.
- Harness-neutral: Claude Code, Codex and GitHub Copilot CLIs behind adapters, plus an
  optional Claude Agent SDK lane. Built as ports and adapters (seven ports: tracker,
  workspace, harness, command, run record, knowledge, progress).
- `autobuild-plan` researches, writes a plan, gets one independent review, registers the
  queue, and **stops before launch** until the owner authorises.
- Stated limits: "Product decisions, public releases and production deployments stay
  outside AutoBuild."
- **Dependency gap:** its `KnowledgePort` has a Koine adapter that shells out to a
  `koine-memory` command [Evidence: `src/autobuild/adapters/koine_knowledge.py`]. That
  command is **not in any public repository** I could find. Kanon can implement this
  port itself.

**Role in Kanon:** the software-build specialist. It already implements builder plus
blind reviewer, which is the Koine Loop for code.

### 2.4 Ergasterion (`antikas/ergasterion`, MIT, v0.6.1, Python 3.11+)

[Evidence: `README.md`, source search]

- "The data product factory: declare the source, emit the pipeline." People write YAML
  declarations; the engine generates a dbt project, Open Data Contract Standard contracts,
  a lineage graph and runtime manifests. "The same inputs create the same files byte for
  byte." DuckDB runs it locally; BigQuery is generated and checked but not run.
- I searched the code for AI or model use. The only hits are two docstrings referring to
  conventions "read by a translation agent". **No model calls exist in the engine.**

**Role in Kanon:** a marketplace **tool**, not an agent (owner decision D2). A
data-product engineer agent uses it: drafts declarations, runs `emit-products --check`,
and hands the output to the reviewer.

### 2.5 Things I found that limit what I can claim

- **Owner instructions are private.** All three of koine-os, pinax-tracker and ergasterion
  have a commit on 2026-09-01: "REMOVED: keep owner agent instructions private". The
  author's own `AGENTS.md` and `CLAUDE.md` are not public. I have not guessed at them.
- **Public repos are projections of private ones.** Pinax and AutoBuild release commits read
  "projected from private commit ...". The public code can change in larger jumps than its
  history shows. All four are pre-1.0. **Kanon must pin versions.**
- **Agora:** an earlier idea with no written record; background only (owner decision D1).

### 2.6 Open standards worth building on

Checked against the standards' own repositories on 2026-11-13. The public websites
(`agentskills.io`, `agents.md`) were blocked by this session's network, so I read their
GitHub sources instead.

| Standard | What it gives Kanon | Evidence |
|---|---|---|
| **Agent Skills** (`SKILL.md`) | A package format for one capability: a folder with `SKILL.md` (required `name`, `description`; optional `license`, `compatibility`, `metadata`, `allowed-tools`) plus `scripts/`, `references/`, `assets/`. Loaded in three steps: about 100 tokens of metadata at startup, the body when activated, files when needed. | `agentskills/agentskills` `docs/specification.mdx`; governance adopted 2026-11-04 as an LF Projects series, Apache-2.0 |
| **AGENTS.md** | A plain Markdown file of project instructions that many coding agents read. The nearest file in the directory tree takes precedence, so subfolders can carry their own. Stewarded by the Agentic AI Foundation under the Linux Foundation. | `agentsmd/agents.md` site source |
| **MCP** | Connects agents to tools and data. Already supported by Claude Code (per Koine's adapter README). | Koine `adapters/claude-code/README.md`; secondary sources say MCP is also under the Agentic AI Foundation **[Unverified against primary source]** |
| **A2A** (Agent2Agent) | A protocol for agents on different servers to talk; each publishes an Agent Card at `/.well-known/agent-card.json`. Latest released spec: 1.0.0. | `a2aproject/A2A` `docs/specification.md` |

**[Proposal]** Use Agent Skills as the marketplace package format and AGENTS.md as the root
context, because both are open, already read by several coding agents, and match Koine's
thin-wrapper and progressive-loading rules. Defer A2A until we need agents that run on
someone else's server (Phase 5).

---

## 3. What Kanon is

**[Proposal]** A Python package and a folder convention.

- **Installed once:** `pipx install kanon-engine`. Python matches Pinax (3.10+) and AutoBuild
  (3.11+), so we target 3.11+ and can import both directly.
- **Started in any repo:** `kanon init` writes a minimal context layer, the
  instructions any coding agent reads, and a Pinax tracker. This copies Pinax's own
  `pinax init` pattern.
- **Claude Code first, any assistant in principle** (owner decision D5). Claude Code is
  the first supported assistant and the only one tested in Phases 1 to 3. Everything the
  loop needs lives in plain files and the `kanon` command, with AGENTS.md as the
  root context, so another assistant needs only a thin adapter, never a second copy of
  the method (Koine's thin-wrapper rule).
- **Proven on itself first** (owner decision D7). This repository is instance number one:
  from Phase 1, Kanon is planned, reviewed, approved and documented with Kanon. A real outside project comes once the core works.
- **Works with whatever model is connected,** in two modes (the same split AutoBuild uses
  between `autobuild-coordinated` and the Python `autobuild` command):
  - **In-session mode (default, no API keys):** the person's own coding assistant (Claude
    Code, Copilot, Codex, or anything that reads AGENTS.md) runs the Koine Loop (as Kanon runs it) through
    installed skills. The `kanon` command does the checking and record-keeping.
  - **Engine mode (later):** `kanon run` drives harnesses headlessly through adapters,
    for unattended work.
- **Enforces, not just suggests.** `kanon verify` (modelled on `pinax verify`) fails if
  any promoted output lacks its plan, its independent review, or its human approval
  record. It runs as a pre-commit hook and in CI. This closes the gap Koine's own adapter
  documents.

### 3.1 What `kanon init` creates (the blank slate)

```text
AGENTS.md                      root context: what the project is, where to look, the loop rules
CLAUDE.md                      one line pointing to AGENTS.md (Claude Code reads CLAUDE.md)
kanon.toml                  instance settings: model adapters, reviewer rules, approvers
docs/
  INDEX.md                     map of all documentation, one line per entry
  status/dashboard.md          current state; read first every session
  daily/YYYY-MM-DD.md          append-only activity log
  requirements/                refined requirements with acceptance criteria (section 4)
  features/  builds/  fixes/  ideas/  decisions/   one folder per document type you named
  learnings/                   lessons that apply across the project
  sources/                     raw input (interviews, notes, links) before it is compiled
  archive/                     superseded documents, with a header saying why
plans/YYYY-MM-DD-topic/        the loop's audit trail (plan, drafts, reviews, approval, final)
.kanon/roster/              the agents currently on the team, one file each
.kanon/agents/  .kanon/tools/   packages pulled from the marketplace (section 6)
kanon.lock                  exact marketplace versions and content hashes in use
.ergon/                        Pinax tracker, holds the work tickets (created by pinax init)
```

Every document carries Koine's required frontmatter. Each folder starts empty except for a
short `INDEX.md` and a template. Following Koine's minimum viable OS, only four roles are
on the roster at the start (section 6.4).

---

## 4. From requirement to working code

**[Proposal, from owner decision D2]** The engine takes a person's requirements, refines
them into actionable steps, turns those into work tickets, and has specialists complete
the tickets using whatever tools they need. Each stage is a run of the Koine Loop (as Kanon runs it)
(section 5). The stages marked **GATE** stop for the person (section 5.2).

```text
 your words ─▶ A INTAKE ─▶ B REFINE ──GATE──▶ C BREAK DOWN ──GATE──▶ D TICKETS
                                                                       │
            ┌──────────────────────────────────────────────────────────┘
            ▼
        E STAFF (onboard missing specialists ──GATE──) ─▶ F EXECUTE (per ticket, loop)
                                                                       │
                                     H RELEASE ◀──GATE── G DOCUMENT ◀──┘
```

| Stage | What happens | Output | Precedent |
|---|---|---|---|
| A Intake | Your request is saved as you wrote it. | `docs/sources/<date>-<topic>.md` | Koine discipline 9 (sources inbox) |
| B Refine | The coordinator interviews you until the requirement has a goal, scope, constraints and **acceptance criteria that a wrong answer would fail**. Missing information is asked for, never invented. | `docs/requirements/<topic>.md` | Koine `prompts/bootstrap-interview.md` ("If any input is missing, halt and ask. Do NOT invent answers."); `autobuild-plan` acceptance rules |
| C Break down | The coordinator, with any specialists the work touches (for example an architect or security reviewer), turns the requirement into a plan of work items. Each item states its inputs, outputs, acceptance check, the capability it needs and the tools it may use. | `plans/<date>-<topic>/plan.md` | Koine specification test (four parts); `autobuild-plan` "next slice in full, later items in one line" |
| D Tickets | Each item becomes a Pinax item with its dependencies and a brief. Code items use AutoBuild's brief format (`Item nature`, `## Declared paths`, acceptance) so AutoBuild can run them unchanged. | `.ergon/` items and briefs | Pinax; AutoBuild `docs/running-autobuild.md` |
| E Staff | Each ticket is matched to a roster agent by capability. If none fits, the coordinator proposes one from the marketplace (section 6.4). | Roster entries | Koine archetypes ("capability-first") |
| F Execute | The assigned specialist does the ticket with its tools, in isolation; the independent reviewer checks it; corrections loop. | Code on a branch, or a document draft; review files | Koine Loop; AutoBuild builder and blind reviewer |
| G Document | The scribe updates the human-facing documents the work changed. | `docs/features/`, `docs/builds/`, `docs/fixes/`, `docs/decisions/` | Owner brief: documentation at the heart |
| H Release | Merge to the main branch, and later release or deployment. | Merged commit, release notes | AutoBuild keeps releases and deployments outside its own scope, so they are a gate here |

**Examples of specialists this pipeline can call** (illustrative; each would be a
marketplace entry, none exists yet): requirements analyst, solution architect,
proof-of-concept builder, software builder (on AutoBuild), security reviewer, test
engineer, automation engineer (CI/CD and scripted workflows), data-product engineer (on
Ergasterion), technical writer.

---

## 5. The Koine Loop (as Kanon runs it)

**[Proposal]** The Koine Loop with an independent reviewer on every output and a human
approval at every major gate. Each step names its precedent.

```text
 1 SPECIFY ─▶ 2 PLAN ─▶ 3 CREATE ─▶ 4 REVIEW (independent) ─▶ pass? ─no─▶ 5 ADJUST ─▶ back to 4
                                                               │            (round limit, then
                                                              yes            escalate to person)
                                                               ▼
                                         6 GATE? ─major─▶ person approves or requests changes
                                               │minor                     │
                                               ▼                          ▼
                                         7 PROMOTE, LOG, LEARN ◀──────────┘
```

| Step | What happens | Written to | Precedent |
|---|---|---|---|
| 1 Specify | Inputs, transformation, output shape and review checks are written down before anything is made. | `plan.md` | Koine "specifications, not intent" |
| 2 Plan | The coordinator names the creator, the reviewer(s), inputs and output path. The plan is committed before the first draft. | `plans/<date>-<topic>/plan.md` | Koine step 1 |
| 3 Create | The named specialist produces a draft in isolation (code in its own Git worktree). | `draft-vN.md` or a branch | Koine step 2; AutoBuild builder |
| 4 Review | A **fresh** reviewer, with a different prompt, read-only tools and **no access to the creator's transcript**, checks the draft against the specification. Verdict `pass`, `correct`, `escalate` or `park`; each finding marked blocking or not. | `review-<reviewer>-vN.md` | Koine step 3; AutoBuild blind reviewer and verdict rules |
| 5 Adjust | The creator revises into a new file. Default limit three rounds, then the item goes to the person with the open findings. | `draft-vN+1.md` | Koine convergence rule (3 to 4); AutoBuild default of 2 corrections |
| 6 Gate | Major outputs stop for the person (section 5.2). Minor outputs go straight on once the reviewer passes them. | `approval.md` for major gates | Owner decision D4 |
| 7 Promote, log, learn | The output moves to its permanent home; `plans/` keeps the history; daily log and dashboard updated; repeated findings become learnings. | `docs/...` | Koine step 5; disciplines 5, 7, 8; Stage 5 |

### 5.1 What `kanon verify` checks

Mechanical checks, run as a pre-commit hook and in CI, modelled on `pinax verify`:

- Every promoted output has a `plan.md` committed before its first draft.
- Every draft has at least one review file from a reviewer other than its creator.
- Every output of a major-gate type has an `approval.md` from a listed human approver,
  pointing at the exact commit that was approved.
- Loops over the round limit were escalated, not quietly continued.
- Every marketplace package in use matches the version and content hash in
  `kanon.lock`.
- Every document has the required frontmatter and is listed in an `INDEX.md`.

### 5.2 Human approval gates

**[Proposal, from owner decision D4]** The person approves at major gates and is shown
the material clearly. Minor outputs are reviewed by the independent reviewer only and
listed in the daily summary so nothing happens out of sight. The split is set in
`kanon.toml` and can be changed per project.

| Major gates (the person approves) | Minor outputs (reviewer only, listed in the daily summary) |
|---|---|
| Refined requirements (stage B) | Daily log entries |
| Plans and work breakdowns (stage C) | Dashboard and INDEX updates |
| Decision records (`docs/decisions/`) | Ticket status changes |
| Documentation of record: features, builds, fixes | Intermediate drafts and review files |
| Bringing in, updating or removing a marketplace agent or tool | Learnings proposed (approved in the four-weekly review) |
| Merging to the main branch; releases; deployments | |

**What the person sees at a gate.** One file, `plans/<date>-<topic>/gate.md`, written in
plain language: what is being asked, what changed, the reviewer's verdict and any
findings left open, what happens on approval, and links to the full material. The person
answers **approve** or **request changes** with comments. Requested changes go back into
the loop at step 5 and return to the same gate.

**Making sure an approval really came from the person.** An assistant working in the
repository can write files, so it could in principle write an `approval.md` itself. This
needs a real control, not a convention:

- **In Claude Code (Phase 1):** approvals are recorded by `kanon approve`, which only
  accepts an answer typed at an interactive terminal, and `kanon init` adds a Claude
  Code permission rule that denies the assistant that command. Claude Code supports
  project permission rules in `.claude/settings.json`. **[Unverified]** whether every
  route around the rule can be closed; Phase 1 must test this before relying on it.
- **On GitHub (Phase 3 onward):** a major gate can be a pull request that the person
  approves under their own GitHub account. The approval then lives outside the assistant's
  reach.

---

## 6. The Pantheon (marketplace)

**[Proposal, from owner decision D3]** One central marketplace holds every agent and
tool; anyone can submit a new one; every Kanon instance can search it and pull entries
in when a project needs them.

### 6.1 Two kinds of entry

| | Agent | Tool |
|---|---|---|
| What it is | A specialist role: instructions, a generator and a paired reviewer | A program agents run |
| Format | An Agent Skills folder (`SKILL.md` plus files) and a `pantheon-agent.yml` manifest | A `pantheon-tool.yml` manifest: how to install it at a pinned version, how to check it works, what it may touch |
| Examples | Security reviewer, proof-of-concept builder, automation engineer | Pinax, AutoBuild, Ergasterion, linters, scanners |
| Precedent | Agent Skills spec; Koine Convention 1 (no generator without a reviewer) | AutoBuild probes every adapter before work begins |

Agent manifest (example):

```yaml
# agents/data-product-engineer/pantheon-agent.yml
id: data-product-engineer
version: 0.1.0
archetype: daedalus                  # optional Koine vocabulary
summary: Designs and changes governed data pipelines.
capabilities: [data-pipeline, data-contract]
generators: [draft-data-product]     # each needs a paired reviewer
reviewers:  [review-data-product]
inputs:  [docs/requirements/*.md, declarations/**/*.yml]
outputs: [declarations/**/*.yml, docs/builds/*.md]
tools:   [ergasterion@0.6.1]         # marketplace tool entries it needs
mcp:     []
assistants: [claude-code]            # tested with
licence: MIT
```

Tool manifest (example):

```yaml
# tools/ergasterion/pantheon-tool.yml
id: ergasterion
version: 0.6.1
summary: Generates dbt data pipelines and data contracts from YAML declarations.
install: pipx install ergasterion-factory==0.6.1
check:   ergasterion --help
writes:  [models/products/**, contracts/products/**, graphs/products/**, manifests/products/**]
network: none
upstream: https://github.com/antikas/ergasterion
licence: MIT
```

The tool's commands, paths and package name above come from Ergasterion's README and
`pyproject.toml`; the exact `check` command will be confirmed when the entry is written.

### 6.2 The central marketplace

**[Proposal]** A public Git repository, `pantheon` (owner decision D8), not a
hosted service, to start.

```text
pantheon/
  agents/<id>/              one folder per agent, each version tagged
  tools/<id>/               one folder per tool
  index.json                generated list of every entry, version, capability and trust level
  SUBMITTING.md             how to submit
  .github/workflows/        the automatic checks
```

Why a Git repository first:

- **Nothing to host,** in line with Pinax and Koine-OS. A browsable website can be
  generated from `index.json` later.
- **Submissions, review and history come free** as pull requests.
- **There is a working precedent.** Claude Code's own plugin marketplaces are Git
  repositories with a catalogue file (`.claude-plugin/marketplace.json`), added by
  `owner/repo` or Git URL (Claude Code documentation, section 14).

### 6.3 Submitting a new entry

1. The author opens a pull request adding `agents/<id>/` or `tools/<id>/`.
2. **Automatic checks** (`kanon pantheon lint` in CI): manifest is complete; the Agent
   Skills `name` rules hold; every generator has a paired reviewer; inputs, outputs and
   tool permissions are declared; licence present; every script listed.
3. **Independent AI review** following the Koine Loop (as Kanon runs it): is the specification clear, are
   the permissions in proportion to the job, does anything in the scripts do something the
   manifest does not declare. Findings are posted on the pull request.
4. **A human maintainer approves and merges.** No entry reaches the marketplace without a
   person's approval.
5. Trust levels: `core` (maintained with Kanon), `reviewed` (passed steps 2 to 4),
   `community` (listed from other catalogues; shown with a warning).

### 6.4 Pulling an entry into a project

1. **Need found.** A ticket needs a capability no roster agent has, or the person asks
   for one.
2. **Search.** `kanon pantheon search <capability>` reads `index.json` from the central
   marketplace and from any extra catalogues listed in `kanon.toml` (for example a
   team's private one).
3. **Proposal at a gate.** The coordinator writes a `gate.md`: which entry, why, what it
   may touch, its trust level, the reviewer's notes. The person approves.
4. **Install.** `kanon pantheon add` copies the entry into `.kanon/agents/` or
   `.kanon/tools/` at that exact version and writes its commit and content hash to
   `kanon.lock`. A copy, not a live link, means the project keeps working if the
   marketplace changes, and `kanon verify` notices if the copy is edited.
5. **Introduce.** A roster file and a short "who joined, what they do, what they may
   touch" entry in the daily log and dashboard.
6. **Update** is a new proposal through the same gate. **Remove** is archive-not-delete
   (Koine discipline 2).

**Starting roster** (always present after `init`), four roles in line with Koine's
"three to five":

| Role | Koine archetype | Job |
|---|---|---|
| Coordinator | Metis | Refines requirements, writes plans and tickets, staffs tickets, writes gate summaries |
| Reviewer | Kritos | Independent review of everything; never produces |
| Scribe | Clio and Paideia | Keeps documentation, daily log, dashboard and INDEX files current |
| Context keeper | Mnemon | Loads the right context per session; compiles `sources/`; flags stale documents |

**First marketplace entries:** tools Pinax, AutoBuild and Ergasterion; agents software
builder (on AutoBuild), security reviewer, proof-of-concept builder, data-product engineer
(on Ergasterion).

### 6.5 Naming entries

**[Proposal, following owner decision D8]** Pantheon agents carry a Greek mythological
name **and** a plain role, always shown together (for example "Kritos, reviewer") so
newcomers know what each does without learning the myths. Koine-OS already says a
team that does not find the names helpful can drop them. Tools keep their upstream
names (Pinax, AutoBuild, Ergasterion), so they stay easy to find on PyPI and GitHub.

Names come first from Koine's twelve archetypes, wherever Koine's own description fits
the role:

| Role | Name | Koine's description |
|---|---|---|
| Coordinator | Metis | "the capability that plans" |
| Reviewer | Kritos | "the capability that reviews ... never the producer" |
| Scribe | Clio | "the capability that records" |
| Context keeper | Mnemon | "the capability that holds and reads context across sessions" |
| Software builder | Daedalus | "produces working software, engineered solutions" |
| Autonomous campaign builder (AutoBuild) | Chiron | "builds autonomously ... long-running unsupervised work" |
| Auditor (health, dependencies, security checks) | Hygeia | "runs structural audits, lint checks, dependency reviews" |
| Integrator and automation | Hermes | "cross-system bridges, inter-team handoffs, integration patterns" |
| Risk and threat foresight | Prometheus | "identifies risks before they manifest" |
| Explainer and technical writer | Paideia | "produces explanatory material" |

Roles Koine does not cover (proof-of-concept builder, data-product engineer and others)
get names when their entries are submitted, and the submission review checks that the
name is not already taken in the Pantheon.

---

## 7. GitHub mode (optional)

**[Proposal, from owner decision D9]** Kanon works with nothing but the repository. For
people who want more structure, or larger groups, `kanon github connect` adds GitHub
Projects, branches and pull requests on top. Everything in this section is optional, and
switching it off loses no history, because the repository stays the source of truth.

### 7.1 One source of truth, two views

| | In the repository (always) | On GitHub (GitHub mode) |
|---|---|---|
| Who reads it | Agents, and people who like files | People, especially larger groups |
| Work tickets | Pinax event log in `.ergon/` (**source of truth**) | Issues on a GitHub Project board (a **mirror**) |
| History | `plans/`, `docs/daily/`, Git log | Project board, pull requests and their reviews |
| Review notes | `review-*.md` files | Posted under the pull request |
| Approvals | `approval.md` | Pull-request approval by the person |

Why the repository stays in charge: Koine's first discipline is one source of truth per
fact, and Pinax already gives agents a tracker they can read and write offline with no
network calls. Making GitHub a second, equal tracker would create two records that drift
apart. So Kanon **writes** ticket state to GitHub, and **reads back** only the things that
have to come from people on GitHub: pull-request approvals and change requests, plus any
fields you choose to edit there (for example priority), which are imported as Pinax
events.

### 7.2 The Project board

One GitHub Project per Kanon instance, created by `kanon github connect` with these
fields. Every field is a standard Projects field type (single select, text, number), set
through the `gh project` commands (checked in `gh` 2.89: `item-add`, `item-edit`,
`field-create`; they need the `project` token scope).

| Field | Values | Fed from |
|---|---|---|
| Status | Backlog, Ready, In progress, In review, Awaiting approval, Done, Parked | Pinax state, plus the gate |
| Stage | Intake, Refine, Break down, Execute, Document, Release (section 4) | Plan |
| Kind | Requirement, Feature, Build, Fix, Idea, Decision, Tool | Ticket |
| Agent | The specialist assigned, for example Daedalus | Roster |
| Review round | 0, 1, 2, 3 | Review files |
| Est. tokens | Running estimate for the ticket | Usage log (section 8) |
| Tool lifecycle | Proposed, In development, In review, Approved, Released | Pantheon entries being built or adopted |

Saved views: **Board** by Status; **Awaiting you** (Status = Awaiting approval);
**Tools** (Kind = Tool, grouped by Tool lifecycle) to show where each tool is in its
production.

### 7.3 Branches and pull requests

```text
main ◀────────── PR: "Feature: <requirement>"  (the human gate)
  └─ kanon/feature/<topic>               one branch per approved plan
       ├─ kanon/<ticket-id>-<slug>       one branch per ticket, built in its own worktree
       ├─ kanon/<ticket-id>-<slug>       merged into the feature branch after its review passes
       └─ ...
```

- **One branch per ticket,** each built in an isolated Git worktree, as AutoBuild already
  does. A ticket branch is merged into its feature branch only after its independent
  review passes.
- **One pull request per approved plan,** gathering all its tickets, not one per ticket.
  That gives people one place to review a coherent piece of work and keeps notifications
  and review effort down.
- **The pull request description** is generated from the files Kanon already keeps, so it
  costs no extra model call:

  ```markdown
  ## What this delivers            ← from the approved requirement
  ## Tickets                       ← one row each: id, title, agent, review rounds, Project link
  ## Changes by ticket             ← files changed and why, from each ticket's summary
  ## Acceptance evidence           ← test and check results
  ## Documentation updated         ← docs/ files changed
  ## Cost                          ← estimated tokens per ticket and in total
  ## Your decision                 ← what approving merges, what "request changes" sends back
  ```

- **Reviewer notes appear underneath** as a pull-request review of type *comment*: the
  independent reviewer's verdict and findings for each ticket, copied from the
  `review-*.md` files and clearly labelled as the AI reviewer. GitHub does not let you
  approve your own pull request, and Kanon acts with your credentials, so its review is a
  comment and **the approval is yours alone**. A team can later give Kanon its own GitHub
  App or bot account so its notes appear under a separate name.
- **The gate:** you approve (Kanon merges and closes the tickets) or request changes
  (Kanon turns your comments into findings and the ticket goes back to the loop's adjust
  step). This is the pull-request approval gate from section 5.2.

### 7.4 Keeping Actions minutes at zero by default

**[Proposal]** Every GitHub action Kanon takes (creating issues, updating the board,
opening pull requests, posting reviews, reading approvals) runs **from your own machine
through the `gh` command**, so it uses **no Actions minutes**. Kanon checks for new
approvals when you run it, not by waiting on a schedule.

GitHub's December 2025 changelog says Actions stays free on standard runners for public
repositories. Private repositories get a monthly minute allowance by plan; I could not
confirm the current figure because this session's network blocks docs.github.com, so
check it under your GitHub billing settings. The design does not depend on the number.

One **optional** workflow, `kanon-verify.yml`, is offered for groups that want a server-side
check:

- runs only on `pull_request` to `main`, never on every push;
- runs `kanon verify` and `pinax verify` only: file checks, **no AI model calls in
  Actions**, so it costs no tokens there;
- a Linux runner, a 5-minute timeout, and cancellation of any older run on the same pull
  request;
- not needed at all by a solo user or small group: the pre-commit hook runs the same
  checks locally for free. The workflow is a backstop for groups where not everyone has
  the hook installed.

Expected cost: one short run per pull request, and pull requests are per plan, not per
ticket.

---

## 8. Keeping cost down (tokens and money)

**[Proposal, from owner decision D9]** Every model call has to earn its place. The rules
below come from practices already in Koine-OS and AutoBuild unless marked otherwise.

| Rule | How | Evidence or precedent |
|---|---|---|
| **Free checks before paid ones** | Run `kanon verify`, tests and linters before asking a model to review. A draft that fails a mechanical check goes straight back without a review call. | AutoBuild reads triage lines "without a model call"; runs the validator before review |
| **Load only what is needed** | Agents read `INDEX.md` and frontmatter descriptions first and open a full document only when needed. Skills load in three steps. | Koine INDEX drill-down and frontmatter disciplines; Agent Skills progressive disclosure (about 100 tokens of metadata per skill) |
| **Pass files, not conversations** | Agents write results to files; the coordinator reads short summaries and paths, not the full output. The reviewer gets the specification, the diff and the test results, never the creator's transcript. | Koine "multi-agent temp-file pattern"; AutoBuild reviewer evidence pack |
| **Plan only what is next** | The next slice is planned in full; later items get one line each until they come up. | `autobuild-plan`: "detail beyond the next slice costs review rounds and buys nothing" |
| **Cap the loops** | At most three review rounds by default, then the person decides. Never repeat a check on unchanged evidence. | Koine convergence rule; AutoBuild two correction rounds; `autobuild-plan` "never repeated on unchanged evidence" |
| **Right-size the model** | Each role in `kanon.toml` names a model and effort level. Example: a light model for daily-log and INDEX reviews, a strong one for code and security review. | AutoBuild per-seat model and effort |
| **Batch the small things** | Minor outputs (logs, dashboard, INDEX) are reviewed together once per session, not one call each. | Section 5.2 split of major and minor |
| **One pull request per plan** | Fewer, larger review points; the description is built from files with no model call. | Section 7.3 |
| **Budgets that stop work** | Each ticket gets a token budget (set in the plan). Reaching it pauses the ticket at a gate showing what was spent and what is left, instead of carrying on. | AutoBuild usage meters stop a lane at a set level |
| **Show the cost** | Estimated tokens per ticket appear in the ticket, the pull request and the dashboard, so expensive patterns become visible and feed the four-weekly review. | AutoBuild records usage per seat; Koine Stage 5 |
| **Keep the fixed context stable** | Root instructions and skills change rarely and sit at the start of every session, which suits the prompt caching providers offer. | **[Unverified]** how much this saves in in-session Claude Code use; to be measured in Phase 1 |

How usage is measured: in engine mode, from what the harness reports (AutoBuild already
collects usage per seat). In in-session Claude Code mode, Kanon can only record what Claude
Code reports to it, so Phase 1 must find out exactly what that is before promising
per-ticket figures. **[Unverified]**

---

## 9. Model and assistant independence

**[Proposal]** Copy AutoBuild's ports-and-adapters design (evidence:
`docs/architecture.md`; dependency direction enforced by `tests/architecture/`):

- **Phases 1 and 2, in-session:** the work happens inside Claude Code. Kanon installs
  `CLAUDE.md` (pointing at `AGENTS.md`), skills under `.claude/skills/`, subagent
  definitions for the reviewer so it runs in a fresh context, and the permission rule from
  section 5.2. Koine's Claude Code adapter maps each of these primitives already.
- **Phase 3, engine mode:** a `HarnessPort` with Claude Code first. Further adapters
  (Codex, Copilot, direct API) follow AutoBuild's tested pattern and are added when
  someone needs them.
- **Running the reviewer on a different model** from the creator is an option, not a
  default. I have no evidence on whether it helps here, so it should be measured first.

---

## 10. Roadmap

Each phase ends with something you can watch work, run in this repository itself
(owner decision D7).

| Phase | Delivers | Done when |
|---|---|---|
| **0. Foundation** | This plan approved; decision records for D1 to D9; this repo laid out with its own docs structure; repository renamed if you choose | You approve revision 4 and the Phase 1 slice |
| **1. Context layer, loop and gates** | `kanon init`; templates (requirement, feature, build, fix, idea, decision, gate); Claude Code skills for the four core roles; `kanon approve` with the permission rule; `kanon verify` as pre-commit hook; token use recorded per loop step (section 8) | In this repo, one requirement goes intake → refine → gate → plan → gate → draft → independent review → correction → gate → promoted, every file committed. `verify` fails if any step is removed. An attempt by the assistant to approve its own gate is refused. We know what Claude Code reports about token use and record it. |
| **2. Tickets, staffing and the Project board** | Pinax built in; plans become tickets; capability matching; roster files; local catalogue with first agent entries; optional `kanon github connect` mirroring tickets to a GitHub Project (section 7.2) | A plan becomes Pinax tickets that appear on the Project board; one ticket needs a specialist not on the roster; Kanon proposes it, you approve, it joins and completes the ticket. No Actions minutes used. |
| **3. Building code, branches and pull requests** | Engine mode (`HarnessPort`, Claude Code); AutoBuild as the software builder's tool; ticket and feature branches; generated pull-request descriptions with reviewer notes underneath; pull-request approvals as gates; optional `kanon-verify.yml` (section 7.3, 7.4); per-ticket token budgets | A small feature of two or more tickets goes from requirement to one pull request with the full breakdown and reviewer notes, then to merged code on your approval, with its cost shown |
| **4. Central marketplace** | `pantheon` repository; `kanon pantheon lint`, `search`, `add`, `update`; submission checks and AI review in CI; trust levels; `kanon.lock`; first entries (Ergasterion and the data-product engineer, security reviewer, proof-of-concept builder) | An entry submitted by pull request is checked, reviewed, merged, then pulled into a fresh project and used on a ticket |
| **5. First outside project and feedback** | Kanon used on a real project; four-weekly review (Koine Stage 5) with loop metrics; other assistants' adapters as needed | The review produces at least one change to the core, made through the loop |

---

## 11. Owner decisions (2026-11-13)

| # | Question in revision 1 | Owner's answer | Effect on this plan |
|---|---|---|---|
| D1 | Where is Agora? | An idea only, no repository; background | Sets no requirements |
| D2 | Is Ergasterion in scope? | Everything is in scope: refine requirements, create tickets, call tools such as Ergasterion to produce code; specialists for proofs of concept, security, automation and more | Section 4 added; marketplace holds agents and tools (6.1) |
| D3 | How to include Antikas's projects? | The engine pulls them in as needed from a real central marketplace that accepts new submissions | Section 6 rewritten around a central marketplace |
| D4 | Approve every output? | Human approval at major gates (plans, decisions, documentation and similar), shown clearly, with approve or request changes | Section 5.2 |
| D5 | First assistant? | Claude Code now; should work in principle with any assistant | Sections 3 and 9 |
| D6 | Python 3.11+ and MIT? | Agreed | Phase 0 decision record |
| D7 | First real user? | None yet; prove it on this project itself first | Every phase is tested in this repository |
| D8 | Names | Keep Koine's Greek convention. Marketplace: **Pantheon**. Engine: a common ancient Greek word like "Koine", at most 6 letters, easy to spell and say, matching the project's purpose: **Kanon**. | Renamed throughout; section 6.5 naming of entries. Name checks below. |
| D9 | GitHub and cost | Optional GitHub mode: Projects for tickets and tool production, branches merged into reviewable pull requests with a breakdown and reviewer notes. Spare Actions minutes; keep the whole loop token-conscious. | Sections 7 and 8 added; roadmap phases 1 to 3 |

**Name checks for D8** (PyPI and GitHub repository search, 2026-11-13):

- **Kanon.** `kanon` is taken on PyPI, so the package is `kanon-engine` (free) with the
  command `kanon`, the same pattern as `pinax-tracker` and `ergasterion-factory`. About
  1,200 GitHub repositories have "kanon" in the name; the largest has 71 stars, and
  nothing notable is in the AI-agent space. Fit: Koine-OS calls a specification "a
  measurement surface", which is what a kanon is. Watch: some people may type "canon".
- **Pantheon** is a GitHub repository name, not a package, so the busy PyPI name does not
  matter.
- **Considered on the way:** Oikos (chosen, then replaced); Athena (clashes with Amazon
  Athena and several AI-agent projects with almost the same pitch); Parthenon (too long);
  Mentor, Glaux, Stoa, Hodos, Skopos, Biblos (viable, not chosen).
- **Rejected for clashing with tools in the same space:** Telos, Argo, Nous, Mnemosyne,
  Kybernetes, Metis, Noema, Sophia, Sophos, Pragma, Nomos, Praxis, Ethos.

**Still open (none blocks Phase 1):**

- **Repository name.** This repository is still `Bwalker01/Mercatus`. Renaming it to
  `kanon` is done in GitHub's repository settings, and only you can do it.
- **Upstream contact.** Pinax, AutoBuild and Ergasterion would be listed as marketplace
  tools pointing at their PyPI releases, with credit. They are MIT-licensed, so no
  permission is needed, but letting the author know is worth considering. Needed by
  Phase 4.

---

## 12. Risks

| Risk | Evidence | Mitigation |
|---|---|---|
| The assistant approves its own gate | It can write files in the repository | Approval only through an interactive command the assistant is denied (Phase 1, tested); pull-request approvals (Phase 3) |
| A marketplace entry does harm | Agent Skills folders can include `scripts/`; `allowed-tools` is marked experimental | Automatic checks, AI review and human merge on submission; human gate to bring it into a project; pinned copies with content hashes |
| Upstream changes break tools | All four upstream projects are pre-1.0 and released from private repositories | Tool entries pin exact versions; updates go through a gate |
| Reviewers that always pass | Koine anti-pattern "reviewers that cannot fail" | Track pass rates; flag a reviewer with no failures over a set number of items |
| Too many gates slow you down | Not yet measured | Major and minor split (5.2) set per project; one-file gate summaries; revisit at the first four-weekly review |
| Skills do not trigger | Koine reports about 70% auto-invocation in Claude Code (author's figure) | Plans name every agent; `verify` checks the named reviewers ran |
| Review rounds cost money | AutoBuild built usage meters, which suggests a real cost | Section 8: free checks first, round limits, model per role, budgets that pause work, cost shown everywhere |
| GitHub and the repository disagree | Two trackers drift apart (Koine discipline 1) | Pinax is the source of truth; GitHub is written by Kanon and only approvals and chosen fields are read back |
| Actions minutes used up | Private repositories have a monthly allowance | Nothing runs in Actions by default; the optional workflow runs once per pull request, Linux, 5-minute limit, no model calls |
| Kanon's GitHub actions appear as you | It uses your `gh` login | Reviewer notes are labelled as AI; Kanon never approves; a separate GitHub App or bot account is an option for groups |
| Documentation overload | Koine: "It will not produce thirty skills on day one" | Blank slate with four roles; specialists only on need |

---

## 13. Revision history

- **Revision 4 (2026-11-13).** MODIFIED engine name Oikos → Kanon (D8 revised by the owner);
  plan folder renamed to match. Reason: owner wanted a short common Greek word closer
  to the project's purpose.
- **Revision 3 (2026-11-13).** MODIFIED names: engine Mercatus → Oikos, marketplace →
  Pantheon (D8); plan folder renamed to match. ADDED section 6.5 (naming entries),
  section 7 (optional GitHub mode: Projects, branches, pull requests, zero Actions minutes
  by default) and section 8 (keeping cost down) (D9). MODIFIED roadmap phases 0 to 3,
  owner decisions, risks; renumbered sections 7 to 12 as 9 to 14. Reason: the owner's
  naming and GitHub requests.
- **Revision 2 (2026-11-13).** ADDED section 4 (requirement to code); section 5.2
  (gates, and how approvals are protected); section 6 rewritten around a central
  marketplace with agents and tools, submission and pull-in; owner decisions D1 to D7
  recorded. MODIFIED summary, Ergasterion's role, and the model, roadmap and risk sections.
  REMOVED the seven open questions, now answered. Reason: the owner's answers to
  revision 1.
- **Revision 1 (2026-11-13).** First draft: research findings and initial proposal.
  Preserved in Git history.

---

## 14. Sources

Upstream repositories (cloned 2026-11-13):

- [antikas/koine-os](https://github.com/antikas/koine-os): `README.md`,
  `method/the-koine-loop.md`, `method/00-overview.md`, `method/knowledge-discipline.md`,
  `method/agent-archetypes.md`, `adapters/claude-code/README.md`,
  `prompts/bootstrap-interview.md`
- [antikas/pinax-tracker](https://github.com/antikas/pinax-tracker): `README.md`,
  `DESIGN.md`, `docs/decisions/ADR-004-separation-enforcement.md`
- [antikas/autobuild-factory](https://github.com/antikas/autobuild-factory): `README.md`,
  `docs/architecture.md`, `docs/running-autobuild.md`, `skills/autobuild-plan/SKILL.md`,
  `skills/autobuild-coordinated/agents/autobuild-reviewer.agent.md`,
  `src/autobuild/adapters/koine_knowledge.py`
- [antikas/ergasterion](https://github.com/antikas/ergasterion): `README.md`, `pyproject.toml`

Standards and products:

- [agentskills/agentskills](https://github.com/agentskills/agentskills): `docs/specification.mdx`, `GOVERNANCE.md`
- [agentsmd/agents.md](https://github.com/agentsmd/agents.md)
- [a2aproject/A2A](https://github.com/a2aproject/A2A): `docs/specification.md`
- [Claude Code: plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [GitHub CLI manual: `gh project item-edit`](https://cli.github.com/manual/gh_project_item-edit) (and the installed `gh` 2.89 help)
- [GitHub changelog, 2025-12-16: Actions pricing update](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/)

Secondary sources (background only, not relied on for claims):

- [i-scoop: Agent Skills and the Agentic AI Foundation](https://www.i-scoop.eu/agent-skills-agentic-ai-foundation/)
- [DEV Community: AI agent standards in 2026](https://dev.to/ialijr/top-ai-agent-standards-to-know-in-2026-31gm)
- [Tyk: A2A architecture and specification](https://tyk.io/blog/a2a-protocol/)
- [Morph: Claude Code plugins and marketplaces](https://www.morphllm.com/claude-code-marketplace)
- [Socket: GitHub Actions pricing whiplash](https://socket.dev/blog/github-actions-pricing-whiplash)
