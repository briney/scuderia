# <package-name>

<one-paragraph description of what the package does>

## Stack & layout

- Python ≥3.10, src layout: importable code in `src/<package_name>/`, tests in `tests/`.
- Packaging: `pyproject.toml` (hatchling + hatch-vcs — version comes from git tags, never edit a version string).
- Toolchain: **uv** (env/install/build), **ruff** (lint + black-style format), **ty** (type-check), **pytest**.

## Commands

```bash
uv sync --group dev          # set up the environment
uv run pytest tests/unit     # fast unit tests
uv run pytest tests/integration -m integration   # end-to-end tests
uv run ruff check .          # lint
uv run ruff format .         # format (black style)
uv run ty check              # type-check
uv build                     # build the package
```

## Testing — read before writing tests

- **Integration tests are the substance.** A feature is not done until a test in `tests/integration/` exercises it the way a user would — real model calls, real I/O, real subprocesses. Mocks belong in unit tests.
- Unit tests (`tests/unit/`) cover pure logic; they are the fast layer.
- No assertion-free tests. Name tests for the behavior they pin.
- Tests needing secrets read them from env vars and skip with a clear reason when unset. Never embed credentials.

## Conventions

- Docstrings: **Google format** on all public modules/classes/functions — they are the docs source (mkdocstrings → Read the Docs).
- Type hints on all public function signatures.
- Formatting is `ruff format`; CI checks with `--check`. Do not hand-format.
- Coverage is reported, never gated — no `fail-under`.

## Release process

1. Merge everything; CI green on main.
2. `git tag vX.Y.Z && git push origin vX.Y.Z`
3. Create the GitHub Release — the publish workflow pushes to PyPI (trusted publishing/OIDC).
