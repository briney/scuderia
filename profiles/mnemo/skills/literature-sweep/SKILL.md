---
name: literature-sweep
description: Standing literature scan — daily new-publication sweep plus rotating brain-coverage gap analysis. Creates stubs (needs-ingest: true) for novel on-topic papers; a scheduled drain fills them. Lenient by design: prefer redundant stubs over missed load-bearing papers.
triggers:
  - "literature sweep"
  - "publication sweep"
  - "anything new in my fields"
  - "brain coverage gaps"
  - "what's missing from the brain"
  - a scheduled run (daily sweep + gap rotation)
---

# literature-sweep — standing scan + brain coverage audit

Two modes, one job: **Mode 1** catches new publications the brain doesn't
have yet; **Mode 2** audits existing concept pages for load-bearing papers
that were overlooked when the concept was built. Both modes write **stubs**
(`needs-ingest: true`) into `papers/` — the scheduled
`ingest-pending-papers` drain fills them. The sweep itself never performs
full ingestion.

**The lenient bar (Bryan's standing instruction, 2026-08-06):** prefer
ingesting some duplicative or redundant papers over missing something key
because it didn't pass an arbitrary importance filter. A redundant stub
costs one subagent round in the drain; a missed load-bearing paper costs a
permanent hole in the knowledge graph. When in doubt, stub.

> **Conventions:** `conventions/brain-first.md` (never stub what the brain
> already holds — check `papers/` by DOI first), `conventions/quality.md`
> (every stub lands with a resolvable DOI/PMID), `_brain-filing-rules.md`,
> `conventions/capabilities.md`.

## Capabilities

`brain-search`, `brain-read`, `brain-write` (stub pages only),
`fetch-url` (`pubmed-fetch`, `arxiv-fetch`, `biorxiv-fetch`),
`terminal` (Paperclip CLI for the semantic arm — optional, degrade
gracefully when absent).

## What this guarantees

- The interest profile is read from `RESEARCH.md` — no duplicated
  watchlist; the sweep never invents interests `RESEARCH.md` does not
  support.
- Nothing the brain already holds is re-stubbed (DOI-checked against
  `papers/` before any stub is written — stubs count as held).
- Every stub carries a resolvable identifier (DOI required; PMID when
  available) and provenance (`stub_source`, the query that found it).
- Stubs bypass the 5-citation threshold gate (set `needs-ingest: true`
  directly, like `grant-ingest`), per the lenient bar.
- Mode 2 rotates: every concept page is swept on a cycle, not just the
  high-importance ones. New papers found for a low-importance concept
  may be the reason its importance should rise — the rotation exists so
  prioritization never collapses onto the top tier.
- Silence is a real result. A day with no novel papers stubs nothing
  and says so.

## Mode 1 — new publications (daily)

**Goal:** papers published (or newly indexed) since the last sweep that
touch the research program, not yet in the brain.

1. **Build the profile.** Read `RESEARCH.md` — Active domains, Threads
   in flight, Publication pipeline. Turn each into concrete query terms
   plus key authors/labs to watch.

2. **Keyword arm (day-fresh sources).** PubMed E-utilities, arXiv API,
   bioRxiv API, windowed to the last 1–2 days. These sources are
   current; the window is precise.

3. **Semantic arm (Paperclip, monthly-indexed).** Paperclip updates its
   full-text corpus **monthly** (verified 2026-08-06: docs + SQL
   `created_at` is a bulk-load artifact, useless for delta detection).
   Use the pub-date window + brain-dedup to self-synchronize:

   ```bash
   paperclip search -s pmc,biorxiv,medrxiv --since 35d --sort date \
       "<domain query in plain language, with topic anchor>" -n 15
   ```

   Most days this returns papers already stubbed/ingested (dedup drops
   them, near-empty delta). Right after each monthly index update, the
   fresh month falls inside the window and the sweep catches the batch.
   Apply the `paperclip-search` skill's precision filters (topic anchor
   in the query, post-hoc title scan). If the `paperclip` binary or
   `PAPERCLIP_API_KEY` is absent, skip the semantic arm silently —
   keyword templates are always the default path.

4. **Dedup against the brain.** For each hit: extract the DOI; search
   `papers/` for it (`rg -l '<doi>' papers/`). Already present (full
   page OR stub) → drop. No DOI → drop (the lenient bar still requires
   a resolvable identifier).

