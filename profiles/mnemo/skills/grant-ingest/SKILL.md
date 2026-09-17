---
name: grant-ingest
description: Ingest a grant — a whole application package, in any format — distill it against grant structure, preserve your human's verbatim prose, annotate it with reviewer critiques, and file it as one grant page wired into the research graph.
triggers:
  - "ingest this grant"
  - "process this grant"
  - a grant document or application package in _drop/
  - review material accompanying a new grant package or requiring first creation of its grant page
eval_contract:
  goal: Preserve and distill one grant package with source-verified verbatim prose, review annotations, graph propagation, and citation stubs.
  dimensions:
    - "PRESERVATION — science prose and captions survive source-to-page verification"
    - "IDENTITY — package grouping, personnel, and citation seeds come from actual documents"
    - "INTEGRATION — graph updates and queued key citations are complete and validated"
    - "ISOLATION — delegate package or paper work without accumulating unbounded extraction in one context"
  hard_fails:
    - Losing verbatim source prose or inventing missing citation/personnel information.
    - Losing source fidelity or overlapping shared writes when delegating package work.
    - Leaving a grant-selected below-threshold stub unqueued.
---

# Grant ingest — distill a grant application package

> **Git closeout:** Follow `skills/git-ops/SKILL.md`. A standalone owner closes one verified grant package, required graph propagation, and citation stubs after archival and verbatim checks. Paper fills remain a later operation. A nested ingest returns its paths and validation to the parent.

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

Delegate package extraction or independent grant sections when useful,
with explicit output ownership. Keep one coherent grant page and give shared
person/project updates one owner across concurrent workers. Verify preserved
prose and source evidence regardless of who performed the extraction.

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `raw-source-archive-upload`
(the application package — research strategy, summary statement, etc.),
`user-model-query` (your human's blind spots inform what the analysis section
should call out). Citation stubs are produced separately from paper extraction;
paper workers or `ingest-pending-papers` can process them once their inputs
are ready, without restarting the session.

## Why verbatim, here

Every other ingest skill distills and discards the source text. This one keeps
it. Two reasons. A grant is your human's own writing, and `skills/conventions/quality.md`
forbids paraphrasing his prose — his voice is a source the brain learns from,
and paraphrase destroys it. And the grant-writing skills (`grant-plan`,
`grant-section`, and their cluster) learn that voice from exactly this corpus. The grant page therefore
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
grant-writing cluster — it is the input side that feeds it. Review-only
material for an existing grant routes to `grant-review-synthesis`; this skill
owns new packages and first creation of a grant page.

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
   is thin; use Hermes vision on the R2 original, sparingly. Format-specific
   extraction rules (`.docx` textbox captions, `_with-refs.docx` reference
   verification, re-ingest from R2) live in
   `references/docx-and-reingest.md` — load it when the package contains
   `.docx` inputs or when `_drop/` is empty but originals exist on R2.
   For every format, check the actual source for complete prose, captions,
   bibliography and personnel evidence; a successful extraction or present
   section headers do not prove completeness. Retain source files until
   archival and source-to-page checks pass.

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
     `skills/ingest-pending-papers/SKILL.md` or assigned paper workers.
   - **Funder → `institution`; program officers → `person`** (notability-gated)
     → chain to `skills/enrich/SKILL.md`.
   - **Key Personnel → `person` pages.** Enumerate the PI, every
     co-investigator, and every key collaborator listed on the grant. For
     each: if a `person` page exists, append `grants/<slug>` to its `links:`;
     if not, create one via `skills/enrich/SKILL.md`. Person slugs are
     `<surname-firstname>` (e.g. `people/doe-jane`,
     `people/de-carvalho-renan` — particles stay with the surname token), per
     `skills/conventions/page-kinds.md`. Never `<firstname-surname>`; the brain
     uses the citation form, which leads with surname. Resolve family/given
     names from structured personnel evidence and the page-kind convention,
     preserving particles; do not reduce every family name to its last token.
     Confirm ambiguous names rather than guessing. Set
     `role:` (PI | co-PI | co-I | consultant) and `affiliation:` from the
     biosketch — do not guess affiliations from prose. Then add every
     personnel slug to the grant page's own `links:` block, so the typed
     edge is symmetric. A real ingest hit exactly this failure mode: a
     grant whose co-Is were silently skipped leaves a graph hole the
     cross-grant collaborator view depends on.

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

8. **Key citations — stubs and paper handoff.** Follow
   `skills/conventions/paper-stubs.md` for the shared shape, producer
   exceptions, citation provenance, and later drain. Prefer isolated paper
   workers so unbounded extraction does not accumulate inside the grant
   context. Follow the configured runtime without changing model pins.

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
   For `.docx` packages whose reference list may not be where the filename
   promises, apply the verification steps in `references/docx-and-reingest.md`
   before declaring references absent or requesting a missing bibliography.

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

   - **Existing stub or queued intermediate.** Append `grants/<slug>`
     to `cited_by`, retain original provenance, and set `needs-ingest: true`
     even if the stub was below threshold. The grant rule queues every key
     citation; false alone does not identify a completed paper.

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

    The 95% floor is a truncation screen, not proof of fidelity: different
    text can have identical byte length, and smaller omissions can pass.
    Compare the actual source paragraphs and their order, check each caption
    separately, and verify that source references/personnel evidence were not
    omitted by the extractor. Exclude inserted formatting consistently from
    the byte comparison; never excuse changed prose as normalization.
    For re-ingest, preserve prior Verbatim until the replacement is verified;
    the distilled Review is not the original summary statement.

    Record the per-document byte counts (source vs. preserved) in the
    `## Drafting log` entry for the ingest so a future audit can spot
    silent regressions.

12. **Hand off paper work.** Report the actual stubs created and existing
    pages updated. The parent may run `ingest-pending-papers` or dispatch
    paper workers immediately once their inputs are ready, or leave them
    for the scheduled drain. No session restart is required. If a worker
    cannot delegate further, return these follow-ups to its parent.

Ingesting a backlog of historical submissions is expected. For more than a
handful, follow `skills/conventions/test-before-bulk.md`: ingest 3-5, read the output,
fix the approach, then run the rest in committed batches.

Before declaring completion, run the platform linter on every owned changed
page (grant, people, projects, institutions, methods/concepts and citation
stubs). Use exact absolute `--paths` in a shared worktree; `--changed-since`
is suitable only when that range contains precisely this operation:

```bash
python3 <platform-repo>/core/tools/lint-frontmatter.py \
  --instance <brain> \
  --changed-since <rev-before-this-ingest>
```

Inspect the exit code and findings; fix owned failures before closeout.
Lint does not replace source-fidelity, archival or graph checks. Shared Git
ownership remains with `skills/git-ops/SKILL.md`.

## Page shape

Load `templates/grant-page.md` when writing the grant page; it owns the full
frontmatter spine, the analysis sections, the `## Key citations` bullet
shape, and the `## Verbatim` section layout with interleaved critique
callouts.

## Stub paper page shape

Load `skills/conventions/paper-stubs.md` when writing citation stubs; its
minimal paper shape is canonical. For a new grant-cited stub, use
`stub_source: grant-ingest`, `needs-ingest: true`, and the verified
`grants/<grant-slug>` citation in `cited_by`. Retain metadata available in
the source citation; unresolved fields stay unknown/null. Copy the real
citation entry into `## Citation` and name the citing grant in provenance.
An existing stub retains its original `stub_source`; append the grant's
provenance and queue it. Do not fabricate a PDF/archive pointer.

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
- Accumulating unnecessary paper extraction in the grant context instead
  of using independent paper workers for a substantial citation batch.
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
