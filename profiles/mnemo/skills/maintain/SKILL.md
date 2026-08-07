---
name: maintain
description: Periodic brain health checks — stale pages, orphans, broken and missing links, citation gaps, filing violations, tag drift — plus the importance-score recompute pass. Reports findings as a health-report table.
triggers:
  - "brain health"
  - "run maintenance"
  - "check the brain"
  - "orphan pages"
  - "stale pages"
  - "link audit"
  - "citation audit"
  - "recompute importance"
---

# Maintain — brain health checks

Periodic upkeep of the knowledge graph. Health is assessed by *scanning the
corpus* — `brain-search` plus reading files — across a fixed set of
dimensions, fixing what is safe to fix and reporting the rest. This is the
**broad-scope** member of the audit cluster; see `RESOLVER.md` "Audit
cluster" for the scope split — frontmatter shape lives in
`frontmatter-guard`, citation-claim health lives in `citation-fixer`, and
this skill chains into them when their narrower bug class surfaces. It also
serves as the `rem-cycle` delegate for **phase 1 (hygiene)** and **phase 7
(importance recompute)** — see *As a rem-cycle phase* below.

> **Conventions:** `skills/conventions/quality.md` (citations, forward linking, the
> notability gate), `skills/conventions/graph-and-links.md` (the edge forms, derived
> backlinks), `skills/conventions/importance-scoring.md` (the salience score),
> `_brain-filing-rules.md` (where a page belongs),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/conventions/rem-cycle-contract.md` (the phase result + commit tiers, when
> run as a rem-cycle phase).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url` (for
citation-existence checks against open APIs). `brain-search` optional.
This is the skill that owns the importance-recompute LLM pass per
`skills/conventions/importance-scoring.md`.

## What this guarantees

- Every dimension below is checked and reported — even when it is clean.
- Each issue found names a specific page and a specific fix.
- A page is never deleted without confirmation.
- A page is read in full before it is edited.

## The dimensions

### Stale pages

A page whose synthesis lags the evidence on it — new papers, new results, or new
notes reference the page's subject, but its body has not been revised to reflect
them.

- Find candidates by checking which referenced pages have newer neighbours.
- Read the page and its inbound references; if the synthesis is genuinely behind,
  flag it (or chain into `restructure-thin-page` to restructure it).

### Orphan pages

A page with no inbound links — nothing in the corpus references it.

- Inbound edges are derived by scanning for `[[kind/slug]]` references and typed
  frontmatter edges (`skills/conventions/graph-and-links.md`).
- Decide per page: genuinely isolated (a candidate for review), or just
  missing a link that a related page should carry. Prefer adding the forward
  link on the related page over deleting the orphan.

### Dead links

A wikilink or typed edge pointing to a `kind/slug` that has no file.

- **Exclude `authors:` edges to un-promoted people.** A paper's `authors:` list
  points at `people/<slug>` for every author, and most have no page by design —
  the ledger tracks them (`author-ledger.md`, `graph-and-links.md`). These are
  **not** dead links; counting them inflates the metric ~15×. Scan the other
  edge types and body wikilinks.
- **Fix or flag by tier:** retargeting a wrong slug to an **existing** page is a
  mechanical **auto** `dead-link-fix`. A link whose target *should exist but does
  not* is `target_exists: false` → **propose** creating it (the slug is a guess),
  never auto (`rem-cycle-contract.md`). A wrong link with no right target →
  propose removing the edge.

### Missing forward-links

A page that names another page's subject in prose without linking it.

- Read the page, spot the unlinked mention, add the `[[kind/slug]]` wikilink on
  the page being read. Forward only — never hand-write a backlink.

### Citation audit

Substantive claims with no source.

- Read a sample of recently touched pages; check that load-bearing claims carry
  `[Source: ...]` (`skills/conventions/quality.md`).
- Flag an uncited claim with `[needs-citation]` — an honest marker, never a
  silent gap. (`citation-fixer` does the deeper repair pass.)

### Filing-rule violations

A page filed under the wrong kind, or in a directory that is not one of the
page kinds (`page-kinds.md`).

- Apply `_brain-filing-rules.md`: the primary subject sets the kind. A page whose
  `kind` and directory disagree, or that sits outside the kind directories
  (`page-kinds.md`), is misfiled — flag it or re-file it.

### Tag consistency

Tag drift — `mab` vs `monoclonal-antibody`, `lm` vs `language-model`.

- Find variant spellings of the same tag; standardize to the most common form.
- Be conservative: confirm two tags really mean the same thing before merging.

### Pending-ingest & unknown-status backlog (detect-only)

Papers carrying `needs-ingest: true` (stubs awaiting fill) or `status: unknown`
(publication status unresolved). Both are completed by **external I/O** — a
DOI/PDF fetch (`ingest-pending-papers`) or a publication-status lookup — which is
a **waking** concern, not a dream's. Here: **count and report** the backlog only;
never fetch, never fill. This keeps the queue visible without pulling external
I/O into an unattended run.

