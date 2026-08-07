---
name: grant-ingest
description: Ingest a grant — a whole application package, in any format — distill it against grant structure, preserve your human's verbatim prose, annotate it with reviewer critiques, and file it as one grant page wired into the research graph.
triggers:
  - "ingest this grant"
  - "process this grant"
  - a grant document or application package in _drop/
  - a summary statement or reviewer critique to attach to a grant
---

# Grant ingest — distill a grant application package

Turn a grant — a funded or unfunded application, a renewal, a resubmission —
into one `grant` page that is distilled against grant structure *and* carries
your human's verbatim prose intact. A grant is the richest source the brain ingests:
an explicit statement of the lab's current research direction, often holding
bleeding-edge preliminary data that has not been published anywhere else. It
earns the highest care, the most detail, and the one deliberate exception to
distill-don't-dump.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/quality.md` (citations, the notability gate, and especially
> *verbatim where the wording is the information*),
> `skills/conventions/brain-first.md` (check the brain first),
> `skills/conventions/frontmatter.md` (the `grant` schema),
> `skills/conventions/raw-source-archive.md` (the R2 archive and multi-document
> `sources:`), `skills/conventions/graph-and-links.md` (the edge forms),
> `skills/conventions/test-before-bulk.md` (a backlog of historical grants),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `raw-source-archive-upload`
(the application package — research strategy, summary statement, etc.),
`user-model-query` (your human's blind spots inform what the analysis section
should call out). Does **not** delegate paper-ingest inline; instead,
sets `needs-ingest: true` on cited paper stubs for `ingest-pending-papers`
to drain later (the producer/consumer split).

## Why verbatim, here

Every other ingest skill distills and discards the source text. This one keeps
it. Two reasons. A grant is your human's own writing, and `skills/conventions/quality.md`
forbids paraphrasing his prose — his voice is a source the brain learns from,
and paraphrase destroys it. And the future grant-writing skills (`RESOLVER.md`,
deferred) learn that voice from exactly this corpus. The grant page therefore
carries both: the mind's distilled analysis *and* the preserved verbatim, in
clearly separated sections doing different jobs.

## What this guarantees

- A grant package becomes **one** `grant` page — distilled against grant
  structure, never one page per package document.
- The verbatim science prose — Specific Aims, Research Strategy, Project
  Narrative — is preserved on the page, intact, alongside the analysis.
- Reviewer critiques are annotated against the exact passages they targeted.
- Every package document is archived to R2; each is a `sources:` entry tagged
  with its `role:`. No binary enters git.
- Preliminary data propagates to `concept` and `method` pages as evidence.
- Key citations get stub `paper` pages (or `cited_by` edges on existing pages)
  — never inline `paper-ingest` runs. Distillation is deferred to
  `ingest-pending-papers`. Fact-sourcing citations are dropped, not paged.
- Images are discarded; figure captions are kept.

## Reached from the router

`grant-ingest` is a specialization of `ingest`, parallel to `paper-ingest`. The
`ingest` router sends a grant document or package here. It is *not* the
grant-writing cluster (deferred) — it is the input side that feeds it.

## A grant is a package

A grant ingest takes a **bundle of documents**, not a file: Specific Aims,
Research Strategy, Project Narrative / Summary, budget, budget justification,
biosketches, and — for a resubmission or an awarded grant — the summary
statement or reviewer critiques. Foundation grants vary widely from the rigid
NIH package, so this skill stays **non-rigid**: a package is whatever documents
your human dropped for one grant, and each document is classified by its *evident
role*, never against a required checklist. Roles seen so far:

`specific-aims`, `research-strategy`, `project-narrative`, `project-summary`,
`budget`, `budget-justification`, `biosketch`, `bibliography`,
`summary-statement`, `reviewer-critique`, `other`.

## Phases

1. **Group the package and confirm.** Detect which dropped documents belong to
   one grant — shared title, PI, agency, aims. Classify each by role. A summary
   statement or critique is paired to its grant by matching project title and
   agency. Then confirm the grouping *and* the primary project(s) with your human
   via `skills/ask-user/SKILL.md` before writing — grants touch several projects
   and the wrong call is expensive to unwind.

