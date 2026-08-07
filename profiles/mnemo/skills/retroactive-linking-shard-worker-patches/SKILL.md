---
name: retroactive-linking-shard-worker-patches
description: "Pending shard-worker patches: path, cites dir, dup PMIDs."
triggers:
  - "shard worker path prefix"
  - "shard worker cites directionality"
  - "shard worker duplicate pmid"
---

# Retroactive linking shard worker — pending patches

This skill carries corrections and additions to
`retroactive-linking-shard-worker` that the background curator should fold into
the parent skill's SKILL.md pitfalls section. It exists because the
skill_manage resolver could not locate the parent skill (nested profile path
mismatch) during the shard-14 review session; the patches are captured here so
they are not lost.

## Patch 1 — Shard path vault-scope prefix ≠ a directory (shard 14)

Shard files list paths with a vault-scope prefix (e.g.
`<vault>/papers/chang-2011-bcl6-dependent-follicular-helper-nkt.md`). This
prefix is the **repo name**, not a vault subdirectory — the actual file lives
at `<vault-root>/papers/chang-2011-...md`, NOT
`<vault-root>/<vault>/papers/...`. If `read_file` returns "File not found" for
a path constructed by naively prepending the vault root to the shard line,
strip the vault-scope prefix and the `.md` suffix and retry. The prompt
instructs stripping both for *result entries* (`target` field); the same
strip is required for the *read path* even though the prompt does not say so
explicitly. A quick `find <vault-root> -maxdepth 3 -name "<slug>*"` confirms
the real path if unsure.

**Add to the Pitfalls section of `retroactive-linking-shard-worker` SKILL.md.**

## Patch 2 — `cites:` edge directionality — successors ≠ predecessors (shard 14)

The existing rule says citation shorthand ("Author Year") → PROPOSE if
load-bearing, target exists, conf ≥ 0.9. But the **direction** of the edge
matters: `cites:` runs FROM the page TO a *predecessor it builds on*. When
prose names a *successor* ("concept used in He et al. 2025", "in contrast to
Cale 2017"), that successor cites *this* page — the relationship is already
captured in *this* page's `cited_by` frontmatter (populated by the successor
at its ingest). A `cites:` from this page to the successor is a reversed edge
and must NOT be proposed. Test: does the named paper build on / motivate /
refute THIS page, or does THIS page build on the named paper? Only the latter
is a `cites:`.

**Add to the Pitfalls section of `retroactive-linking-shard-worker` SKILL.md.**

## Patch 3 — Duplicate-PMID pages within a shard (shard 14)

Two pages may share the same PMID (and near-identical title) but carry
different slugs — e.g. `doria-rose-2014-cap256-vrc26-developmental-pathway`
and `doria-rose-2014-v1v2-developmental-pathway` both have PMID 24590074.
This is an entity-resolution issue (the same paper ingested twice under
different slugs). Detect it by comparing `pmid:` fields as you read. Do NOT
attempt to merge or deduplicate — that is outside shard scope (the
`entity-resolution` skill owns it). Record the pair in the result
`anomalies:` list and process each page independently on its own merits.

**Add to the Pitfalls section of `retroactive-linking-shard-worker` SKILL.md.**

## Patch 4 — `anomalies:` field in result schema

Shard 14 added an `anomalies:` list to the result YAML (not in the original
schema but a natural extension). The aggregator should treat it as
informational — items are flagged for the curator / `entity-resolution`
skill, not as committed or proposed edges. If the aggregator does not expect
this field, it is safely ignored (YAML parser skips unknown keys).

**Add a note to the Result schema section of
`retroactive-linking-shard-worker` SKILL.md.**

## Curator action

When the profile resolution issue is resolved, fold patches 1–3 into the
Pitfalls section and patch 4 into the Result schema section of
`retroactive-linking-shard-worker`, then delete this skill (absorbed_into:
`retroactive-linking-shard-worker`).
