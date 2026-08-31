# Toolchain

The Astral stack, plus pytest. One vendor for lint/format/type keeps the
config surface small.

| Job | Tool | Invocation |
|---|---|---|
| Lint | **ruff** | `uv run ruff check .` |
| Format | **ruff format** (black-compatible) | `uv run ruff format .` |
| Type-check | **ty** | `uv run ty check` |
| Test | **pytest** | `uv run pytest` |
| Coverage | **pytest-cov** — report only, never a gate | `uv run pytest --cov` |
| Env/install/build | **uv** | `uv sync` / `uv run` / `uv build` |

## Rules

- **Formatting is black style, applied by `ruff format`.** Check mode in CI
  (`--check`); never hand-format.
- **ruff lint rules**: start from the template set (`E, F, I, UP, B`). Do not
  enable every rule family that exists — a lint config that cries wolf gets
  silenced with `# noqa`, which is worse than a short rule list that is
  obeyed.
- **ty is the type-checker.** It is young; when ty and reality disagree,
  prefer a targeted `ty: ignore` comment with a reason over weakening the
  global config. Type hints on all public function signatures.
- **Coverage is reported, not gated.** No `fail-under`. Hard thresholds
  incentivize assertion-free tests written to hit a number, which is the
  opposite of the testing philosophy (see `testing.md`).
- **Docstrings: Google format**, on all public modules, classes, and
  functions. They are the docs source — mkdocstrings renders them (see
  `docs.md`), so a docstring is not finished when the summary line is
  written; Args/Returns/Raises sections are required where applicable.
