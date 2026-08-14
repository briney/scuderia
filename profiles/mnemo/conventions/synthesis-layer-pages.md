# Convention: synthesis-layer page anatomy

The canonical body structure for `concept` and `hypothesis` pages. Frontmatter
fields and edges live in `frontmatter.md` / `graph-and-links.md`; this file fixes
the **prose sections**, so every skill that writes these pages writes one shape.
Full rationale lives in the instance's private `docs/specs/`, not shipped in the template.

## `concept` — the persistent frontier

```markdown
---
kind: concept
slug: data-constrained-generative-modeling
title: "Data-constrained generative modeling for antibody sequences"
importance: 0.75
status: active
thesis_updated: 2026-07-06
related_concepts: [concepts/diffusion-language-models]
tags: [scaling, data-efficiency, generative-modeling]
---

## Thesis
The current best statement of the bet/lens. One or two paragraphs. Evolves.

## Frontier
The fuzzy, not-yet-applied spurs, each with an inline maturity marker.
- Adapt discrete diffusion to AbLMs for >3× per-token efficiency — *fuzzy*
- MoE capacity conditioned on templated/non-templated split — *sharpening*

## Open questions
The discriminating, mechanism-hungry questions.

## Shifts
Dated, append-only. The concept's **evidence log** — sourced facts, no opinion.
Where the synthesis engine reports what a source *showed*. Entry format below.
```

`Thesis`, `Frontier`, `Open questions`, `Shifts` are the core four. A concept's
crystallized children ("realized as") are a derived backlink of `rests_on:`, not
a hand-written section.

## `hypothesis` — the proving-ground funnel

```markdown
---
kind: hypothesis
slug: discrete-diffusion-ablm-data-efficiency
title: "Discrete-diffusion AbLMs beat AR AbLMs on paired-data efficiency"
importance: 0.6
status: open
origin: seeded
promise: [Beat, Scale]
draws_on: [concepts/data-constrained-generative-modeling, concepts/diffusion-language-models]
tags: [AbLM, diffusion]
---

## Claim
The falsifiable statement (or candidate-crystallization statement for an
engineering seed).

## Why it clears the bar
The Beat / Unlock / Scale / Explain argument. Thin here = weak hypothesis.

## Discriminating test
What would distinguish this from its strongest rival — or prove it won't work.
For a not-ready seed: what we'd need to see to believe it.

## Evidence
`supports:` / `refutes:` edges accumulate (derived backlinks + curated notes).

## Log
Dated working notes as it is pushed toward maturity or death.
```

On exit: `status: promoted` (the crystallized project/grant carries
`promoted_from:` back to this page — no `promoted_to:` here), or `status: killed`
plus a one-line `killed_reason` in frontmatter (retained, never deleted).

## The `Shifts` entry format — facts only, no opinion

Since 2026-08-13 the `## Shifts` log is a **fact ledger**, not an opinion log.
The governing rule is the fact/opinion line (`rem-cycle-contract.md`): an entry
reports what a source **showed**, with a citation, and says nothing about what it
*means* — that interpretation is deferred to the moment a grant, a paper, or a
conversation actually uses the concept. Reporting a fact is not a judgment call,
so the log is fully autonomous-writable.

```markdown
### 2026-07-04 — DLM per-token efficiency
**Source:** [[papers/ni-2025-diffusion-super-data-learners]]
**Shown:** DLMs extract >3× value per *unique* token vs. AR, on text
(perplexity + downstream NLP).
```

An entry is:
- **Dated** and **append-only** — never edited, never removed; dedup on
  `(concept, source)`.
- **Factual** — the "Shown" line states what the source demonstrated, in the
  source's own terms where possible. No "this establishes", no "this overturns",
  no "this challenges", no maturity-marker bumps, no "enough to justify a test".
- **Cited** — every entry carries its source (cite-or-flag, `SOUL.md`).

**What does NOT go in `## Shifts` anymore:** the `[unconfirmed]` hedge, the
"shown vs. concluded" split, the "mature-to-promote" / "contradict-thesis"
classification, the Frontier maturity-marker bump. All of that was *opinion*, and
it has moved: interpretation belongs in the grant draft, the brainstorm, or the
conversation — where "does this new evidence change anything" has the context to
be asked properly. Entries written before 2026-08-13 in the old hedged format
remain as historical record; new entries are facts-only.

The one guardrail is factual accuracy: the "Shown" line must be true to the
source. A claim that cannot be grounded in the source is simply not written
(cite-or-flag).
