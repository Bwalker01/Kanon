# Kanon

**Kanon** (κανών: a measuring rod; a rule or standard; the root of "canon") is an engine
that keeps one shared, human-readable layer of context across a whole project, so that
people and specialist AI agents can work on it together without losing track of what was
decided, built, fixed or planned.

It is designed to:

- **start as a blank slate** in any repository and grow with the project;
- **turn requirements into work:** refine what you ask for, plan it, ticket it, and have
  specialists carry it out with the tools they need;
- **bring in specialists as needed** from the **Pantheon**, a central marketplace of agents
  and tools, the way a team onboards a new expert;
- **review everything independently** and **ask you to approve** at the points that matter
  (the Koine Loop, from [Koine-OS](https://github.com/antikas/koine-os));
- **keep documentation at the centre,** written for people as well as agents;
- **spend tokens and CI minutes carefully.**

## Status

**Phase 0 (foundation).** There is no code yet. This repository is laid out the way Kanon
will lay out any project, and is Kanon's own first instance.

- The plan: [plans/2026-11-13-kanon-foundation/plan.md](plans/2026-11-13-kanon-foundation/plan.md)
- Decisions: [docs/decisions/INDEX.md](docs/decisions/INDEX.md)
- Current state: [docs/status/dashboard.md](docs/status/dashboard.md)
- All documentation: [docs/INDEX.md](docs/INDEX.md)

## Built on

Kanon builds on MIT-licensed work by Georgios Antikatzidis:
[Koine-OS](https://github.com/antikas/koine-os) (the method),
[Pinax](https://github.com/antikas/pinax-tracker) (Git-native work tracking),
[AutoBuild](https://github.com/antikas/autobuild-factory) (harness-neutral build campaigns)
and [Ergasterion](https://github.com/antikas/ergasterion) (data-product generation).
Kanon also uses the open [Agent Skills](https://github.com/agentskills/agentskills) and
[AGENTS.md](https://github.com/agentsmd/agents.md) formats.

## Licence

MIT. See [LICENSE](LICENSE).