2. **Receive the extracted text.** Hermes extracts document text — do not shell
   out to pandoc, ImageMagick, or any converter. Images are discarded: no
   extraction, no format normalization, no asset directory. Two carve-outs,
   because a grant's preliminary data often lives in a figure: keep every
   **figure caption verbatim**, and where the prose had a figure leave a marker
   — `[Figure N — image omitted; original in R2]`. The analysis may describe a
   figure's content when a preliminary-data claim depends on it and the caption
   is thin; use Hermes vision on the R2 original, sparingly.

   **`.docx` carve-out — figure captions live in textboxes, not paragraphs.**
   In NIH-style grants authored in Word, figure captions are commonly placed
   in *floating textboxes* (`<w:txbxContent>` in the OOXML), and a naive
   `Document(path).paragraphs` walk through `python-docx` will **silently
   miss every caption** even when the body text is fully recovered. Always
   iterate `doc.element.body.iter('{...wordprocessingml...}txbxContent')` and
   harvest `<w:t>` text from each, deduplicating (mc:Choice/Fallback
   duplicates are common). Insert each recovered caption block as
   `[Figure N — image omitted; original in R2]\n*<caption>*` placed after the
   first paragraph in the body text that references `Fig N` / `Figure N`.

   **Re-ingest from R2.** If `_drop/` is empty but originals exist on R2
   (a re-ingest, or someone else already cleared `_drop/`), pull them back
   via `rclone copyto <instance>-r2:<instance>-drops/<r2_key> /tmp/<workdir>/`
   using each `sources[].r2_key` from the existing page's frontmatter. If
   `rclone listremotes` returns empty, the agent's HOME is shimmed — export
   `RCLONE_CONFIG=/Users/<user>/.config/rclone/rclone.conf` once. See
   `skills/conventions/raw-source-archive.md` "Watch the agent's HOME" pitfall.

3. **Brain-first dedup.** Run `brain-search` for an existing `grant`
   page — a grant may already be stubbed as planned, or this may be a
   resubmission of a scored application. Page exists → UPDATE: add the delta,
   never blind-overwrite. No page → CREATE.

   **Dedup pitfall — the qmd index lags fresh writes.** The hybrid search may
   miss a `grant` page that was filed in the same session (or by a parallel
   ingest attempt earlier in the same conversation) because the page is not
   yet indexed. **Also do a filesystem grep before writing**:
   `search_files target=content pattern="<grant-number>"` (e.g.
   `R21AI000000`) across `grants/`, `projects/`, `RESEARCH.md`,
   `people/`, and `institutions/`. If a near-identical page exists,
   consolidate: keep the most complete one (verbatim section closest to
   100% of source bytes; per-passage critique pairings present), delete
   the others, and fix backlinks in `RESEARCH.md`, `people/*`, and
   `institutions/*` to point at the surviving slug.

4. **Distill against grant structure.** Write the analysis sections — project
   summary, Specific Aims, Significance & Innovation, Preliminary Data (each
   result tied to its figure or caption), Approach, Future Directions. This is
   The mind's own read, in its normal voice — distilled, cited, connected.

5. **Synthesize the review** (if a summary statement or critiques are present).
   Pull the impact score, criterion scores, percentile, and outcome into the
   `## Review` section and the frontmatter. Paraphrase the critique themes —
   strengths and weaknesses across reviewers — and separate out the concerns
   that are actionable for a resubmission. Reserve verbatim critique text for
   the short quotes used in the annotation callouts (phase 6).

6. **Assemble the verbatim section.** After the analysis, reproduce the science
   prose — Specific Aims, Research Strategy, Project Narrative — verbatim and
   intact, with figure captions kept and figures marked omitted. Interleave
   reviewer critiques as `> [!critique]` callouts placed against the exact
   passage each one targeted. This passage-to-critique pairing is high-value
   evidence about what study sections punished (`DESIGN.md` §7.3).