5. **Stub the survivors.** For each novel on-topic hit, write
   `papers/<author>-<year>-<descriptive>.md` as a stub (see "Stub
   format" below). Then report.

## Mode 2 — brain coverage gaps (rotating, 3 concepts per run)

**Goal:** for concept pages already in the brain, find the load-bearing
papers that were overlooked when the concept was built — the gaps the
ebolavirus test drive proved exist (semantic search found 16 on-topic
papers missing from a concept that had been deliberately dived).

1. **Pick the rotation.** List `concepts/*.md` with their `last_swept:`
   frontmatter date. Select the 3 oldest — never-swept concepts first.
   Skip anything swept within the last **14 days**.

2. **Build queries per concept.** From the concept page: the title, the
   first sentence of the Thesis, and the frontmatter `tags:`. Compose
   1–2 plain-language semantic queries and 1–2 keyword queries that
   cover the concept's scope — including its named sub-mechanisms where
   the thesis mentions them (e.g., a lifecycle concept yields one query
   per major stage if the concept is broad).

3. **Search (no recency window).** Mode 2 is about completeness, not
   freshness — do not use `--since`. Run:

   ```bash
   paperclip search -s pmc,biorxiv,medrxiv "<concept query>" -n 15
   ```

   plus PubMed E-utilities keyword equivalents. For broad concepts,
   also consider `-s abstracts` for paywalled-journal recall (expect
   more noise; apply the precision filter).

4. **Classify against the concept.** First, parse the results
   **per entry block**, not with global regexes (trial lesson
   2026-08-06): each numbered result is a block of title line → id line
   → URL line; extracting DOIs and titles with separate list-regexes
   misaligns them whenever some entries carry PMC URLs instead of
   doi.org links, producing stubs with the wrong title↔DOI pairing —
   the same wrong-seed failure class the drain's Phase 2.5 validation
   exists to catch. PMCID URLs (`ncbi.nlm.nih.gov/pmc/articles/PMC\d+`)
   are acceptable identifiers when no DOI is shown — the drain resolves
   them. Then, for each hit, three-way triage
   (mirrors literature-dive tiering, applied leniently):
   - **Load-bearing / supplementary for THIS concept** + not in the
     brain → stub it. Record the concept in the stub's `links:` and the
     provenance note.
   - **Already in the brain** → drop silently. If the paper exists but
     is NOT linked from the concept page and clearly should be, add the
     forward link on the concept page (cheap graph repair; do not
     re-stub).
   - **Off-topic analog** (different virus family, different method,
     semantic neighbor only) → drop. When genuinely uncertain whether
     it's load-bearing, stub it — the lenient bar resolves ties toward
     inclusion, and the drain's distillation is where marginal calls
     get cheaply discarded.

5. **Update `last_swept`.** Set `last_swept: <today>` in each swept
   concept's frontmatter. This is the rotation cursor — never rewrite
   anything else in the frontmatter for this purpose.

6. **Report.** Per concept: hits reviewed, already-held, gaps stubbed,
   links repaired. Note any concept whose gap yield suggests its
   `importance` should be reconsidered — flag it in the report; do not
   change importance yourself.

## Stub format

Stubs follow the paper-kind frontmatter schema
(`conventions/frontmatter.md`) with the sweep additions shown:

```markdown
---
kind: paper
slug: <author>-<year>-<descriptive>
title: "<title>"
authors: []                # filled by the drain's paper-ingest
doi: <doi>
pmid: <pmid or omit>
needs-ingest: true
cited_by: []
stub_source: literature-sweep
tags: [stub]
links:
  - concepts/<concept>     # Mode 2 only — the concept this was found for
---

## Citation

<one-line citation as resolved: FirstAuthor et al., Journal Year. DOI.>

## Sweep provenance

Found by literature-sweep {mode} on {date}.
Query: "<the exact query that surfaced this paper>"
{Mode 1: matched domain/thread from RESEARCH.md}
{Mode 2: load-bearing or supplementary for [[concepts/<concept>]]}
```

The `links:` entry and provenance note are how the drain (and Bryan)
know why the stub exists. `cited_by` stays empty — citation edges
accumulate from real citing papers later.

## Output

Returned to the caller (the scheduled job delivers it; a direct request
gets it as text):

```
LITERATURE SWEEP — {date}

Mode 1 — new publications:
  - {title} — {first author}, {year}
    {domain/thread matched} | stubbed: papers/{slug} {or: already held}
    {DOI} {(semantic) if found only by the semantic arm}

Mode 2 — coverage gaps (concepts swept: {list}):
  {concept}:
  - {title} — {first author}, {year}
    {why load-bearing} | stubbed: papers/{slug} {or: linked (was in brain)}
    {DOI}

Summary: {N} stubs created, {M} already-held dropped, {K} links repaired
```

Flag standout papers worth immediate attention ("→ worth reading now")
rather than relying on the drain's queue order.

## Anti-patterns

- **Sweeping without reading `RESEARCH.md`** — a profile-less sweep is
  a noise generator.
- **Stubbing without the DOI brain-check.** Stubs live in `papers/`;
  re-stubbing a held DOI (full page OR existing stub) creates
  duplicates the drain will have to reconcile.
- **Filtering to a shortlist instead of stubbing.** The old sweep was
  read-only; this one stubs. The lenient bar is the standing
  instruction — do not reintroduce importance gating the drain doesn't
  apply.
- **Re-sweeping concepts inside the 14-day window.** The rotation
  exists so every concept gets coverage; camping on high-importance
  concepts starves the rest.
- **Applying `--since` in Mode 2.** Gap analysis is about completeness;
  a recency window recreates the hole Mode 2 exists to fill.
- **Treating semantic-arm output as trusted.** Apply the
  `paperclip-search` precision filters; off-topic analogs (other virus
  families, adjacent methods) are expected at ~30% without a topic
  anchor.
- **Full-ingesting in the sweep.** The sweep writes stubs. Ingestion —
  with Phase 2.5 identifier validation and delegation — is the drain's
  job. Do not collapse the producer/consumer split because the queue
  looks short.
