---
name: ADR-011 Agent conduct and writing
description: Kanon agents ask early, push back, stay realistic, match each person's technical level and write without AI-writing patterns, under a single standard with checks
type: decision
status: accepted (awaiting owner approval at the Phase 0 gate)
date: 2026-11-14
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-011
  - Agent conduct
  - Writing standard
---

# ADR-011: Agent conduct and writing

## Context

The owner asked that agents ask questions as they go instead of collecting them at the
gate, push back on bad ideas, stay realistic, talk like a helpful peer, write without
AI-isms, and pitch their language at each person's technical level without patronising
them ([request](../sources/2026-11-14-owner-conduct-request.md)). Phase 0 itself showed the
problem: seven owner inputs were held back and listed at the end of the Phase 1 plan.

## Decision

Every Kanon agent follows [the conduct and writing standard](../standards/conduct-and-writing.md).

- **Asking:** ask when information is missing, before building on a guess; group questions
  that arise together; log every question and answer in the plan folder's `questions.md`.
  A question first raised in a gate that could have been asked earlier is a reviewer
  finding.
- **Pushing back and realism:** say plainly when a request is flawed or costly, with
  evidence and an alternative; the person decides; separate what is tested from what is
  expected.
- **Technical level:** each person has a profile, set by a question at setup; agents
  suggest changes when conversation shows a mismatch, and the person confirms (owner
  answer: both). Four levels with guidance on how to pitch each.
- **Writing:** strict for documents, guidance in chat (owner answer). A free mechanical
  check fails em and en dashes and a list of phrases; the reviewer fails a list of
  patterns that need judgement.

## Evidence

- Owner request and answers ([questions](../../plans/2026-11-14-agent-conduct/questions.md)).
- Koine-OS `prompts/reviewers/writing-quality-reviewer.md`: AI-writing fingerprints
  (including the dash ban), practitioner voice, earned claims. Credited in the standard.
- AutoBuild's `autobuild-plan` requires one block of owner inputs answered once; Kanon
  departs from that on purpose, because the owner asked for questions as they arise.

## Consequences

- `AGENTS.md` in this repository follows the standard now.
- Phase 1 builds it into the engine: profile in `kanon.toml`, the setup question in
  `kanon init`, the mechanical check in `kanon verify`, conduct in every role prompt, and
  a writing review by the reviewer.
- The check is a floor, not a guarantee. New patterns the owner spots become learnings and
  join the lists.
