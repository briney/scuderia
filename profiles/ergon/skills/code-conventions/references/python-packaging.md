# Python packaging

Modern packaging, no legacy forms.

## Rules

- **`pyproject.toml` only.** Never `setup.py`, never `setup.cfg`. Build
  backend: **hatchling**.
- **src layout.** Importable code lives at
  `<repo>/src/<package_name>/`, not at repo root. Tests at `<repo>/tests/`.
  src layout forces tests to run against the *installed* package, which
  catches packaging bugs that flat layouts hide.
- **Version from git tags** via `hatch-vcs`. The version string exists in
  exactly one place — the tag. No `__version__` bumping commits. Release
  process: commit, tag `vX.Y.Z`, push tag, cut a GitHub Release; the publish
  workflow does the rest (see `publishing.md`).
- **uv for everything local and CI.** `uv sync`, `uv run pytest`,
  `uv build`. Do not pip-install in workflows.
- **Dependency declarations** go in `pyproject.toml` `[project.dependencies]`
  (runtime), `[dependency-groups]` (dev — uv-native), and
  `[project.optional-dependencies]` (docs — an *extra*, because Read the Docs
  and other pip consumers cannot read dependency-groups). No
  `requirements*.txt` unless a consumer genuinely cannot read pyproject
  (rare; ask first).
- **Python floor: 3.10.** Match `requires-python` and the CI matrix.

## Skeleton

```
<repo>/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── LICENSE
├── .gitignore
├── .readthedocs.yaml
├── mkdocs.yml
├── src/
│   └── <package_name>/
│       ├── __init__.py
│       └── ...
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   └── index.md
└── .github/
    └── workflows/
        ├── ci.yml
        └── python-publish.yml
```

Template: `templates/pyproject.toml`.
