---
name: retroactive-linking-shard-worker-patches-v3
description: "Shard 37 patches to fold into the shard-worker parent skill."
triggers:
  - "shard worker parenthetical path reference"
  - "shard worker grant link target"
  - "shard worker mature frontmatter sync"
  - "shard 37 patches"
---

# Retroactive linking shard worker — pending patches v3

This skill carries corrections and additions to
`retroactive-linking-shard-worker` that should be folded into the parent
skill's SKILL.md. It exists because the `skill_manage` resolver cannot locate
the parent skill (nested profile path mismatch — the skill lives at
`skills/<instance-category>/retroactive-linking-shard-worker/` but the resolver looks in
`skills/retroactive-linking-shard-worker/`).

## Patch 9 — Parenthetical full-path references → wikilink (shard 37)

Mature paper pages frequently reference other entities by naming the entity
followed by the full vault path in parentheses, with NO wikilink markup:

- "The energy-based formulation connects to ProteinEBM
  (papers/roney-2025-proteinebm)."
- "This paper and CRADLE-1 (papers/bixby-2026-cradle-1-lead-optimization)
  both originate from the Genentech ecosystem."
- "The AbDesign database (papers/janusz-2025-abdesign-ddg-database)
  arrives at a complementary conclusion."

These are strong LINK candidates — the entity is named verbatim and the
target is explicitly referenced by full path. The sentence WOULD change
meaning if the target page didn't exist. Convert to `[[target|surface]]` at
the entity name:

- "connects to ProteinEBM ([[papers/roney-2025-proteinebm]])."
- "This paper and [[papers/bixby-2026-cradle-1-lead-optimization|CRADLE-1]]
  both originate..."
- "The AbDesign database ([[papers/janusz-2025-abdesign-ddg-database]])
  arrives at..."

When a markdown link to the same vault page follows separately (e.g.
`([Pacesa et al., 2025](papers/pacesa-2025-bindcraft.md))`), wikilink the
entity name and leave the markdown link intact:
`the [[papers/pacesa-2025-bindcraft|BindCraft]] pipeline
([Pacesa et al., 2025](papers/pacesa-2025-bindcraft.md))`.

This pattern is distinct from:
- Citation shorthand ("Author Year") → PROPOSE if load-bearing (shard 28)
- Markdown links to external URLs → SKIP (not vault pages)

**Frequency:** 4 of 10 pages in shard 37 had ≥1 parenthetical full-path
reference. Expect ~1-3 per mature page with analytical prose.

**Add to the Pitfalls section of `retroactive-linking-shard-worker` SKILL.md.**

## Patch 10 — Grant pages as valid LINK targets (shard 37)

The observations skill documented that grant-identifier shorthand
("R01AI180120") should be SKIP. Shard 37 refines this: grants referenced
by **full vault path** in analytical prose ARE valid LINK targets.

**LINK (body wikilink):** When prose references a grant by full path AND
the sentence's argument depends on the grant — e.g. "The Ono Pharma
antibody hit-expansion grant (grants/ono-pharma-ab-hit-expansion) and the
R01 data-driven antibody models grant (grants/r01ai193616-data-driven-ab-models)
both propose ML-guided affinity optimization." The sentence is about the
grants' specific aims. Convert to `[[grants/<slug>]]` and mirror into
frontmatter `links:`.

**SKIP:** Grant-identifier shorthand ("R01AI180120", "R01 AI171438") without
a full path — these are labels, not verbatim entity names. The page slug
is `r01ai180120-prepandemic-cov-bnab-west-africa`, not `R01AI180120`.

**Directionality note:** A `cites:` edge from paper→grant is always wrong
direction — grants cite papers via `cited_by`, not vice versa. But a body
wikilink (forward-link) from paper→grant is fine — it's a navigational
link, not a citation edge.

**Add to the Pitfalls section of `retroactive-linking-shard-worker` SKILL.md,
extending the existing grant-identifier shorthand SKIP rule.**

## Patch 11 — Mature-page frontmatter sync can be 4-5 entries (shard 37)

Shard 28 established that mature pages need ~2-5 frontmatter-sync entries.
Shard 37 had a variant: the hie-2022 page (importance 0.82) had **5
pre-existing body wikilinks unmirrored** in frontmatter `links:` —
`papers/mille-fragoso-2025-germinal-antibody-design`,
`papers/candido-2026-esmc-world-model`, `papers/pacesa-2025-bindcraft`,
`papers/roney-2025-proteinebm`, `methods/stepwise-design`. The janusz-2025
page had 4 unmirrored body wikilinks including `methods/mab-maker` and
`methods/stepwise-design`.

**Takeaway:** For pages with rich Analysis sections that reference many
methods/projects, the frontmatter-sync count can be 4-5, not 2-3. Scan
the **entire body** for `[[...]]` markup, not just the sections where you
added links. Methods pages (`methods/`) and projects pages (`projects/`)
are valid frontmatter `links:` entries — not just `papers/` and
`concepts/`.

**Add to the Pitfalls section of `retroactive-linking-shard-worker` SKILL.md,
extending the existing mature-page pattern.**

## Patch 12 — Patch 1 (path prefix) from v1 still not folded (shard 37)

The vault-scope path prefix issue (Patch 1 in `retroactive-linking-shard-worker-patches`)
was re-encountered in shard 37 — the worker hit the doubled
doubled `<vault>/<vault>/papers/...` path and wasted read_file calls before
stripping the prefix. This patch was documented in the v1 patches skill
but has NOT yet been folded into the parent SKILL.md (the resolver issue
prevents it). Reiterating here for the curator: the path prefix strip
rule MUST go into step 1 (Read in full) of the parent SKILL.md.

## Patch 13 — Patches 2-4 from v1 still not folded

Same resolver issue prevents folding patches 2 (cites: directionality),
3 (duplicate PMID), and 4 (anomalies: field) from the v1 patches skill.
Reiterating for the curator: all three are still pending and should be
folded into the parent SKILL.md when the resolver is fixed.

## Curator action

When the profile resolution issue is resolved, fold patches 9–11 into the
Pitfalls section of `retroactive-linking-shard-worker` SKILL.md, confirm
patches 1–4 (v1) and 5–8 (v2) have been folded, then delete all three
patches skills (absorbed_into: `retroactive-linking-shard-worker`).

## References

- `references/shard-37-observations.md` — session-specific detail from shard 37
  (parenthetical full-path LINK pattern with examples, grant-page LINK
  targets, mature-page frontmatter sync count, result metrics).
