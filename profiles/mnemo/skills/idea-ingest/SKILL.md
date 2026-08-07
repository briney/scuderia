---
name: idea-ingest
description: Ingest a shared link, article, or written-out idea — fetch the content, distill it into a brain page filed by primary subject, link it forward, and connect it to Bryan's active research threads.
triggers:
  - shares a link or URL
  - "read this"
  - "save this"
  - "think about this"
  - a written-out idea pasted into the conversation
---

# Idea ingest — distill a link, article, or idea

Turn a shared link, an article, or a written-out idea into a distilled brain
page. The job is not to summarize — it is to distill the content and connect it
to Bryan's research program.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/quality.md` (citations, forward-only linking, the notability
> gate), `skills/conventions/raw-source-archive.md` (the R2 archive),
> `skills/conventions/brain-first.md` (check the brain first),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url`,
`raw-source-archive-upload` (when a binary original is in hand).
`brain-search` optional.

## What this guarantees

- Every ingested item becomes a page with genuine analysis, not a summary.
- The page is filed by primary subject and forward-linked into the graph.
- Every claim carries an inline citation or a `[needs-citation]` flag.
- The analysis connects the content to Bryan's active research threads.
- A non-markdown original is archived to R2; the binary never enters git.

## Phases

1. **Fetch the content.** Use `fetch` against the URL — an article, a blog
   post, an open-API record. For a written-out idea pasted directly, the text
   *is* the content; skip the fetch.

   **If it turns out to be a scientific paper** — a peer-reviewed article or a
   bioRxiv/arXiv/medRxiv preprint — stop and hand the whole job to
   `skills/paper-ingest/SKILL.md`. Paper ingestion has its own home; this skill
   does not file `paper` pages.

2. **Check the brain first.** Use `brain-search` for existing coverage before
   writing — the subject, the authors, the methods it names. Ingest adds the
   *delta*; it does not duplicate a page that already exists
   (`skills/conventions/brain-first.md`).

3. **File by primary subject** (`_brain-filing-rules.md`). The format it
   arrived in is irrelevant — the subject sets the kind:
   - A scientific paper (peer-reviewed or preprint) → not filed here; hand to
     `skills/paper-ingest/SKILL.md` (see phase 1)
   - An experimental or computational technique → `methods/<slug>.md`
   - A scientific principle or framework → `concepts/<slug>.md`
   - A testable claim worth tracking evidence on → `hypotheses/<slug>.md`
   - Bryan's own first-person reaction or reflection → `notes/<slug>.md`

   One source can distill into more than one page (a paper that introduces a
   method *and* supports a hypothesis) — file each facet under its kind and link
   them.

4. **Archive a non-markdown original.** If the source is a PDF or other binary,
   route it through the `_drop/` → R2 pipeline and record the git pointer in the
   page's `sources:` frontmatter (`skills/conventions/raw-source-archive.md`). The
   original is never a brain page.

5. **Link forward.** Add `[[kind/slug]]` wikilinks in the prose and typed edges
   in frontmatter (`cites:`, `supports:`, `refutes:`, `links:`) to every entity
   the content connects to. Never hand-write backlinks — they are derived
   (`skills/conventions/graph-and-links.md`).

6. **Enrich notable people and institutions.** An author gets a `person` page
   *only if* their work is notable or recurring in Bryan's field — apply the
   notability gate (`skills/conventions/quality.md`); it is not unconditional. The same
   gate governs labs, universities, consortia, and funders. Chain into
   `skills/enrich/SKILL.md` for each entity that passes the gate.

7. **Connect to the research program.** Read `RESEARCH.md` for the active
   threads. The analysis must say where this content lands: does it advance a
   thread in flight, contradict a brain page, or open a question? Tell Bryan
   what he would not have noticed — not what the article says.

## Page shape

A scientific paper hands off to `paper-ingest` (phase 1) and never appears
here. Every other distillation lands in one of `method | concept | hypothesis
| note`. Example shape, for a `concept` distilled from an article:

```markdown
---
kind: concept
slug: <slug>
title: "<title>"
importance: 0.0
links: [papers/<slug>, methods/<slug>]
tags: []
sources:
  - hash: sha256-...
    r2_key: media/....pdf
    filename: "..."
    ingested: YYYY-MM-DD
    provenance: "shared link, YYYY-MM-DD"
---

# <Title>

## Context
Why this matters now, against what the brain already holds.

## Key claims
The specific findings, numbers, and arguments — each with a citation.

## Analysis
How this connects to Bryan's active threads. What is new. What it
contradicts. What question it opens.
```

A `method`, `hypothesis`, or `note` follows the same shape with the
corresponding `kind:` and the per-kind fields documented in
`skills/conventions/frontmatter.md`. `sources:` is the R2 pointer per
`skills/conventions/raw-source-archive.md`; the `r2_key` prefix reflects the source
format (`media/` for podcasts/videos/non-paper PDFs, etc.) — see the
archive convention.

## Anti-patterns

- Summarizing without connecting the content to the research program.
- Filing by format instead of by primary subject.
- Creating a `person` page for every author mentioned. For paper
  authors, the ledger (`skills/conventions/author-ledger.md`) is the
  staging area until the citation threshold fires; do not
  short-circuit it from here.
- Writing a claim with neither a citation nor a `[needs-citation]` flag.
- Committing a binary original into git instead of archiving it to R2.
- Blind-overwriting a page that already covers the subject.
