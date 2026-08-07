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
Dated, append-only. Where the synthesis engine writes; the weekly-read trust
surface. Entry format below.
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

## The `Shifts` entry format

A shift must be **contestable** — the reasoning separates what the source *showed*
from what the mind *concluded for this concept*, and names the **edge** (what it
does not yet establish). The trigger is always cited (cite-or-flag).

```markdown
### 2026-07-04 — diffusion spur: fuzzy → sharpening
**Trigger:** [[papers/ni-2025-diffusion-super-data-learners]]
**Reasoning:** Shows DLMs extract >3× value per *unique* token vs. AR — but on
text, measured by perplexity + downstream NLP. Our paired-antibody corpus is the
prototypical data-constrained regime, so the efficiency argument plausibly
transfers → enough to justify a discriminating test, so the spur graduates from
hunch to bet. Does **not** yet establish the gain survives on antibody
sequences; the cross-seam analogy is untested.
```

An entry is: the shift in the heading, a cited trigger, then 2–4 sentences
separating *shown* from *concluded* and naming the edge.

**The `[unconfirmed]` marker.** A Shift authored *autonomously* — by the
`reinforce` phase, not directed by Bryan — carries an `[unconfirmed]` tag in its
heading (`### 2026-07-04 — [unconfirmed] diffusion spur: fuzzy → sharpening`) until
Bryan confirms it (drop the tag) or deletes the entry to reject it. A directed or
hand-authored Shift carries no marker. The tag is what lets the log be an
auto-appended surface Bryan polices in place, not a strictly-approved one.
