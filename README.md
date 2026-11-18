# Kanon

Kanon (κανών: a rule or standard) is a context engine for AI-assisted projects. It keeps one
authoritative, human-readable record of a project's decisions and work, and coordinates
specialist AI agents through an independent review loop with owner approval.

## Status

Phase 0 (foundation) is complete and awaiting approval. No code has been released yet.

| Start here | Purpose |
|---|---|
| [kanon/REVIEW.md](kanon/REVIEW.md) | Items awaiting the owner's decision |
| [kanon/STATUS.md](kanon/STATUS.md) | Phases, progress and recent changes |
| [kanon/decisions/](kanon/decisions/) | Decision records, one page each |

## Capabilities (planned)

- Initialises in any repository with a single `kanon/` folder.
- Refines requirements into plans and tickets, and assigns them to specialist agents.
- Adds agents and tools on demand from the Pantheon marketplace.
- Reviews every output independently and requests approval at defined points.
- Keeps token and CI costs visible and controlled.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). After cloning, run `kanon sync` to generate the agent files.

## Acknowledgements

Builds on MIT-licensed work by Georgios Antikatzidis:
[Koine-OS](https://github.com/antikas/koine-os),
[Pinax](https://github.com/antikas/pinax-tracker),
[AutoBuild](https://github.com/antikas/autobuild-factory) and
[Ergasterion](https://github.com/antikas/ergasterion). Uses the
[Agent Skills](https://github.com/agentskills/agentskills) and
[AGENTS.md](https://github.com/agentsmd/agents.md) formats.

## Licence

MIT. See [LICENSE](LICENSE).