7. **Propagate into the graph.**
   - **Specific Aims → `project` pages.** Each project the grant touches gets
     the grant linked and its proposed directions noted.
   - **Preliminary data → `concept` and `method` pages.** A validated result
     gets a `> [!note] Preliminary data — [[grants/<slug>]]` callout on the
     relevant concept page; technique-feasibility data goes on the `method`
     page. Bump `updated:`. Do **not** create `hypothesis` pages — hypotheses
     are derived from brainstorming and literature review, not restated from a
     grant. An edge to an *existing* hypothesis is fine; a new one is not.
   - **Methods and concepts** the grant uses or introduces → `method` /
     `concept` pages, created or updated.
   - **Key citations → stub `paper` pages (do not run `paper-ingest` here).**
     See Phase 8 for the full procedure. The grant page gets a `## Key
     citations` section; each cited paper gets a stub page or an updated
     `cited_by` edge. Full distillation is deferred to
     `skills/ingest-pending-papers/SKILL.md`, which runs in a fresh session.
   - **Funder → `institution`; program officers → `person`** (notability-gated)
     → chain to `skills/enrich/SKILL.md`.
   - **Key Personnel → `person` pages.** Enumerate the PI, every
     co-investigator, and every key collaborator listed on the grant. For
     each: if a `person` page exists, append `grants/<slug>` to its `links:`;
     if not, create one via `skills/enrich/SKILL.md`. Person slugs are
     `<surname-firstname>` (e.g. `people/doe-jane`,
     `people/de-carvalho-renan` — particles stay with the surname token), per
     `skills/conventions/page-kinds.md`. Never `<firstname-surname>`; the brain
     keys back-links on the citation form, which leads with surname — a grant
     doc's "Firstname Lastname" personnel list is "Given Family" order, so the
     **last** token is the surname (`page-kinds.md` "Deriving the slug"). Set
     `role:` (PI | co-PI | co-I | consultant) and `affiliation:` from the
     biosketch — do not guess affiliations from prose. Then add every
     personnel slug to the grant page's own `links:` block, so the typed
     edge is symmetric. A grant whose co-Is were silently skipped is a
     graph hole the cross-grant collaborator view depends on, and it is
     the failure mode this bullet exists to prevent (ENDURE R01AI000000,
     2026-05).

     **Where to find personnel — in priority order.** Body prose is the
     *last* place to look, not the first. The names live in structured
     documents in the package, and that is where they should be read from:

     1. **SF424 / facepage** — the official Key Personnel list if a
        facepage document was dropped. Names plus roles plus affiliations
        in one block.
     2. **Biosketch documents** — one per investigator on most NIH
        packages. Each is canonical for that person's name spelling,
        degree, and affiliation.
     3. **Personnel Justification** (sometimes in the budget justification
        document) — names with role percentages and an explicit statement
        of contribution.
     4. **Research Strategy prose** — only as a sanity check that the list
        from (1)–(3) is complete. A name that appears in the Approach
        narrative but is missing from the facepage and biosketches is
        worth confirming with your human before paging.

     If none of (1)–(3) are present in the dropped package — common for
     foundation grants and for re-ingests where only the science documents
     were preserved — stop and ask your human for the facepage or biosketches
     before guessing personnel from prose. A name mentioned in the
     Approach ("the Irvine lab has developed…") is not by itself
     sufficient evidence that the person is Key Personnel on this grant;
     they may be a method-source citation rather than a co-I.

8. **Key citations — stubs out, no inline paper-ingest.** This is the phase
   that used to chain to `paper-ingest`. It no longer does, for two reasons:
   running paper-ingest inline stacks an unbounded number of paper
   distillations on top of an already-large grant ingest (compaction risk —
   the dominant historical failure mode), and the right model for routine
   paper distillation is cheaper than the model needed for grant ingest. The
   producer/consumer split fixes both.

   **Identify key citations.** A key citation is a reference that introduces a
   core method, a foundational concept, or a dataset the grant builds on.
   Citations that merely source a fact or statistic are *dropped*, not paged.
   This is the same notability bar as before; only the downstream handling
   changes.

   **Find the full citation text.** Preferred source: a standalone
   `bibliography` document in the package, if one was dropped — it is the
   shortest text to re-read. Fallback: the references section of the
   `research-strategy` document. Extract the full citation entry (authors,
   year, title, venue, DOI if present) for each key citation. Do *not*
   parse the entire bibliography — only the key citations identified above.

   **A pitfall worth the named warning: `_with-refs.docx` may not actually
   contain references.** NIH grant packages often ship the research strategy
   in two flavors — one without references, one with — and the latter is
   named something like `<grant>_research_strategy_with-refs.docx`. The
   *filename* is a promise, not a guarantee. The references may live in
   `endnotes.xml`, in a separate paragraph block at the end of the body, or
   simply nowhere at all (some grants are submitted with references in a
   bibliography manager that never round-trips back into the docx). Before
   spending time reverse-engineering citation numbers from prose context,
   verify the references are actually parseable:

   ```python
   # Quick check after unzipping <doc>.docx:
   # - endnotes.xml non-trivial?
   # - last N body paragraphs match r'^\d{1,3}\.\s+[A-Z]'?
   ```

   If both checks fail, the references are not in the document. Stop and
   ask your human for a standalone bibliography file — it almost certainly
   exists as a separate doc in the original NIH submission. Drop it into
   `_drop/`, archive it to R2 with `role: bibliography`, and append the new
   `sources:` entry to the grant page frontmatter retroactively (use
   provenance like `"uploaded retroactively to support Phase 8 key-citation
   backfill, YYYY-MM-DD — the original research-strategy_with-refs.docx in
   the package did not contain a parseable references list"`).

   Do *not* try to recover citation entries by matching numbers in the
   verbatim prose against external CrossRef / PubMed lookups based on
   inferred context — that path is slow, error-prone, and the citation
   entries we'd write into the stubs `## Citation` sections would be
   guesses dressed up as fact. The seed text for `paper-ingest`'s identity
   resolution needs to be the real entry, not a reconstruction.

   **For each key citation, three cases:**

   - **Existing full paper page** (`needs-ingest` absent or `false`, no
     `stub` tag). Append `grants/<slug>` to its `cited_by` frontmatter list
     if not already present. Do not modify anything else on the page.

   - **Existing stub** (`needs-ingest: true` or `tags: [stub]`). Append
     `grants/<slug>` to `cited_by`. The flag is already set; the next run
     of `ingest-pending-papers` will pick it up.

   - **No existing page.** Create a new stub at `papers/<topical-slug>.md`
     with the page shape under "Stub paper page shape" below. The
     `needs-ingest: true` flag is set unconditionally — the grant rule.

   **Brain-first dedup before creating a stub.** Search `papers/` by title,
   author surnames, and DOI (if the citation entry carries one) before
   creating a new stub. A stub may already exist from a prior grant's
   ingest, or a full page may exist that the qmd index hasn't yet surfaced.
   Use both qmd hybrid search *and* `search_files target=content` against
   `papers/` — the same dedup pitfall documented in Phase 3 applies here.

   **Update the grant page.** Add a `## Key citations` section with one
   bullet per key citation in the shape under "Page shape" below.

