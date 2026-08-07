---
name: ingest
description: Router for content ingestion. Detects the input type and delegates to the right specialist skill. Also the entry point for the _drop/ raw-source pipeline.
triggers:
  - "ingest this"
  - "save this to the brain"
  - "process this"
  - a file appears in _drop/
---

# Ingest — the routing layer

Ingestion turns raw material — a paper, a transcript, a link, a voice memo —
into distilled brain pages. This skill is the **router**: it identifies what
arrived and hands off to the specialist that knows how to distill it.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/quality.md` (citations, linking), `skills/conventions/raw-source-archive.md`
> (the `_drop/` pipeline), `skills/conventions/test-before-bulk.md` (batches),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

Router only — delegates to the specialists. Universal capabilities only
(`brain-read`, `spawn-subagent`). The specialists declare their own
capability dependencies; the `_drop/` pipeline entry point additionally
needs `schedule-job` (the cron poll) and `raw-source-archive-upload`.

## The two entry points

1. **Bryan hands you something directly** — a URL, a file, pasted text. Route it
   by type using the table below.
2. **A file appears in `_drop/`** — the raw-source ingest channel. Syncthing
   carries a PDF or DOCX dropped on a laptop to the host; from there it is
   ingested, the original is archived via `raw-source-archive-upload`, a git
   pointer is recorded, and the file is cleared from `_drop/`. The full
   pipeline is in `skills/conventions/raw-source-archive.md`. The harness does not
   provide a filesystem watcher, so `schedule-job` polls `_drop/` on a cadence
   — this skill is what that job runs.

## Routing table

| Input | Route to |
|---|---|
| A scientific paper — peer-reviewed or preprint, any format | `skills/paper-ingest/SKILL.md` |
| A grant — an application package, a summary statement, reviewer critiques | `skills/grant-ingest/SKILL.md` |
| A link, article, or written-out idea | `skills/idea-ingest/SKILL.md` |
| A video, podcast, book, code repo, or a non-paper PDF | `skills/media-ingest/SKILL.md` |
| A meeting or talk transcript | `skills/meeting-ingestion/SKILL.md` |
| A voice memo or audio note | `skills/voice-note-ingest/SKILL.md` |
| An email thread or work email sync | `skills/email-ingest/SKILL.md` |
| A new person or institution to track | `skills/enrich/SKILL.md` |

When the type is ambiguous, read the content far enough to classify it. When it
is genuinely mixed (a PDF that is really a meeting transcript), route by the
*primary* nature of the content, not its file extension.

A **scientific paper routes to `paper-ingest` whatever form it arrives in** — a
PDF, a bare DOI or PMID, a journal / bioRxiv / arXiv link. The paper row is
first in the table for that reason: a paper PDF is a paper, not media, and a
paper link is a paper, not a generic article.

A **grant routes to `grant-ingest` as a whole package** — Specific Aims,
Research Strategy, budget, summary statement, and the rest are one grant, one
page. Do not route the individual package documents separately.

## What every ingest specialist shares

The specialists differ in extraction; they share this discipline:

- **Distill, do not dump.** A brain page is a distillation — the analysis, the
  claims, the connections to existing pages. The raw text is not the page.
- **File by primary subject.** A paper introducing a method is a `method` page
  as much as a `paper` page; file each facet under its kind and link them
  (`_brain-filing-rules.md`).
- **Cite every claim** — or flag it `[needs-citation]` (`skills/conventions/quality.md`).
- **Link forward.** Wikilink the pages this content connects to; never
  hand-write backlinks (`skills/conventions/graph-and-links.md`).
- **Archive the raw source.** Non-markdown originals go to the raw-source archive
  (R2), and each distilled page carries the git pointer in its `sources:`
  frontmatter (`skills/conventions/raw-source-archive.md`). The original is never a
  brain page.
- **Chain into `enrich`.** Every notable person or institution the content names
  gets its page created or updated.
- **Never blind-overwrite.** Read a page's current state before writing; if it
  was edited very recently, append or hold.

## Batches

For more than a handful of items — a large `_drop/` backlog — follow
`skills/conventions/test-before-bulk.md`: ingest 3-5, read the output, fix the approach,
then run the rest in committed batches.

## Anti-patterns

- Dumping raw text into a page instead of distilling it.
- Filing by format (`all PDFs together`) instead of by subject.
- Leaving a notable person or institution un-enriched "for later".
- Committing the binary original into git instead of archiving it to R2.
- Bulk-ingesting a backlog without testing a few first.
