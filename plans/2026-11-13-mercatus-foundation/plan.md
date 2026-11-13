---
name: Mercatus foundation plan
description: Research findings on Koine-OS, Pinax, AutoBuild and Ergasterion, and a phased plan for building Mercatus, an importable context engine with a marketplace of specialist agents run through the Koine Loop
type: plan
status: draft-awaiting-owner-approval
date: 2026-11-13
tags:
  - type/plan
  - project/mercatus
  - stage/foundation
aliases:
  - Mercatus plan
  - Foundation plan
---

# Mercatus: research findings and foundation plan

> **Status:** draft for the owner's review. Nothing here is built yet. Section 9 lists the
> questions that need your answers before Phase 1 starts.
>
> **How to read this:** each claim about an existing project is marked **[Evidence]** with
> the file it comes from. Each design choice is marked **[Proposal]** with the evidence
> that supports it. Anything I could not confirm is marked **[Unverified]** or listed as an
> open question. I have not filled gaps with guesses.

---

## 1. Summary

Mercatus can be built, and most of the hard parts already exist as working, MIT-licensed
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

**Mercatus's job is the missing column:** an installable engine that sets up the context
layer in any repository, enforces the Koine Loop with a recorded human approval at the
end, keeps human-readable documentation current, and onboards specialist agents from a
catalogue as the project needs them.

Two findings change the brief and need your decision (section 9):

1. **Ergasterion is not an agent harness.** It is a deterministic generator that turns
   YAML declarations into dbt data pipelines. It contains no AI model. It fits Mercatus
   as a *tool* a data-engineering specialist uses, not as an agent.
2. **I could not find "Agora".** It is not a public repository under `Bwalker01` or
   `antikas`. I have not assumed anything about its contents.

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
> authorisation. Mercatus would make *both* mandatory for every output. That is
> compatible with Koine, but it is a choice we are making, not something Koine already
> says. (Question Q4.)

**What Koine admits it cannot enforce.** [Evidence: `adapters/claude-code/README.md`]
"Skills cannot enforce specifications at the runtime level", "No mechanical enforcement
of the Koine Loop convergence limit", and if a generator runs without its reviewer
"nothing in Claude Code will catch it." The adapter also reports skill auto-invocation at
"approximately 70 percent reliability" (the author's figure; I have not measured it), and
so requires reviewers to be named explicitly in plan files.

This is the strongest argument for Mercatus being an **engine** rather than another pack:
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
  elsewhere. **Mercatus is that elsewhere.**

**Role in Mercatus:** the work ledger. Every task an agent or person does is a Pinax item.
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
  command is **not in any public repository** I could find. Mercatus can implement this
  port itself.

**Role in Mercatus:** the software-build specialist. It already implements builder plus
blind reviewer, which is the Koine Loop for code.

### 2.4 Ergasterion (`antikas/ergasterion`, MIT, v0.6.1, Python 3.11+)

[Evidence: `README.md`, source search]

- "The data product factory: declare the source, emit the pipeline." People write YAML
  declarations; the engine generates a dbt project, Open Data Contract Standard contracts,
  a lineage graph and runtime manifests. "The same inputs create the same files byte for
  byte." DuckDB runs it locally; BigQuery is generated and checked but not run.
- I searched the code for AI or model use. The only hits are two docstrings referring to
  conventions "read by a translation agent". **No model calls exist in the engine.**

**Role in Mercatus:** not an agent. A data-engineering specialist agent would *use*
Ergasterion: draft declarations, run `emit-products --check`, and have the reviewer check
the output. (Question Q2.)

### 2.5 Things I found that limit what I can claim

- **Owner instructions are private.** All three of koine-os, pinax-tracker and ergasterion
  have a commit on 2026-09-01: "REMOVED: keep owner agent instructions private". The
  author's own `AGENTS.md` and `CLAUDE.md` are not public. I have not guessed at them.
- **Public repos are projections of private ones.** Pinax and AutoBuild release commits read
  "projected from private commit ...". The public code can change in larger jumps than its
  history shows. All four are pre-1.0. **Mercatus must pin versions.**
- **Agora:** not found (see section 1).

### 2.6 Open standards worth building on

Checked against the standards' own repositories on 2026-11-13. The public websites
(`agentskills.io`, `agents.md`) were blocked by this session's network, so I read their
GitHub sources instead.

| Standard | What it gives Mercatus | Evidence |
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

## 3. What Mercatus is

**[Proposal]** A Python package and a folder convention.

- **Installed once:** `pipx install mercatus`. Python matches Pinax (3.10+) and AutoBuild
  (3.11+), so we target 3.11+ and can import both directly.
- **Started in any repo:** `mercatus init` writes a minimal context layer, the
  instructions any coding agent reads, and a Pinax tracker. This copies Pinax's own
  `pinax init` pattern.
- **Works with whatever model is connected,** in two modes (the same split AutoBuild uses
  between `autobuild-coordinated` and the Python `autobuild` command):
  - **In-session mode (default, no API keys):** the person's own coding assistant (Claude
    Code, Copilot, Codex, or anything that reads AGENTS.md) runs the Mercatus Loop through
    installed skills. The `mercatus` command does the checking and record-keeping.
  - **Engine mode (later):** `mercatus run` drives harnesses headlessly through adapters,
    for unattended work.
