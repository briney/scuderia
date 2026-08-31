# CI

One workflow: `.github/workflows/ci.yml` (template: `templates/ci.yml`).
Runs on **every push** and on pull requests. Four jobs:

| Job | What it runs | Why it is separate |
|---|---|---|
| `lint` | `ruff check` + `ruff format --check` | Fails in seconds; style problems should not wait for a test matrix |
| `typecheck` | `ty check` | Same — fast, independent signal |
| `test` | `pytest tests/unit --cov` | Matrix: Python 3.10–3.13 on `ubuntu-latest` |
| `integration` | `pytest tests/integration -m integration` | Long, may need secrets; one Python version (current stable) |

## Rules

- **uv in CI.** `astral-sh/setup-uv`, then `uv sync` / `uv run`. No pip, no
  manual caching — setup-uv handles it.
- **Coverage is an artifact, not a gate.** Upload the report; never
  `fail-under`.
- **Matrix discipline.** ubuntu-only unless the package has
  platform-specific code; add `macos-latest`/`windows-latest` per-package,
  not by default. Keep the matrix honest: every entry must correspond to a
  platform your human actually supports.
- **Secrets-dependent integration tests** get repo secrets and skip cleanly
  when unavailable (fork PRs) — the job must be green-or-skipped, never
  red-for-external-contributors.
- **No third-party actions beyond the essentials** (`actions/checkout`,
  `astral-sh/setup-uv`, `actions/upload-artifact`, `pypa/gh-action-pypi-publish`
  in publish). Pin by major version tag.
