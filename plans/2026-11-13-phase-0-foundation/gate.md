---
name: Phase 0 gate
description: What the owner is asked to approve at the end of Phase 0, in plain language
type: gate
status: awaiting-owner
date: 2026-11-13
tags:
  - type/gate
  - project/kanon
  - stage/phase-0
aliases:
  - Phase 0 gate
---

# Phase 0 gate: your decision

## What you are asked

Approve, or request changes to, five things:

1. **Ten decision records** ([docs/decisions/](../../docs/decisions/INDEX.md)). ADR-001 to
   ADR-009 record your answers D1 to D9. ADR-010 records "follow the Koine Loop" from your
   original brief.
2. **Two amendments** found by testing in Phase 0, both explained in
   [the first learning](../../docs/learnings/2026-11-13-local-approvals-can-be-forged.md):
   - **ADR-004:** approvals kept inside the repository are *tamper-evident, not
     tamper-proof*. The assistant can obtain a terminal and write files, so it could forge
     one. Kanon will make any change after approval detectable, and will say plainly that it
     cannot prove more than that locally.
   - **ADR-009:** in GitHub mode Kanon must act through **its own GitHub identity** (a
     GitHub App, or a bot account). GitHub does not let a pull request's author approve
     it, so if Kanon opened pull requests as you, you could not approve them. This replaces
     that point in the foundation plan, section 7.3.
3. **The repository layout** (this repository is now Kanon's first instance):
   [README.md](../../README.md), [AGENTS.md](../../AGENTS.md), `CLAUDE.md`,
   [LICENSE](../../LICENSE) (MIT), [docs/INDEX.md](../../docs/INDEX.md),
   [the dashboard](../../docs/status/dashboard.md), [today's log](../../docs/daily/2026-11-13.md),
   and [your brief, saved verbatim](../../docs/sources/2026-11-13-owner-brief.md).
4. **The Phase 1 plan** ([plan.md](../2026-11-13-phase-1-context-loop-gates/plan.md)):
   eight items, from the package skeleton to two requirements run end to end in this
   repository. Now updated with your answers and with the conduct standard built in
   (P1-02, P1-03, P1-04, P1-06, P1-08).
5. **Agent conduct and writing** (added 2026-11-14 at your request):
   [the standard](../../docs/standards/conduct-and-writing.md),
   [ADR-011](../../docs/decisions/ADR-011-agent-conduct-and-writing.md), and the rewritten
   [AGENTS.md](../../AGENTS.md), which this session already follows. The questions asked
   along the way are in [questions.md](../2026-11-14-agent-conduct/questions.md).

## What was not done, and why

- **No independent review.** Kanon's reviewer is built in Phase 1, and this session does not
  start subagents unless you ask. Everything here was produced and checked by the same
  assistant, which the method treats as no review at all. If you want an independent
  review before deciding, say so and a separate reviewer subagent will review these files
  against the foundation plan.
- **No tool installation.** Pinax, Kanon's settings file and the Claude Code files come in
  Phases 1 and 2.
- **The repository is still named `Mercatus`.** Only you can rename it.
- **The approval record for the foundation plan** was written by the assistant from your
  "begin phase 0" message. Approving this gate confirms it.

## Inputs for Phase 1

Already answered (see the Phase 1 plan's [questions.md](../2026-11-13-phase-1-context-loop-gates/questions.md)):
reviewer subagents allowed, both `kanon status` and `kanon questions` as end-to-end runs,
3 review rounds, and the repository rename. The three small ones I did not ask about use
their defaults: approver `owner@<your machine name>`, licence holder `Bwalker01`, and `uv`
for packaging. Say if any should differ.

**Your action:** rename the repository to `kanon` (GitHub, Settings, General, Repository
name). Tell me when it's done and I'll update the references.

## Your answer

- **Approve:** Phase 1 starts with P1-01.
- **Request changes:** say what to change; the changes come back to this gate.