- **Enforces, not just suggests.** `mercatus verify` (modelled on `pinax verify`) fails if
  any promoted output lacks its plan, its independent review, or its human approval
  record. It runs as a pre-commit hook and in CI. This closes the gap Koine's own adapter
  documents.

### 3.1 What `mercatus init` creates (the blank slate)

```text
AGENTS.md                      root context: what the project is, where to look, the loop rules
CLAUDE.md                      one line pointing to AGENTS.md (Claude Code reads CLAUDE.md)
mercatus.toml                  instance settings: model adapters, reviewer rules, approvers
docs/
  INDEX.md                     map of all documentation, one line per entry
  status/dashboard.md          current state; read first every session
  daily/YYYY-MM-DD.md          append-only activity log
  features/  builds/  fixes/  ideas/  decisions/   one folder per document type you named
  learnings/                   lessons that apply across the project
  sources/                     raw input (interviews, notes, links) before it is compiled
  archive/                     superseded documents, with a header saying why
plans/YYYY-MM-DD-topic/        the loop's audit trail (plan, drafts, reviews, approval, final)
.mercatus/roster/              the agents currently on the team, one file each
.ergon/                        Pinax tracker (created by pinax init)
```

Every document carries Koine's required frontmatter. Each folder starts empty except for a
short `INDEX.md` and a template. Following Koine's minimum viable OS, only four roles are
on the roster at the start (section 5.3).

---

## 4. The Mercatus Loop

**[Proposal]** The Koine Loop, with the reviewer and the human approval both required and
both recorded. Each step names its precedent.

```text
 request ─▶ 1 SPECIFY ─▶ 2 PLAN ─▶ [human approves plan] ─▶ 3 REGISTER
                                                              │
   ┌──────────────────────────────────────────────────────────┘
   ▼
 4 CREATE (specialist) ─▶ 5 REVIEW (independent) ─▶ pass? ──no──▶ 6 ADJUST ─▶ back to 5
                                                     │                (max rounds, then
                                                    yes                escalate to human)
                                                     ▼
                         7 DOCUMENT (scribe + its reviewer)
                                                     ▼
                         8 APPROVE (human, explicit, recorded)
                                                     ▼
                         9 PROMOTE, LOG, LEARN
```

