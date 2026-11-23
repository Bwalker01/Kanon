# Kanon

Kanon (κανών: a rule or standard) is a context engine for AI-assisted projects. It keeps one
authoritative, human-readable record of a project's decisions and work, and coordinates
specialist AI agents through an independent review loop with owner approval.

## Status

Phase 1 (core engine) is in progress. Run `kanon desk` to see what waits on you.

| Start here | Purpose |
|---|---|
| [kanon/docs/roadmap.md](kanon/docs/roadmap.md) | Phases and their scope |
| [kanon/work/](kanon/work/) | Work in progress, one file per piece of work |
| [kanon/decisions/](kanon/decisions/) | Decision records, one page each |

## Capabilities (planned)

- Initialises in any repository with a single `kanon/` folder.
- Refines requirements into plans and tickets, and assigns them to specialist agents.
- Adds agents and tools on demand from the Pantheon marketplace.
- Reviews every output independently and requests approval at defined points.
- Keeps token and CI costs visible and controlled.

## GitHub Mode (Optional)

Kanon can open one pull request per approved plan as its own GitHub App, and agents are refused your GitHub
connector and writing `gh` commands. Cloud sessions' own clone and branch pushes still use your connection.
Set it up once, on your own computer, in a clone of your repository:

1. `kanon github setup` opens GitHub with Kanon's permissions filled in. Create the App, then install it on the repository.
2. `kanon github check` confirms the App signs in and has the right permissions.
3. `kanon github protect`, run with your own `gh` login, makes a code owner's review required on `main`. As administrator you can still merge your own pull requests; the App and agents cannot.

Merging the pull request is the approval. Cloud sessions cannot sign in as the App (their proxy refuses GitHub App
paths), so pull requests are opened from your computer. A repository's own CI runs on the App's pull requests as on
any other.

Pull requests open as drafts (ADR-015). `kanon github ready <work>` marks one ready for review, which starts the
check, and `kanon github draft <work>` returns it to draft; both act as the App, and agents may run them.

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
