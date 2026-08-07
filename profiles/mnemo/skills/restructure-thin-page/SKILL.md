---
name: restructure-thin-page
description: Restructure a thin brain page — a pasted abstract, a stub, a raw-text dump — into a structured, useful page with an executive summary, why-it-matters, verbatim quotes, real insights, and forward links. Operates on any page kind; distinct from `enrich`, which is specifically for people and institutions.
triggers:
  - "restructure this page"
  - "restructure this stub"
  - "this brain page is a dump"
  - "make this page useful"
  - "batch restructure pages"
  - "restructure pass"
---

# Restructure thin page — from thin page to useful page

Take a brain page that is not yet pulling its weight — a `paper` page that is
just a pasted abstract, a `concept` stub, a raw-text dump under a `## Content`
header — and rewrite it as a structured, durable page.

> **Conventions:** `conventions/quality.md` (citations, forward linking,
> verbatim preservation), `conventions/graph-and-links.md` (the edge forms),
> `_brain-filing-rules.md` (file by subject), `_output-rules.md` (no slop),
> `conventions/test-before-bulk.md` (batches),
> `conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-read`, `brain-write`, `fetch-url` (when the page references a
source that needs to be re-fetched to verify a quote or claim).

## What a structured page has

- **Executive summary** — 2–3 sentences, the one thing worth remembering.
- **Why it matters** — ties the page to Bryan's *actual* research threads. Read
  the brain and `RESEARCH.md` for thread context; this section is never generic.
  If you cannot tie it to a real thread, drop the section — do not invent one.
- **Quotable lines** — 3–5 *verbatim* lines worth referencing later. Literal
  quotes, never paraphrase.
- **Key insights** — 3+ real insights: things the source says that were not
  already obvious. Not topic labels.
- **See also** — forward `[[kind/slug]]` wikilinks to the pages this one
  connects to.

## When to invoke

- A page lands thin via an ingest skill, carrying `needs-enrichment: true` in
  frontmatter.
- An existing page is a wall of raw text with no synthesis.
- Bryan says a page is useless, boring, or a dump.

## The pipeline

1. **Read.** Open the page; parse frontmatter and body. Note its `kind` — the
   restructure must respect the kind's schema (`conventions/frontmatter.md`).
2. **Scan.** Confirm it is thin — a raw `## Content` dump, a bare abstract, no
   synthesis. If `needs-enrichment` is already absent or false and the page is
   structured, skip it (idempotency).
3. **Ground.** Search the brain for the page's key entities and read
   `RESEARCH.md` so "Why it matters" rests on real threads, not assumptions.
4. **Restructure.** Rewrite the body into the structured sections above. Keep
   every verbatim quote exact. Cite every substantive claim or flag it
   `[needs-citation]` (`conventions/quality.md`).
5. **Link forward.** Add `[[kind/slug]]` wikilinks in prose and a "See also"
   block; add typed edges in frontmatter where the relationship is queryable
   (`cites:`, `links:`). Never hand-write backlinks — they are derived.
6. **Clear the marker.** Remove `needs-enrichment` from frontmatter (or set it
   false) so the page is not re-enriched.

## On the raw source

The raw text being restructured is *replaced*, not preserved inline. A brain
page is a distillation; the primary-source original lives in the raw-source
archive (R2), and the page carries a `sources:` pointer to it
(`conventions/raw-source-archive.md`). Do not wrap the raw dump in an inline
`<details>` block.

## Links — forward wikilinks

Intra-brain edges are `[[kind/slug]]` **wikilinks** — the Obsidian-native form
(`conventions/graph-and-links.md`). Use them freely in prose and in "See also".
A link to a page that does not exist yet is fine; it marks an edge worth filling.

## Quality bar

An enriched page passes if it has:

- An executive summary, 2–3 sentences.
- 3+ verbatim quotable lines — literal, not paraphrased.
- 3+ key insights that are genuine insights, not topic labels.
- A "Why it matters" tied to a specific brain thread, or no such section.
- A "See also" of forward `[[kind/slug]]` wikilinks.
- No `needs-enrichment` marker left in frontmatter.

## Batches

For an enrichment sweep over many pages, follow `conventions/test-before-bulk.md`:
restructure 3–5, read the output, fix the approach, then run the rest in
committed batches. Model routing for the pass is Hermes's call — this skill does
not select a model.

## Anti-patterns

- Paraphrasing a quote. A quote is verbatim or it is not a quote.
- A generic "Why it matters" ("this is important because innovation"). Tie it to
  a real thread or cut it.
- Inventing topic labels and calling them insights.
- Using markdown-path links instead of `[[wikilinks]]` for intra-brain edges.
- Wrapping the raw source inline instead of letting the archive hold it.
- Re-enriching a page that is already structured — check `needs-enrichment`.
- Hand-writing a backlinks section.