### Importance recompute

`skills/conventions/importance-scoring.md` defines `importance` as a *recomputed* score,
refreshed by a periodic maintenance pass — and this skill owns that pass.

- It is an LLM pass over the corpus. For each page, read the signals the
  convention names — tag boost over the research-relevant tag set, annotation
  density (how much of Bryan's own thinking is on the page), and graph
  centrality (how connected the page is) — and write a refreshed `importance`
  value to frontmatter.
- Treat the existing value as the last pass's output, not ground truth.

## Output — the health report

Report findings as a table, one row per dimension:

```
## Brain Health Report — YYYY-MM-DD

| Dimension              | Issues found | Fixed | Remaining |
|------------------------|--------------|-------|-----------|
| Stale pages            | N            | N     | N         |
| Orphan pages           | N            | N     | N         |
| Dead links             | N            | N     | N         |
| Missing forward-links  | N            | N     | N         |
| Citation gaps          | N            | N     | N         |
| Filing violations      | N            | N     | N         |
| Tag inconsistencies    | N            | N     | N         |
| Importance recompute   | N            | N     | N         |

### Details
[Per-dimension: the specific pages and the action taken on each.]

### Needs confirmation
[Anything that requires Bryan's decision — deletions, ambiguous re-filings.]
```

## As a rem-cycle phase

When the `rem-cycle` orchestrator invokes this skill as a phase (not a standalone
health check), it runs under `skills/conventions/rem-cycle-contract.md` and changes what
runs, what commits, and what it emits:

- **Scope.** The orchestrator passes `scope` — `hygiene` (phase 1: every
  dimension above *except* importance) or `importance` (phase 7: the recompute
  pass only). Cadence drives it — hygiene runs nightly, importance weekly — so
  run **only** the requested dimensions, not the whole sweep.
- **Mode.** `dry-run` (report every change, write nothing) or `normal` (auto-tier
  commits, propose-tier queues). Default `dry-run` until the cycle earns trust.
- **Tiers** (`rem-cycle-contract.md`):
  - *Auto* → `committed[]`: mechanical, high-confidence fixes — a
    missing-forward-link wikilink to an existing page (`category: forward-link`),
    a dead-link **retarget** to an existing page (`dead-link-fix`), filing
    normalization, a tag merge whose synonymy is certain (`tag-merge`; its
    `target` is the tag, not a page).
  - *Propose* → `proposed[]`: every judgment call — any page deletion, an
    ambiguous re-file, a tag merge whose synonymy is uncertain, a stale-page
    restructure. Each carries an evidence basis.
- **Importance recompute is graduated by swing** (the ±0.3 delta is the
  auto/propose boundary, absolute in `[0, 1]`):
  - `|Δ| ≤ 0.3` → **auto-write** the refreshed value (`committed[]`,
    `category: importance`); in `dry-run` it is reported, not written.
  - `|Δ| > 0.3` → **propose only** — record the recompute in `proposed[]` and do
    **not** write it; a large swing is a judgment call.
  - **Any *downward* recompute of a page tagged `seminal` / `key-citation` (or
    pinned / identity) → propose, never auto, regardless of size** — a
    signal-based recompute can legitimately want to decay a globally-seminal
    paper the corpus has not yet linked; that call is Bryan's, not the pass's.
  - `|Δ|` that rounds to the same 2-decimal value → **no-op**: don't write, omit
    from `committed[]`, count only in `metrics.recomputed`. This keeps the pass
    idempotent.
  The recompute is a holistic judgment over the three signals
  (`importance-scoring.md`), not a formula; the ±0.3 boundary bounds the
  subjectivity by routing big moves to review.
- **Output.** Emit the fenced-yaml phase result (`rem-cycle-contract.md`) — not
  the health-report table. Populate `metrics` with the counts the health delta
  needs: for `hygiene`, `orphans` / `dead_links` / `pending_stubs` /
  `unknown_status` / fixes applied; for
  `importance`, `recomputed` / `moved_up` / `moved_down` / `swings_over_0.3` /
  `max_abs_delta` (a distribution, not a bare mean — an up/down wash hides in a
  mean). No `cursor` (this phase is not cursor-driven).
- **No chaining.** The orchestrator owns phase composition — do **not** spawn
  `frontmatter-guard`, `citation-fixer`, or `restructure-thin-page` here.
  Surface their bug classes in `proposed[]` and let the orchestrator route them.

## Anti-patterns

- Marking a dimension clean without actually scanning it.
- In phase mode: running dimensions outside the requested `scope`, chaining into
  another skill, or emitting the health-report table instead of the phase result.
- Editing a page without reading it in full first.
- Deleting an orphan page instead of checking whether it just needs a link.
- Deleting any page without confirmation.
- Batch-fixing missing links without verifying each relationship is real.
- Hand-writing a backlinks section — inbound edges are derived.
- Merging two tags that do not actually mean the same thing.
