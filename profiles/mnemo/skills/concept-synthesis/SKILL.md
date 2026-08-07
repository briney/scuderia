---
name: concept-synthesis
description: Deduplicate raw concept stubs, tier them (T1 Canon to T4 Riff), synthesize the durable ones, and cluster them into an intellectual map at concepts/README.md. Use to find the patterns across Bryan's recurring research ideas and trace how an idea sharpened over time.
triggers:
  - "synthesize my concepts"
  - "find patterns across my notes"
  - "build my intellectual map"
  - "trace how this idea evolved"
  - "canon vs riff"
  - "deduplicate the concept stubs"
---

# concept-synthesis — from raw stubs to an intellectual map

Ambient capture (`signal-detector`, `idea-ingest`, `voice-note-ingest`) files a
`concept` page for nearly every idea Bryan articulates. Over months that
produces hundreds of stubs — many of them near-duplicates of each other, none
tiered, none clustered. This skill turns that raw material into a curated map
of Bryan's recurring research ideas and how they sharpened over time.

> **Conventions:** `skills/conventions/quality.md` (citations, forward-only linking,
> the notability gate), `skills/conventions/graph-and-links.md` (edge forms),
> `_output-rules.md` (verbatim-quote fidelity), `skills/conventions/test-before-bulk.md`
> (test the dedup pass on a sample before running the corpus),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/conventions/rem-cycle-contract.md` (the phase result + tiers, when run as a
> rem-cycle phase-5 delegate).

## Capabilities

`brain-search`, `brain-read`, `brain-write`. `brain-search` is load-bearing
here — semantic ranking finds near-duplicate concepts; under a keyword-only
fallback, run a wider net and accept more false positives.

## What this guarantees

- No two `concept` pages survive as the same idea in different words.
- Every surviving concept is tiered by how durable and recurring it is.
- T1/T2 concepts carry a synthesis — the *evolution* of the idea, not a
  repetition of it.
- The corpus ends with a navigable intellectual map at `concepts/README.md`.

## Phases

### 1. Dedup and merge

Search the brain for the full set of `concept` pages and reduce duplicates:

- **Word-overlap dedup** — high title + first-paragraph overlap flags a likely
  duplicate.
- **Substring dedup** — "founder-mode generalization" subsumes "founder mode".
- **Semantic dedup** — read the candidates and judge: same idea, or genuinely
  distinct?

Merge each duplicate into one canonical page. Preserve alternate phrasings in
an `aliases:` frontmatter list so search still finds them. Fold the merged
page's wikilinks and typed edges into the canonical page; never hand-write a
backlinks section (`skills/conventions/graph-and-links.md`).

### 2. Score and tier

Score each canonical concept from signals already present on its page:

- **Frequency** — how many distinct sources reference the concept.
- **Timespan** — first mention to last mention, in days.
- **Breadth** — the count of distinct months it appears in.

Research ideas carry no engagement signal — do not score on attention or
popularity. Durability is the signal: an idea Bryan keeps returning to, and
keeps sharpening, ranks high.

| Tier | Label | Shape |
|---|---|---|
| T1 | Canon | A recurring framework — sharp, returned to across many months. |
| T2 | Developing | Sharpening; may become canon. |
| T3 | Speculative | Tested once or twice; unproven. |
| T4 | Riff | A one-off aside. |

Guardrails: no concept is T1 with fewer than ~6 mentions or under a ~4-month
span; no concept is T4 with a span over ~3 months.

### 3. Synthesize T1 and T2

For the T1 and T2 concepts only, read the concept page and its source pages, and
write the canonical concept body — `Thesis`, `Frontier`, `Open questions`,
`Shifts` — per `skills/conventions/synthesis-layer-pages.md`. Capture **evolution, not
repetition**: how the idea was first framed and how it sharpened becomes dated
`Shifts` entries; the current best statement is the `Thesis`. Use Bryan's
verbatim quotes for the sharpest articulations (`_output-rules.md`) — never
paraphrase, never invent a quote or a date. T3 and T4 stay as stubs.

### 4. Cluster and map

Group the tiered concepts into intellectual clusters — domains within Bryan's
research program at the immunology × AI interface. Name each cluster
concretely; "various topics" means the cluster is not real. Write a master map
at `concepts/README.md`: the clusters, their member concepts, and the idea
genealogies (concept A sharpened into concept B). Link forward with
`[[concepts/slug]]` wikilinks throughout.

## Output formats

### A T1 concept page (post-synthesis)

The body follows the canonical concept anatomy in
`skills/conventions/synthesis-layer-pages.md` — `Thesis` / `Frontier` / `Open questions`
/ `Shifts`. The tiering signals this skill computes ride in frontmatter and a
header line; the idea's *evolution* is captured as dated `Shifts` entries (the
old standalone `Evolution` table folds into `Shifts`), and the sharpest verbatim
articulation anchors the `Thesis`.

```markdown
---
kind: concept
slug: <concept-slug>
title: "<concept name>"
importance: 0.75
status: active
tier: 1
tier_label: Canon
mention_count: 18
distinct_months: 8
first_mention: YYYY-MM-DD
last_mention: YYYY-MM-DD
aliases: ["alternate phrasing"]
related_concepts: [concepts/sibling-concept]
---

