# Publishing

`.github/workflows/python-publish.yml` (template:
`templates/python-publish.yml`) publishes to PyPI on every GitHub Release.

## The release process

1. All changes merged; CI green on main.
2. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z` (hatch-vcs reads the
   version from the tag — no version-bump commit).
3. Create the GitHub Release from the tag.
4. The workflow builds (`uv build`) and publishes. Done.

## Trusted publishing (OIDC) — the only accepted mechanism

No stored PyPI API tokens. The workflow uses
`pypa/gh-action-pypi-publish` with `id-token: write`; PyPI verifies the
workflow's identity directly.

One-time setup per package (your human does this on pypi.org; it cannot be
automated from the repo):

1. PyPI → project → Publishing → Add a new pending publisher.
2. Owner: `<github-org-or-user>`, repo: `<repo>`,
   workflow: `python-publish.yml`, environment: leave blank.
3. First release after that publishes without any secret in the repo.

When commissioning a first publish, surface this setup step explicitly — the
workflow will fail with an OIDC error until it is done.

## Rules

- Trigger on `release: [published]`, not on tag push — the Release is the
  human-reviewed gate.
- `fetch-depth: 0` on checkout; hatch-vcs needs full tag history.
- TestPyPI is optional per-repo. If used, it is a separate job in the same
  workflow with its own trusted publisher, not a second workflow.
