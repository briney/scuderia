# ergon — the doer profile (SKELETON)

*ergon*: work, deed, craft. The doer complement to mnemo's thinker.

A mnemo instance is a **mind**: its persistent state is a knowledge graph.
An ergon instance is a **doer**: its persistent state is a *capability
library* — its skills, its run log, and its craft knowledge (tool quirks,
environment facts, failure modes). It holds **no domain data**: when it
needs to know something, it asks a knowledge agent, fresh, every time. Its
products are artifacts — verified, provenance-carrying, deposited in the
shared store.

The collaboration contract (shared store, message shapes, provenance
schemas, gated skill creation) lives at **`core/agora.md`** — it spans
profiles and is owned by the platform, not by ergon.

**This is a skeleton, not a stub** (contrast `profiles/oiko/`): an ergon
instance is being built toward a pilot, so the schema, manifest, and SOUL
spine are real. What is deliberately still missing (add when the instance
is scaffolded):

1. `conventions/` — prose frontmatter/page-kind conventions (schema.yaml
   is the machine-readable source of record; the prose must be written and
   the two kept in sync per the platform rule).
2. `skills/` — ergon-specific craft skills. The generic agora procedure is
   already inherited from `core/skills/agora-exchange`; coding methodology
   is evaluated as a harness plugin before anything is vendored here.
3. `STYLE.md` / `USER/` / `AGENTS.md` / `CLAUDE.md` templates.
4. Card types for the feed, if runs/proposals ever want feed surfaces.

v1 scope: ergon agents are **reactive only** — they answer queries and
execute commissions. No cron, no initiation.
