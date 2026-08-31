# Testing

The load-bearing convention. Read this before any test work.

## Philosophy

Your human's emphasis is **end-to-end integration tests that accurately
exercise real-world use of the tool or model** — not unit tests, and never
coverage-driven theater.

- An integration test runs the real path: real model calls, real file I/O,
  real subprocesses, real (or faithfully recorded) network where the tool has
  network behavior. Mocks are for isolating *unit* tests, not for making an
  "integration" test cheap.
- **A feature is not done until an integration test exercises it the way a
  user would.** Unit tests alone do not close a task.
- Unit tests still earn their keep for pure logic — parsers, transforms,
  math, edge-case branching. They are the fast layer, not the substance.
- **No assertion-free tests.** A test that calls the code and asserts nothing
  (or only "does not raise") is coverage padding and will be rejected in
  review.
- Tests are first-class code: named for the behavior they pin
  (`test_parse_rejects_truncated_header`, not `test_parse_2`), one behavior
  per test, no shared mutable fixtures between tests.

## Layout

```
tests/
├── unit/          # fast, isolated, no I/O beyond tmp_path
└── integration/   # real-world end-to-end; marked 'integration'
```

- `integration` is a registered pytest marker (see `templates/pyproject.toml`).
  CI runs the layers as separate jobs — unit on the full matrix, integration
  as its own longer job (see `ci.md`).
- Integration tests that need secrets (API keys, model endpoints) read them
  from the environment and **skip with a clear reason** when unset — they
  never fail opaquely and never embed credentials.
- Integration tests clean up after themselves: temp dirs, not the repo; no
  residue in shared systems.

## Workflow interaction

For behavior changes, tests come first — follow the
`test-driven-development` skill (RED-GREEN-REFACTOR). This file governs
*what* the tests are; that skill governs *when* they are written.
