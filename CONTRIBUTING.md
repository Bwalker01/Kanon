# Contributing to Kanon

This repository builds Kanon and is also its first instance, so it is developed with its own
method. Agent instructions are generated, not committed.

## After Cloning

```bash
uv sync
```

```bash
uv run kanon sync
```

`kanon sync` regenerates the agent files listed in the Kanon block of `.gitignore`, using the
committed standard in `kanon/` and your personal profile. Set up your profile once, outside the
repository:

```bash
uv run kanon profile --github <your-github-username> --level developer
```

## Working

- Read `kanon/STATUS.md` and `kanon/REVIEW.md` first.
- Run the tests with `uv run pytest -q` and the checks with `uv run kanon verify` before committing.
- `kanon/sources.md` holds the owner's words verbatim; work from the decision records.
- Commit messages start with ADDED, MODIFIED or REMOVED and give a one-line reason.