9. **Connect to the research program.** Read `RESEARCH.md` for the active
   threads and funding context. The analysis must say where this grant lands —
   what it advances, what it proposes that other grants also propose, what it
   opens. Cross-*grant* synthesis is deliberately **not** done here: it belongs
   to `skills/concept-synthesis/SKILL.md`, run after a batch of grants is in,
   so the first grants ingested are not at a synthesis disadvantage.

10. **Archive the package.** Every package document goes through the `_drop/` →
    R2 pipeline; the binary never enters git. The grant page carries one
    `sources:` entry per document, each tagged with its `role:`
    (`skills/conventions/raw-source-archive.md`).

11. **Verify the verbatim — mandatory, mechanical, after writing.** Before
    declaring the ingest complete, byte-check each `### <doc> (verbatim)`
    block on the written page against the extracted source text it came from.
    For each science document with a verbatim subsection (Project Summary,
    Project Narrative, Specific Aims, Research Strategy, and any other
    document carried verbatim), measure the length of the preserved block
    *excluding* the leading `> [Source: …]` line and excluding inserted
    figure-caption blocks (`[Figure N — image omitted; …]` plus the italic
    caption line) and any interleaved `> [!critique]` callouts. Compare to
    the byte count of the extracted source.

    **Fail loudly if any block is below 95% of source bytes.** A short block
    is the dominant failure mode this skill has hit in practice — usually
    triggered by a mid-task context compaction that replaces the held source
    text with a summary, after which the writing step drafts from the
    summary and silently truncates. The block being short is the signature;
    catch it mechanically here rather than discovering it later. If a block
    fails the check, do not patch over the gap from memory — re-extract from
    the R2 original and rewrite the block from the freshly held text, then
    re-check.

    The 95% floor allows for legitimate whitespace normalization but flags
    any real prose loss. A block at 100% of source bytes is the expected
    norm; anything below 95% is the *failure case*, not an edge case.

    Record the per-document byte counts (source vs. preserved) in the
    `## Drafting log` entry for the ingest so a future audit can spot
    silent regressions.

12. **Hand off to `ingest-pending-papers`.** As the closing line of the
    ingest, tell your human: "N stubs created, M existing pages updated. Run
    `ingest-pending-papers` in a fresh session to fill them in — optionally
    switch the TUI to a cheaper/faster model first; routine paper ingest
    doesn't need Opus." Do *not* invoke the worker.

Ingesting a backlog of historical submissions is expected. For more than a
handful, follow `skills/conventions/test-before-bulk.md`: ingest 3-5, read the output,
fix the approach, then run the rest in committed batches.

## Page shape

