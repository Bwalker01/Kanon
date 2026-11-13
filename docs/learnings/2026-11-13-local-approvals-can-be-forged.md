---
name: Local approvals can be forged by the assistant
description: An approval recorded inside the repository cannot prove a person gave it, because the assistant can write files and can obtain a terminal; real proof needs an identity the assistant does not hold
type: learning
date: 2026-11-13
tags:
  - type/learning
  - project/kanon
  - topic/approval
aliases:
  - Approval forgery
---

# Local approvals can be forged by the assistant

## What happened

Foundation plan section 5.2 proposed protecting approvals with a command, `kanon approve`,
that only accepts input typed at an interactive terminal, plus a Claude Code permission
rule denying the assistant that command. Phase 0 tested the first half before building on it.

## The probe (2026-11-13, in this Claude Code session)

```bash
python3 -c "import sys; print(sys.stdin.isatty())"
# False: the assistant's shell is not a terminal

script -qc "python3 -c 'import sys; print(sys.stdin.isatty())'" /dev/null < /dev/null
# True: the standard `script` command gives the assistant a terminal
```

## What it means

1. **A terminal check does not stop the assistant.** `script` (installed by default on
   most Linux systems) provides one.
2. **A rule that blocks one command does not stop the outcome.** The assistant can write an
   `approval.md` directly. Rules on file writes may narrow this; Phase 1 tests what Claude
   Code's rules can and cannot block. **[Not yet tested]**
3. **Anything done with the owner's own credentials looks like the owner.** This includes
   GitHub actions taken through the owner's `gh` login. GitHub also does not let a pull
   request's author approve it, so pull requests opened under the owner's login cannot be
   approved by the owner.

## The rule that follows

- **Local approvals are tamper-evident, not tamper-proof.** Record a hash of exactly what
  was approved so later changes are caught, and say plainly that the record itself could
  be forged.
- **Tamper-proof approval needs a second identity.** The assistant acts under its own
  identity (for example a GitHub App), and the owner approves under theirs.

Recorded in ADR-004 and ADR-009.
