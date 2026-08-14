---
name: concept-coalesce
description: >
  The mechanical half of concept capture. Reads the concept-stub notes, clusters
  the stubs that point at one idea, and — when ≥3 independent sourced signals
  coalesce AND the idea clears a "so what" gate — auto-aggregates them into a
  `concept` page (facts, no opinion). Never creates a hypothesis. Runs as a
  rem-cycle phase (weekly) or standalone.
triggers:
  - "coalesce the concepts"
  - "coalesce concept stubs"
  - "which stubs should become concepts"
  - "promote my concept stubs"
---

# concept-coalesce — from stubs to sourced concepts

The concept-stub pipeline (`conventions/concept-stub-capture.md`) files cheap,
verbatim `note` pages for transient ideas that may coalesce. This skill is the
**decide later** half: it reads the stubs and, when enough independent signals
point at one idea, **aggregates** them into a `concept` page. It is mechanical
and fact-only — the opinion (is this *important* enough to shape a research
thread?) is deferred to `intersect`'s single-item surfacing and to conversation.

The division of labor with `intersect` is exact: **coalesce does routine
fact-aggregation** (low floor, no value-ranking); **intersect does singular
value-ranking** (one item). Coalesce never asks "is this the thing to think
about" — it only asks "has this idea recurred enough, independently, that
aggregating its sourced facts makes future retrieval and drafting better."

> **Conventions:** `concept-stub-capture.md` (what a stub is, the
> `is_concept_stub: true` marker), `rem-cycle-contract.md` (the fact/opinion
> line — concept aggregation is fact and auto-commits; hypothesis creation is
> forbidden here), `synthesis-layer-pages.md` (the concept anatomy), `quality.md`
> (the "so what" gate). Character: `SOUL.md` — no fabricated confidence.

## Capabilities

`brain-read`, `brain-search` (semantic + keyword clustering), `brain-write`.
Universal; no external I/O.

## What this guarantees

- **Facts only.** The aggregated `concept` carries sourced claims pulled from the
  stubs and their source pages — no synthesis, no thesis, no frontier bet. The
  "so what" is a filter (does it earn a page), not a prose section.
- **Fully autonomous when the bar clears.** ≥3 independent sourced signals + a "so
  what" pass → auto-create the concept (`concept-create` class, armed 2026-08-13).
  Below the bar → the stub stays; nothing is proposed.
- **Never creates a `hypothesis`.** Testable claims are conversation-only
  (`rem-cycle-contract.md`). A cluster whose natural output would be a hypothesis
  is simply left un-aggregated — it is not this skill's lane.
- **The "so what" gate is real, not a formality.** Recurrence alone is not
  enough; the idea must clear the notability test (`quality.md`): will the mind or
  your human reference this again, does it sit on a `RESEARCH.md` thread, would a
  grant draft actually draw on it. A recurring-but-inert idea stays a stub.
- **Non-destructive, idempotent.** Dedup on idea identity; re-run over unchanged
  stubs is a no-op.

## The dual gate

1. **Recurrence floor (programmatic):** ≥3 **independent** signals for one idea —
   distinct stubs / source pages / an under-developed existing concept. Two stubs
   that both quote the same conversation are one signal, not two.
2. **"So what" (judgment, but bounded):** does aggregating this idea into a
   `concept` page improve future retrieval or drafting? If it would only add a
   page nobody references, it stays a stub.

Only when **both** clear does coalesce auto-create. The floor is deliberately low
(so cheap ideas coalesce); the "so what" gate is what keeps it from flooding
`concepts/` with mediocre pages.

## Phases

1. **Select.** Enumerate every `notes/*.md` with `is_concept_stub: true`, plus
   the existing `concepts/` (to check overlap and under-developed nodes). Grep —
   a cheap scan, unbudgeted.
2. **Cluster.** Group stubs by the idea they point at, using forward-link
   proximity, title/verbatim-trigger overlap, and one `brain-search` pass. Count
   **independent** signals per cluster.
3. **Gate.** Apply the dual gate: ≥3 independent signals, then "so what". A
   cluster that fails either is left as stubs (`metrics.no_ops`).
4. **Aggregate.** For each clearing cluster, author the `concept`: the sourced
   facts from the stubs (verbatim where that's the information), forward `links:`
   onto the source pages and stub notes, `status: active`, `origin: detected`.
   Flip the contributing stubs to `status: promoted`. No `## Thesis` synthesis —
   the facts stand; the lens is authored later, if at all, in conversation.
5. **Return** the phase result (below) or, standalone, a conversational summary.

## As a rem-cycle phase

The weekly phase (5c; `rem-cycle-contract.md`). The orchestrator passes `mode`;
this skill returns the fenced-yaml phase result:

- **Mode:** `normal` (auto-create clearing clusters) or `dry-run` (report
  intended creations in `committed[]`, write nothing). `proposed[]` is empty —
  there is no propose lane for a mechanical aggregation.
- **`committed[]`** — the creations (`category: concept-create`), each with the
  `sources:` (stub + source page slugs) and the "so what" justification span.
- **`metrics`** — `stubs_scanned`, `clusters_found`, `concepts_created`,
  `no_ops` (below-floor or failing "so what").

## Output

- **Auto-created `concept` page** — sourced facts, forward edges, no synthesis.
- **Standalone** — a conversational summary: what coalesced, what stayed a stub.

## Anti-patterns

- Aggregating below the recurrence floor, or with non-independent signals (two
  stubs quoting one conversation).
- Skipping the "so what" gate — recurrence alone creates a junk page.
- Writing a `## Thesis` / `## Frontier` / `## Shifts` opinion into the new
  concept — that is conversation's job, not aggregation's.
- Creating a `hypothesis` — conversation-only, never here.
- Re-ranking clusters (asking "which is most important") — that is `intersect`'s
  single-item job, not this skill's.
- Fetching anything — coalesce consolidates the graph, it never reaches outside.
