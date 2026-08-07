---
name: retroactive-linking-shard-worker-patches-v2
description: "Use when folding shard 36 patches into the shard-worker."
triggers:
  - "shard worker abstract blockquote"
  - "shard worker ghost frontmatter links"
  - "shard worker search_files glob"
  - "shard worker wikilink surface"
---

# Retroactive linking shard worker — pending patches v2

This skill carries corrections and additions to
`retroactive-linking-shard-worker` that should be folded into the parent
skill's SKILL.md. It exists because the `skill_manage` resolver cannot locate
the parent skill (nested profile path mismatch — the skill lives at
`skills/<instance-category>/retroactive-linking-shard-worker/` but the resolver looks in
`skills/retroactive-linking-shard-worker/`).

## Patch 5 — Abstract blockquotes are the most common frozen zone (shard 36)

The `## Abstract` section in paper pages is a `>` blockquote containing the
paper's verbatim abstract. It is the first place entity names appear
(RFdiffusion, ProteinMPNN, ESM-2, etc.), making it tempting to link there.
Do NOT — the Abstract is frozen source text (a blockquoted `>` line). Link
the entity in a non-blockquoted section (Context, Approach, Findings,
Analysis, Limitations) instead. If the only mention of an entity is in the
Abstract blockquote, SKIP the body link entirely.

**Add to the Pitfalls section of `retroactive-linking-shard-worker` SKILL.md.**

## Patch 6 — Frontmatter `links:` may reference non-existent pages (shard 36)

Many pages carry frontmatter `links:` pointing to concept/method pages that
haven't been created yet (e.g. `methods/rfdiffusion`, `concepts/coevolution`,
`concepts/de-novo-protein-design`, `concepts/antibody-developability`). Do NOT
assume a target exists just because it appears in another page's frontmatter
links — always verify existence via the dir listing before LINKing. Do NOT
remove existing frontmatter links to non-existent pages; they are forward
references placed by the ingest process, not errors. In shard 36, only
`concepts/antibody-language-models`, `concepts/diffusion-language-models`,
`concepts/general-protein-language-models`, `concepts/scaling-laws`,
`concepts/backprop-protein-design`, `concepts/data-constrained-scaling`, and
`methods/masked-diffusion-language-models` actually existed — every other
concept/method link was a forward reference to a page not yet created.

**Add to step 5 (Populate frontmatter `links:`) of
`retroactive-linking-shard-worker` SKILL.md.**

## Patch 7 — `search_files` glob vs regex for existence checks (shard 36)

`search_files` with `target='files'` uses glob patterns (the `file_glob`
parameter), NOT regex — a regex alternation pattern in the `pattern` field
returns 0 results even when files exist. For batch existence-checking, use
a single `terminal` call: `ls papers/ methods/ concepts/ grants/ projects/
hypotheses/ | grep -iE 'slug1|slug2|...'`. Then confirm each hit with
`ls <dir>/<slug>.md` before LINKing.

**Add to step 2 (Candidate generation) of `retroactive-linking-shard-worker`
SKILL.md.**

## Patch 8 — Wikilink surface text should be human-readable (shard 36)

When inserting `[[target|surface]]`, the surface is the display text. Use the
entity's common name or the exact prose token (e.g.
`[[papers/watson-2023-rfdiffusion|RFdiffusion]]`,
`[[papers/frey-2024-walk-jump-sampling|Walk-Jump Sampling]]`), NOT the raw
path (`[[papers/foo|papers/foo]]`). When the original prose contains the
entity name as plain text, use that text as the surface.

**Add to step 4 (Apply LINKs) of `retroactive-linking-shard-worker` SKILL.md.**

## Curator action

When the profile resolution issue is resolved, fold patches 5–8 into the
appropriate sections of `retroactive-linking-shard-worker` SKILL.md, then
delete this skill (absorbed_into: `retroactive-linking-shard-worker`).
