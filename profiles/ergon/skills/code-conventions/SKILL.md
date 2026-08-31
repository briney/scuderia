---
name: code-conventions
description: Use when scaffolding a new repository, setting up CI/publishing/docs, choosing tooling, or reviewing whether a repo matches house style. States your human's opinionated defaults for Python codebases and points at the executable templates that encode them.
triggers:
  - "new repo"
  - "scaffold"
  - "project structure"
  - "repo layout"
  - "ci setup"
  - "github workflow"
  - "pypi publish"
  - "readthedocs"
  - "code conventions"
  - "house style"
---

# Code Conventions

Your human's opinionated defaults for how a codebase is built, tested, and
published. Virtually all code is **Python**; these conventions are
Python-first. Load the reference for the topic at hand; use the templates
rather than re-deriving config from prose.

## Precedence

1. A repo's own `AGENTS.md` / `CLAUDE.md` / existing config wins. Conventions
   fill gaps; they do not override a project that has already decided.
2. These conventions apply to new repos and to repos that have not decided.
3. Your human's explicit instruction for the task at hand wins over both.

## Projecting conventions to delegates

Coding-CLI delegates (Claude Code, Codex) and Hermes subagents never see this
skill — they read the repo. Therefore:

- **New repos:** scaffold `AGENTS.md` from `templates/AGENTS.md` at creation
  time. Every harness reads it natively; the conventions travel with the repo.
- **Existing repos with their own AGENTS.md:** leave it alone. If a delegate
  run needs a convention the repo lacks, pass the specific reference file via
  `claude -p ... --append-system-prompt-file <path>` (or the Codex
  equivalent) for that run only.

## References

| Topic | File |
|---|---|
| Packaging: pyproject.toml, src layout, hatchling, hatch-vcs, uv | `references/python-packaging.md` |
| Toolchain: ruff, ty, pytest, coverage, docstring format | `references/toolchain.md` |
| Testing philosophy and layout — read this one for ANY test work | `references/testing.md` |
| CI workflow shape (lint / typecheck / test matrix / integration) | `references/ci.md` |
| PyPI publishing: tag-driven versions, trusted publishing | `references/publishing.md` |
| Docs: mkdocs + mkdocstrings, Google docstrings, Read the Docs | `references/docs.md` |

## Templates

Executable forms of the conventions. Copy-and-substitute, never author from
scratch; placeholders are marked `<angle-bracketed>`.

| Template | Target path in repo |
|---|---|
| `templates/pyproject.toml` | `pyproject.toml` |
| `templates/ci.yml` | `.github/workflows/ci.yml` |
| `templates/python-publish.yml` | `.github/workflows/python-publish.yml` |
| `templates/mkdocs.yml` | `mkdocs.yml` |
| `templates/readthedocs.yaml` | `.readthedocs.yaml` |
| `templates/AGENTS.md` | `AGENTS.md` |

## Maintenance

These conventions crystallize from user-corrected runs. When your human
corrects a scaffolding or tooling choice, patch the relevant reference or
template here — the correction is not complete until the skill carries it.
