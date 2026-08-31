# ergon — the doer profile (SKELETON)

*ergon*: work, deed, craft.

An ergon agent is a **doer**: an agent whose persistent state is a
*capability library* — its skills, its run log, and its craft knowledge
(tool quirks, environment facts, failure modes). Its products are
**artifacts**: verified, provenance-carrying outputs deposited in a shared
store, and reports that state plainly what ran, what it produced, and what
was checked.

An ergon agent holds **no domain data**. When a commission needs a fact
about the world, the agent obtains it from a configured knowledge source —
which may be a sibling scuderia agent (via the agora; see `core/agora.md`), a
database, a public repository, an MCP service, or anything else the
instance is wired to. No particular knowledge source — and no companion
profile — is required. What is required is the discipline: domain facts are
requested fresh, labeled with provenance, and never cached as if they were
the agent's own knowledge.

The profile ships:

- `schema.yaml` — two page kinds, both about the craft, never domain
  content: `run` (a job log: commission, inputs, artifact, what broke) and
  `proposal` (a gated skill-creation proposal awaiting human approval).
- `SOUL.md` — the character skeleton. The spine (§2) is near-final; the
  rest is marked draft pending a live instance.
- `STYLE/` — the visual-artifact standard: a three-tier tree (spine →
  modality → type) plus machine-readable palette and preset assets. Copied
  into instances at scaffold and instance-owned thereafter (divergence is
  expected: style is crystallized from the instance's own corrected runs).
  Opinionated defaults crystallized from the founding instance's
  demonstrated runs; generic craft earned downstream is back-ported here
  with the `style-promote` skill.
- `manifest.yaml` + `example-instance/` — the install contract.

**This is a skeleton, not a stub** (contrast `profiles/oiko/`): an ergon
instance is being built toward a pilot, so the schema, manifest, and SOUL
spine are real. What is deliberately still missing (add when the instance
is scaffolded):

1. `conventions/` — prose frontmatter/page-kind conventions (schema.yaml
   is the machine-readable source of record; the prose must be written and
   the two kept in sync per the platform rule).
2. `skills/` — ergon-specific craft skills. The craft set now ships
   (planning/verification skills plus `style-promote`); the generic
   shared-store procedure is inherited from `core/skills/agora-exchange`;
   additional methodology (e.g. coding skills) is evaluated per instance
   before anything is vendored here.
3. `USER/` / `AGENTS.md` / `CLAUDE.md` templates (`STYLE/` now ships).
4. Card types for the feed, if runs/proposals ever want feed surfaces.

v1 scope: ergon agents are **reactive only** — they answer queries and
execute commissions. No cron, no initiation.