| Step | What happens | Written to | Precedent |
|---|---|---|---|
| 1 Specify | The request is turned into a specification: inputs, transformation, output shape, review checks. If the request is vague, the coordinator asks the person; it does not guess. | `docs/sources/` then `plans/.../plan.md` | Koine "specifications, not intent"; Koine "It will not guess" |
| 2 Plan | The coordinator names the specialist, the reviewer(s), the inputs and the output path. **The person approves the plan** before work begins. | `plans/.../plan.md` | Koine step 1 and stop points; `autobuild-plan` stops before launch |
| 3 Register | The plan becomes Pinax items with dependencies. | `.ergon/` | Pinax |
| 4 Create | The named specialist produces a draft in isolation (code in its own worktree). | `draft-vN.md` or a worktree branch | Koine step 2; AutoBuild builder |
| 5 Review | A **fresh** reviewer with a different prompt, read-only tools and **no access to the creator's transcript** checks the draft against the spec. Verdict: `pass`, `correct`, `escalate`, `park`, with each finding marked blocking or not. | `review-<reviewer>-vN.md` | Koine step 3; AutoBuild blind reviewer and verdict rules |
| 6 Adjust | The creator revises into a new file. Limit: 3 rounds (default, configurable), then the item goes to the person with the open findings. | `draft-vN+1.md` | Koine convergence rule (3 to 4); AutoBuild default of 2 corrections |
| 7 Document | The scribe writes or updates the human-facing documentation the change affects, and a documentation reviewer checks it. | `docs/...` | Your brief (documentation at the heart); Koine disciplines |
| 8 Approve | The person sees one summary: what changed, the reviewer's verdict and findings, the documentation diff. They approve, reject, or send back. The decision, who made it, and the commit it applies to are recorded. Until then the Pinax item sits behind a `decision` gate. | `approval.md`; Pinax event | Your brief; Pinax `decision` gate |
| 9 Promote, log, learn | Output moves to its permanent home; `plans/` keeps the history. Daily log and dashboard are updated. Recurring findings become `learnings/`. | `docs/daily/`, `docs/status/`, `docs/learnings/` | Koine step 5, disciplines 5, 7, 8; Koine Stage 5 |

**What `mercatus verify` checks** (mechanical, not advisory):

- Every `final.md` or promoted output has a `plan.md` committed before its first draft.
- Every draft has at least one review file from a reviewer that is not its creator.
- Every promoted output has an `approval.md` naming a human approver listed in
  `mercatus.toml`.
- Loops over the round limit were escalated, not silently continued.
- Every document has the required frontmatter and is listed in an `INDEX.md`.

---

## 5. The marketplace

### 5.1 What an agent package is

**[Proposal]** An Agent Skills folder (so any skills-aware assistant can load it) plus a
small Mercatus manifest. Using the standard's optional `metadata` field, or a sidecar file
if that becomes too limiting:

```yaml
# agents/data-engineer/mercatus-agent.yml
id: data-engineer
version: 0.1.0
archetype: daedalus               # optional Koine vocabulary
summary: Designs and changes governed data pipelines.
generators: [draft-data-product]   # each must name a reviewer below
reviewers:  [review-data-product]  # Koine Convention 1: no generator without a reviewer
inputs:  [docs/features/*.md, declarations/**/*.yml]
outputs: [declarations/**/*.yml, docs/builds/*.md]
tools:   [ergasterion]             # programs it may run
mcp:     []                        # MCP servers it needs
harnesses: [claude-code, codex, copilot]
trust: reviewed                    # core | reviewed | community
licence: MIT
```

Rules the engine enforces at onboarding: every generator has a paired reviewer; inputs and
outputs are declared (Koine's specification test); tool permissions are listed (the Agent
Skills `allowed-tools` field is marked experimental in the spec, so Mercatus checks its own
list rather than relying on it).

### 5.2 Onboarding a specialist ("hiring an expert")

The onboarding runs through the Mercatus Loop like any other output:

1. **Need found.** A Pinax item has no roster agent whose outputs cover it, or the person
   asks for a capability.
2. **Candidate proposed.** The coordinator searches the configured catalogues and writes a
   plan: which package, why, what it can touch.
3. **Reviewed.** The reviewer checks the package: manifest complete, reviewer paired,
   permissions proportionate, licence compatible, scripts read.
