---
name: ADR-002 Scope: from requirements to working code
description: Kanon refines requirements, creates tickets and calls specialists and tools to produce working output, in every domain
type: decision
status: accepted
date: 2026-11-13
decided-by: owner
tags:
  - type/decision
  - project/kanon
aliases:
  - ADR-002
  - Scope
  - D2
---

# ADR-002: Scope: from requirements to working code

## Context

Revision 1 found that Ergasterion is a deterministic data-pipeline generator with no AI
model inside, not an agent harness, and asked whether it was in scope.

## Decision

Everything is in scope. Kanon takes a person's requirements, refines them into actionable
steps, creates work tickets, and has specialists complete them with whatever tools they
need: proofs of concept, security, automation, data products, software, and more.
The Pantheon therefore holds two kinds of entry: **agents** (specialist roles) and
**tools** (programs agents run). Ergasterion is a tool.

## Evidence

- Owner answer 2.
- Ergasterion `README.md`; source search found no model calls.
- Foundation plan section 4 (stages A to H) and section 6.1.

## Consequences

- The requirement-to-code pipeline in foundation plan section 4 is the engine's main flow.
- Tool entries need their own manifest (install, check, permissions), separate from agents.
