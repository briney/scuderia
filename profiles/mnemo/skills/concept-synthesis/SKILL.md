---
name: concept-synthesis
description: Deduplicate raw concept stubs, tier them (T1 Canon to T4 Riff), synthesize the durable ones, and cluster them into an intellectual map at concepts/README.md. Use to find the patterns across your human's recurring research ideas and trace how an idea sharpened over time.
triggers:
  - "synthesize my concepts"
  - "find patterns across my notes"
  - "build my intellectual map"
  - "trace how this idea evolved"
  - "canon vs riff"
  - "deduplicate the concept stubs"
eval_contract:
  goal: Reduce the ambient concept-stub corpus to a deduplicated, tiered, mapped intellectual layer without losing a distinct idea or inventing one.
  dimensions:
    - "DEDUP — merges fold aliases and edges; no two pages survive as the same idea"
    - "TIERING — tiers derive from frequency/timespan/breadth signals, never attention or popularity"
    - "SYNTHESIS — T1/T2 bodies capture evolution, verbatim-anchored, not repetition"
    - "MAP — concepts/README.md names real clusters and genealogies"
  hard_fails:
    - Merging two concepts that are not verifiably the same idea.
    - Hallucinating a quote, a date, or a Shifts entry.
    - Authoring synthesis prose inside a scheduled rem-cycle run.
---

# concept-synthesis — from raw stubs to an intellectual map

Curate existing concepts and ambient concept-stub notes by deduplicating,
tiering and mapping their source-grounded ideas. Ambient capture follows
`concept-stub-capture.md`; this skill does not assume every idea already has
a concept page. `concept-coalesce` owns mechanical stub-cluster aggregation;
`topic-synthesis` owns a named literature synthesis.

> **Conventions:** `skills/conventions/quality.md` (citations, forward-only linking,
> the notability gate), `skills/conventions/graph-and-links.md` (edge forms),
> `_output-rules.md` (verbatim-quote fidelity), `skills/conventions/test-before-bulk.md`
> (test the dedup pass on a sample before running the corpus),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/conventions/rem-cycle-contract.md` (the phase result and binary gate, when run as a
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
popularity. Durability is the signal: an idea your human keeps returning to, and
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
write the canonical concept body per `skills/conventions/synthesis-layer-pages.md`
— load the owning anatomy when authoring. The current synthesis and any
interpretation of how the idea changed belong in Thesis/Frontier; Shifts
uses only the canonical dated Source/Shown factual entries. Preserve earlier
entries, source dates and exact human quotations; never invent a quote or
date. T3/T4 remain stubs. Scheduled runs skip this authoring step.

### 4. Cluster and map

Group the tiered concepts into intellectual clusters — domains within your human's
research program. Name each cluster concretely; "various topics" means the cluster
is not real. Write a master map at `concepts/README.md`: the clusters, their member
concepts, and the idea genealogies (concept A sharpened into concept B). Link
forward with `[[concepts/slug]]` wikilinks throughout.

## Output formats

### A synthesized concept page

The body and its section definitions are owned by
`skills/conventions/synthesis-layer-pages.md` — load it when authoring; do not
restate its anatomy here. What this skill adds on top of the canonical anatomy
are its own tiering signals, which ride in frontmatter and a header line, with
the sharpest verbatim articulation anchoring the `Thesis`:

Use the canonical concept frontmatter and add `tier`, `tier_label`,
`mention_count`, `distinct_months`, `first_mention`, `last_mention`, and
verified `aliases`/`related_concepts`. A header line reports the computed
tier, mention count and months; never copy example values as measurements.

### The cluster map at `concepts/README.md`

This is this skill's own output artifact (not a page anatomy) — the map spec:

- One section per tier (`Canon (T1)` … `Riff (T4)`), each naming its
  clusters; under each cluster, one bullet per member concept —
  `[[concepts/slug]] — one-line characterization`.
- A `## Genealogies` section: `[[concepts/early-idea]] → sharpened into
  [[concepts/later-idea]]`.
- A `## Stats` line: total concepts per tier; earliest/latest source dates.

## As a rem-cycle phase

Runs as its own cron job as part of **phase 5 (consolidation)**, under
`skills/conventions/rem-cycle-contract.md` (binary gate, 2026-08-15):

- **Commit** → `committed[]`: the tier recompute (T1–T4, `category: tier`), the
  `concepts/README.md` map refresh (`category: map-refresh` — a derived,
  regenerable index), an **exact-duplicate** stub merge, and a fuzzy/semantic
  concept merge ONLY when the two nodes are verifiably the same idea (same
  sources, same referent — fold + corpus-wide reference rewrite in one commit).
- **Drop** → counted in `metrics.dropped`: a fuzzy merge whose same-idea
  verification fails.
- **Notable** → `notable[]`: a T1/T2 concept whose durable prose is stale
  relative to its Shifts — authoring that prose is generative (opinion), so
  the dream detects ripeness and signals it; the synthesis happens in
  conversation.
- **Tiering applies to all concept pages.** Ambient idea-stubs tier on
  frequency/timespan signals; literature-syntheses tier on their own signal
  basis — inbound edge count, shift count, grant/project `rests_on:` usage.
  The consolidation phase recomputes tiers weekly regardless of whether
  ambient stubs exist; only the dedup/merge side stays stub-driven.
- **Output.** The raw-YAML phase result — `metrics` (`concepts_scanned`,
  `merged_auto`, `retiered`, `dropped`). No chaining.

## Closeout and verification

Read back all changed pages, preserved quotes/edges and map counts; validate
frontmatter and any merge's inbound repairs. The completed standalone unit is
the verified concept changes plus map; use `git-ops`. In a scheduled or nested
run the owning primary closes the unit, and children return paths/checks only.
Procedure edits follow change-scoped verification in
`skills/conventions/skill-hygiene.md`. When map/phase behavior requires an
execution check, use bounded real-source input in scratch, with no test
delivery or production consolidation.

## Anti-patterns

- Running the full dedup pass without testing it on a sample first
  (`skills/conventions/test-before-bulk.md`).
- Authoring a T1/T2 synthesis in the dream — generative prose is
  conversation-only; emit a `notable:` ripeness signal instead.
- Synthesizing T3/T4 — they may never sharpen; the synthesis effort is wasted.
- Hallucinating a quote or a date — the `Shifts` entries must be verifiable
  against the source pages.
- Generic cluster names. If you cannot name the cluster, it is not a cluster.
- Re-synthesizing a T1 page (adding a `Shifts` entry or rewriting the `Thesis`)
  when there is no new source material since its last synthesis.
- Scoring concepts by attention or popularity — research ideas have no
  engagement signal; durability is the only axis.