4. **Approved by a person.** Nobody joins the team without an explicit approval.
5. **Introduced.** A roster file is written, plus a short human-readable "who joined, what
   they do, what they may touch" note in the daily log and dashboard.
6. **Leaving** is archive-not-delete: the roster file moves to `docs/archive/` with the
   reason.

A **catalogue** is a Git repository with an index of agent packages. Mercatus ships one
official catalogue; teams can add their own (private) ones in `mercatus.toml`.

### 5.3 Starting roster and first specialists

**Core (always present after `init`), four roles** per Koine's "three to five":

| Role | Koine archetype | Job |
|---|---|---|
| Coordinator | Metis | Turns requests into specs and plans; picks specialists; proposes onboarding |
| Reviewer | Kritos | Independent review; never produces |
| Scribe | Clio and Paideia | Keeps documentation, daily log, dashboard and INDEX files current |
| Context keeper | Mnemon | Loads the right context for each session; compiles `sources/`; flags stale docs |

**First catalogue entries, built on Antikas's projects:**

| Entry | Built on | Type |
|---|---|---|
| Tracker integration | Pinax | Built into the engine, not a hireable agent |
| Software builder | AutoBuild (its builder and blind reviewer seats) | Specialist |
| Data-product engineer | Ergasterion as its tool | Specialist (pending Q2) |

---

## 6. Model and harness independence

**[Proposal]** Copy AutoBuild's ports-and-adapters shape (evidence: `docs/architecture.md`,
dependency direction enforced by `tests/architecture/`):

- A `HarnessPort` with adapters for Claude Code, Codex, GitHub Copilot, and direct API
  access. Each adapter is tested against a shared contract.
