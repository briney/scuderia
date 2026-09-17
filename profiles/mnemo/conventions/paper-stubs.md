# Convention: paper stubs and the ingestion queue

Read when creating, promoting, filling, or merging a paper stub. This is the
shared producer/consumer contract; `paper-ingest` owns per-paper extraction,
execution modes, and final verification. `ingest-pending-papers` owns draining
queue entries; `batch-drain` owns scheduling; `git-ops` owns closeout.

## Identity and minimal shape

A stub is a paper page with a source-derived citation seed and `tags: [stub]`.
Never construct a seed from recollection. Preserve the literal citation in
`## Citation`; copied identifiers are candidates until title/author/year and
identifier checks confirm them. Known metadata is retained, not replaced by
placeholders. Unknown DOI is null; an absent DOI on a stub is legacy incomplete
metadata, not proof that the paper has no DOI.

```yaml
kind: paper
slug: <paper-slug>
title: "<title from the source citation>"
status: unknown
needs-ingest: false
stub_source: paper-ingest
doi: null
authors: []
venue: ""
year: null
importance: 0.0
links: []
cited_by: []
tags: [stub]
```

Wrap this mapping in frontmatter fences and add `## Citation` containing the
source entry. Carry PMID, PMCID, arXiv ID, year, and venue when known. Add
source-specific provenance below the citation: the citing page/reference
location, or the sweep query and date. No R2 source is claimed before archival.

`stub_source` is a free-text original-producer label. New canonical values
are `paper-ingest`, `grant-ingest`, `literature-sweep`, and `literature-dive`;
retain existing legacy/custom labels without rewriting history. It is optional on legacy pages and
survives fills/merges; it does not identify the last editor. Document a newly adopted producer’s queue policy before relying on its label;
the label alone does not change queue priority.
When an existing stub is selected by another producer, retain its origin and
append the new provenance rather than overwriting it.

## Producer decisions

| Producer / input | Queue decision |
|---|---|
| paper-ingest bibliography walk | Stub only load-bearing methods, datasets, and frameworks. Set `needs-ingest: false` below five distinct citing papers/grants; promote to true at five or more. Never inline-ingest the resulting tree. |
| grant-ingest key citation | Set true immediately, including on an existing below-threshold stub. Fact-only citations are not stubs. |
| literature-sweep | Set true immediately. Mode 1 requires a resolved DOI; Mode 2 also permits a source-verified PMCID lead, with the DOI unresolved until identity validation. Record the query and matching domain/concept. |
| literature-dive | Tier 1 papers go to paper-ingest without the citation threshold; use isolated workers for batches. Tier 2 load-bearing references become ordinary threshold-gated stubs. |

Do not reset an already-queued stub to false when a later producer sees fewer
than five citing sources. A filled paper stays filled; another citation adds
an edge, not a fresh queue entry. Use parsed frontmatter and actual body state
to distinguish a full page from a below-threshold stub; false alone is not a
full-page marker.

`cited_by` contains only actual `papers/<slug>` and `grants/<slug>` citations,
deduplicated by source page. A campaign selection, concept relevance, or search
hit is not a citation. Put those connections in `links` and provenance text.
The review's citation contributes an edge only when verified in its reference
list; unavailable review discussion cannot establish the 'discussed in detail'
Tier 1 bar by itself.

The source request or producer’s existing rules determine what to ingest.
Delegation adds no selection gate: new papers and queued stubs use the same
paper-ingest worker. Producers and drains may run in the same session, after
the relevant inputs are ready. Prefer isolated workers for larger workloads;
small jobs can run inline.

## Fill, failure, and merge lifecycle

- Snapshot the input path, citation seed, `cited_by`, provenance, and attempt
  fields before dispatch. A same-page fill preserves existing citing entries
  in order; concurrent valid additions may extend the list and must not be lost.
- A page-only child returns `PAGE_READY` with the canonical output path and
  deferred obligations. It removes the stub tag after writing the distillation
  but retains `needs-ingest: true` until the parent completes required wiring.
  A crash therefore leaves the paper discoverable by the next drain.
- Once source checks, bibliography decisions, author wiring, and graph updates
  are verified, the parent sets `needs-ingest: false` and runs final checks.
  `needs-enrichment` is independent: abstract-only or preprint-in-place-of-
  published distillation remains true even when the ingest itself is complete.
- An actual failed attempt increments `ingest_attempts` and records
  `last_ingest_attempt` plus an Ingest-log diagnostic. Success never resets the
  accumulated failure count. Absence on a first attempt may be initialized to
  zero; skipped/held entries are not failed attempts. A producer's missing
  fields are not a license to overwrite existing values.
- A merge/rename returns the canonical path, preserves the union of citing
  sources and provenance, repairs required inbound references, and deletes
  only the verified duplicate. Preserve each existing list's order when
  adding missing entries. Re-read the canonical page; a missing input file
  alone is not evidence of a successful merge.
- A provider error after a write is neither automatic success nor automatic
  failure. Inspect the artifact and complete the same checks as any other fill.
  An abstract-only page that meets the retrieval-closure contract belongs in
  enrichment, not an endless failed-ingest retry loop.

Every producer lints its changed pages. Every drain accounts for each original
queue item exactly once (verified fill/merge, failed, held, skipped, or deferred),
including canonical paths after merges. Distinct completed output pages and
processed input items are separate counts.