```markdown
---
kind: grant
slug: <slug>
title: "<grant title>"
funder: institutions/<slug>
mechanism: "R01"            # or the foundation program — free text, not an enum
role: PI                    # PI | co-PI | co-I | consultant
status: scored-not-funded   # full lifecycle enum in skills/conventions/frontmatter.md
score: 34                   # impact score, if reviewed — else omit
percentile: 22              # if scored — else omit
submitted: YYYY-MM-DD
decision_date: YYYY-MM-DD   # if reviewed — else omit
deadline: YYYY-MM-DD        # next actionable deadline — the attention contract reads this
importance: 0.0
links: [people/<pi-slug>, people/<co-i-slug>, projects/<slug>, methods/<slug>, concepts/<slug>]
tags: []
sources:
  - role: research-strategy
    hash: sha256-...
    r2_key: grants/....pdf
    filename: "..."
    ingested: YYYY-MM-DD
    provenance: "ingested grant package, YYYY-MM-DD"
  - role: summary-statement
    hash: sha256-...
    r2_key: grants/....pdf
    filename: "..."
    ingested: YYYY-MM-DD
    provenance: "ingested grant package, YYYY-MM-DD"
---

# <Title>

## Summary
The project summary, distilled — against what the brain already holds.

## Specific Aims
Each aim's goal, in the mind's words. The verbatim aims sit in `## Verbatim`.

## Significance & Innovation
What the grant claims is significant and new, distilled.

## Preliminary Data
Each preliminary result, tied to its figure or caption — and where it
propagated (which `concept` or `method` page).

## Approach
The key methods and experimental designs, linked to `method` / `concept` pages.

## Future Directions
Work the grant proposes beyond the current period.

## Review
Scores, percentile, outcome. Critique themes paraphrased. Actionable
resubmission concerns called out separately. Omit the section if unreviewed.

## Analysis
Where this lands on your human's active threads — what it advances, what it
contradicts, what it opens. What your human would not have noticed.

## Key citations
One bullet per key citation. Each bullet has three pieces: the wikilink to the
paper page (a stub or a full page), a one-line why-foundational, and the
verbatim citation entry as a blockquote child.

- [[papers/<slug>]] — <one-line why this is foundational to the grant>.
  > <Authors>. <Title>. <Venue>. <Year>;<volume>(<issue>):<pages>.
  > doi:<doi-if-present>

## Verbatim
your human's preserved prose — the corpus the grant-writing skills learn their voice
from. One subsection per science document, intact, figure captions kept.

### Specific Aims (verbatim)
> ...

### Research Strategy (verbatim)
> ...the prose, with critiques interleaved:
> [!critique] Reviewer 2 — Approach
> "Aim 3 is overambitious for the timeline." Recurs in R21-XXXXXX review.
```

## Stub paper page shape

A stub `paper` page is what `grant-ingest` writes for a key citation that
does not yet have a page. It is a valid `paper` page (`paper-ingest` will
fill it in via the UPDATE path), distinguished by `needs-ingest: true`,
`tags: [stub]`, and the minimal body.

```markdown
---
kind: paper
slug: <topical-slug>
title: "<full title from the citation entry>"
status: unknown            # paper-ingest fills this when it resolves DOI
needs-ingest: true         # grant rule — set unconditionally for grant-cited stubs
cited_by:
  - grants/<grant-slug>
authors: []                # paper-ingest fills these
venue: ""
year: null
importance: 0.0
tags: [stub]
sources: []                # no R2 source yet — paper-ingest pulls the PDF
---

# <Title from citation>

> [!info] Stub
> This page was created by `grant-ingest` as a key citation of
> [[grants/<grant-slug>]]. It will be filled in by `ingest-pending-papers`
> (or `paper-ingest` directly if you run that against this page manually).

## Citation

> <verbatim citation entry copied from the citing grant>
```

## Anti-patterns

- Shelling out to pandoc or ImageMagick — text extraction is Hermes's job.
- Extracting or normalizing figure images instead of discarding them; dropping
  the figure captions, which are text and carry the result.
- Paraphrasing the verbatim science prose — your human's grant voice is preserved
  intact or it is lost.
- Creating `hypothesis` pages from grant content — hypotheses derive from
  brainstorming and literature review, not grant restatement.
- Hand-maintaining cross-grant synthesis pages — that is `concept-synthesis`'s
  job, run after a batch of grants is in.
- Ingesting every cited reference — only key citations earn a stub, and even
  those are not distilled inline. Fact-sourcing citations are dropped.
- Running `paper-ingest` inline from grant-ingest — that is exactly the
  compaction-risk shape this skill split was designed to remove. Stubs out,
  worker drains them later.
- Splitting one grant package into several pages, or filing each package
  document separately.
- Committing a binary package document into git instead of archiving it to R2.
- Skipping the post-write byte-check on the verbatim blocks, or "patching
  over" a short block from memory instead of re-extracting from R2 and
  rewriting it.
- Filing a grant without enumerating its Key Personnel as `person` pages —
  the funder and the PO get this treatment, the co-Is must too. Read names
  from the facepage and biosketches, not from the Approach prose.
- Bulk-ingesting a backlog of historical grants without testing a few first.