# <concept name>

**Tier 1 — Canon** | 18 mentions across 8 months

## Thesis
Two to four paragraphs: the current best statement of the bet, what it means in
Bryan's program, and what it argues against. Anchor the sharpest point on a
verbatim quote — `> "…" [Source: Bryan, <context>, YYYY-MM-DD]`.

## Frontier
Fuzzy, not-yet-applied spurs, each with a maturity marker (*fuzzy* / *sharpening*).

## Open questions
The discriminating, mechanism-hungry questions.

## Shifts
### YYYY-MM-DD — <what changed>
**Trigger:** [[papers/<slug>]] (or the source of the shift)
**Reasoning:** what the source showed vs. what it means for this concept, and the
edge it does not yet establish.
```

### The cluster map at `concepts/README.md`

```markdown
# Intellectual map

## Canon (T1) — N concepts
Recurring frameworks that span the research program.

### <Cluster name>
- [[concepts/slug]] — one-line characterization

## Developing (T2) — N concepts
## Speculative (T3) — N concepts
## Riff (T4) — N concepts

## Genealogies
- [[concepts/early-idea]] → sharpened into [[concepts/later-idea]]

## Stats
- Total concepts: N | T1: N | T2: N | T3: N | T4: N
- Earliest source: YYYY-MM-DD | Latest: YYYY-MM-DD
```

## As a rem-cycle phase

Invoked by the orchestrator as part of **phase 5 (consolidation)**, under
`skills/conventions/rem-cycle-contract.md`. The graph is Bryan's to curate, so the dream
**proposes** every generative change and auto-commits only the mechanical:

- **Mode.** `dry-run` (report only) or `normal` (auto-commit the mechanical,
  queue the rest).
- **Tiers:**
  - *Auto* → `committed[]`: the tier recompute (T1–T4, `category: tier`), the
    `concepts/README.md` map refresh (`category: map-refresh` — a derived,
    regenerable index), and an **exact-duplicate** stub merge.
  - *Propose* → `proposed[]`: a **fuzzy / semantic** concept merge (a corpus-wide
    reference rewrite — the `entity-resolution` rule; a body wikilink and a typed
    edge for one pair stay distinct), and the **synthesis** of a T1/T2 concept
    (authoring durable prose is generative — `category: synthesis`, with a draft
    outline for Bryan to approve; author on approval, never in the dream).
- **Tiering applies to all concept pages.** Ambient idea-stubs tier on
  frequency/timespan signals; literature-syntheses tier on their own signal
  basis — inbound edge count, shift count, grant/project `rests_on:` usage.
  The consolidation phase recomputes tiers weekly regardless of whether
  ambient stubs exist; only the dedup/merge side stays stub-driven.
- **Output.** The fenced-yaml phase result — `metrics` (`concepts_scanned`,
  `merged_auto`, `merges_proposed`, `retiered`, `syntheses_proposed`). No
  chaining.

## Anti-patterns

- Running the full dedup pass without testing it on a sample first
  (`skills/conventions/test-before-bulk.md`).
- In phase mode: auto-authoring a T1/T2 synthesis or auto-merging a fuzzy
  duplicate — both are generative / reference-rewriting; propose them.
- Synthesizing T3/T4 — they may never sharpen; the synthesis effort is wasted.
- Hallucinating a quote or a date — the `Shifts` entries must be verifiable
  against the source pages.
- Generic cluster names. If you cannot name the cluster, it is not a cluster.
- Re-synthesizing a T1 page (adding a `Shifts` entry or rewriting the `Thesis`)
  when there is no new source material since its last synthesis.
- Scoring concepts by attention or popularity — research ideas have no
  engagement signal; durability is the only axis.