- In-session mode needs no adapter beyond the instruction files: AGENTS.md for any agent
  that reads it, CLAUDE.md and `.claude/skills/` for Claude Code, and
  `.github/copilot-instructions.md` plus prompt files for Copilot (all three have
  precedents in Koine's adapters).
- The reviewer can be set to run on a different model from the creator. This is an
  option, not a default; I have no evidence on whether it improves results for this kind
  of work, so we should measure it before recommending it.

---

## 7. Roadmap

Each phase ends with something you can watch work, and is itself run through the loop.

| Phase | Delivers | Done when |
|---|---|---|
| **0. Foundation** | This plan approved; first decision records (licence, language, how Antikas's projects are included); Mercatus's own repo uses its own docs layout | You have approved the plan and the Phase 1 slice |
| **1. Context layer and loop** | `mercatus init`; templates for features, builds, fixes, ideas, decisions; AGENTS.md and Claude Code and Copilot instructions; the loop as skills; `mercatus verify` with a pre-commit hook | In an empty test repo, one feature document goes plan → draft → independent review → correction → human approval → promoted, with every file committed, and `mercatus verify` fails if any one step is removed |
| **2. Tracker and roster** | Pinax built in; roster files; the four core roles; onboarding flow; the official catalogue repo with its first entry | A person asks for something no core role covers; Mercatus proposes a specialist, it is reviewed, approved, and appears in the roster and the docs |
| **3. Engine mode and builder** | `HarnessPort` with Claude Code first; AutoBuild as the software-builder specialist | A small feature goes from request to merged code with a blind review and a human approval, through two different harnesses |
| **4. Marketplace** | Trust levels, version pinning, third-party catalogues; data-product engineer on Ergasterion (if Q2 says yes) | A second team's catalogue can be added and one of its agents onboarded |
| **5. Feedback and scale** | Metrics (loop rounds, approval rates, agent use) feeding `learnings/`; A2A for agents on other servers if needed | A four-weekly review (Koine Stage 5) produces at least one change to the core |

---

## 8. Risks

| Risk | Evidence | Mitigation |
|---|---|---|
| Upstream changes break Mercatus | All four projects are pre-1.0 and released from private repos | Pin versions; use them only behind Mercatus ports; contract tests per adapter |
| Third-party agents run harmful scripts | Agent Skills folders can include `scripts/`; `allowed-tools` is experimental | Every onboarding is reviewed and approved by a person; permissions declared and checked; trust levels |
| Reviewers that always pass | Koine anti-pattern "reviewers that cannot fail" | `verify` tracks pass rates; a reviewer with no failures over N items is flagged for the person |
| Documentation overload | Koine: "It will not produce thirty skills on day one" | Blank slate with four roles; folders created empty; specialists added only on need |
| Skills not triggering | Koine reports about 70% auto-invocation in Claude Code (author's figure) | Plans name every agent explicitly; `verify` checks that named reviewers ran |
| Cost of review rounds | AutoBuild added usage meters and lane cooling, which shows this is a real cost | Round limit; review effort configurable per agent; usage reporting in Phase 3 |
| Human approval becomes a bottleneck | Inferred, not evidenced | One-screen approval summaries; batch approvals; open question Q4 on what may skip approval |

---

## 9. Questions for you

These need your answer before Phase 1. Each one changes what gets built.

- **Q1. Agora.** Is there a document or repo for the original "Agora" idea? I could not
  find one. If it has requirements Mercatus must keep, I need to read it.
- **Q2. Ergasterion.** It is a data-pipeline generator with no AI inside. Do you want
  data products in scope for Mercatus (as a specialist using Ergasterion), or did you mean
  a different project?
- **Q3. Relationship with Antikas's projects.** Options: (a) install Pinax and AutoBuild
  from PyPI as pinned dependencies and copy Koine-OS in (its own recommended model);
  (b) fork all of them into Mercatus; (c) work with the author upstream. I recommend (a):
  all are MIT-licensed, and it keeps credit and upstream fixes. Have you been in touch with
  the author?
- **Q4. Approval scope.** Must a person approve **every** output, including small
  documentation updates and log entries, or only certain kinds (code merges, new agents,
  decisions)? Koine requires approval at stage boundaries; your brief says all output.
- **Q5. First harness.** Which assistant will you use first: Claude Code, Copilot,
  Codex, or something else? Phase 1 starts with that one.
- **Q6. Language and licence.** I propose Python 3.11+ (matches Pinax and AutoBuild) and
  MIT (matches all four upstream projects). Agree?
- **Q7. Who is the first real user?** A real project to test Mercatus on in Phase 1 will
  find problems no test repo will.

---

## 10. Sources

Upstream repositories (cloned 2026-11-13):

- [antikas/koine-os](https://github.com/antikas/koine-os): `README.md`,
  `method/the-koine-loop.md`, `method/00-overview.md`, `method/knowledge-discipline.md`,
  `method/agent-archetypes.md`, `adapters/claude-code/README.md`
- [antikas/pinax-tracker](https://github.com/antikas/pinax-tracker): `README.md`,
  `DESIGN.md`, `docs/decisions/ADR-004-separation-enforcement.md`
- [antikas/autobuild-factory](https://github.com/antikas/autobuild-factory): `README.md`,
  `docs/architecture.md`, `skills/autobuild-plan/SKILL.md`,
  `skills/autobuild-coordinated/agents/autobuild-reviewer.agent.md`,
  `src/autobuild/adapters/koine_knowledge.py`
- [antikas/ergasterion](https://github.com/antikas/ergasterion): `README.md`

Standards (read from their GitHub sources):

- [agentskills/agentskills](https://github.com/agentskills/agentskills): `docs/specification.mdx`, `GOVERNANCE.md`
- [agentsmd/agents.md](https://github.com/agentsmd/agents.md)
- [a2aproject/A2A](https://github.com/a2aproject/A2A): `docs/specification.md`

Secondary sources (used only for context, not for claims above):

- [i-scoop: Agent Skills and the Agentic AI Foundation](https://www.i-scoop.eu/agent-skills-agentic-ai-foundation/)
- [DEV Community: AI agent standards in 2026](https://dev.to/ialijr/top-ai-agent-standards-to-know-in-2026-31gm)
- [Tyk: A2A architecture and specification](https://tyk.io/blog/a2a-protocol/)
