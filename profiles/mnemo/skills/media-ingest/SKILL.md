---
name: media-ingest
description: Ingest a video, podcast, book, code repo, or a non-paper PDF — distill it into a brain page filed by primary subject, link it forward, and chain into enrich for every notable entity it names. A scientific paper goes to paper-ingest instead.
triggers:
  - "watch this video"
  - "process this podcast"
  - '"ingest this PDF" (a non-paper PDF — a report, a slide deck)'
  - "summarize this book"
  - "check out this repo"
  - a video, podcast, book, repo, or non-paper PDF to ingest
---

# Media ingest — distill a video, podcast, PDF, book, or repo

Turn long-form media into a distilled brain page. The format is just the
container — what gets filed is the content, distilled.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/quality.md` (citations, forward-only linking, the notability
> gate), `skills/conventions/raw-source-archive.md` (the R2 archive),
> `skills/conventions/brain-first.md` (check the brain first),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url`,
`raw-source-archive-upload`, `voice-transcribe` (optional — for podcasts
and videos with no transcript provided). Under harnesses without
`voice-transcribe`, the audio-only path refuses cleanly; text-bearing
media (PDFs, repos, books) still work.

## What this guarantees

- Every media item becomes a page with analysis — never a transcript dump.
- The page is filed by primary subject, not by media format.
- Every notable person or institution it names is enriched.
- The raw original is archived to R2; the binary never enters git.

## Not for scientific papers

A scientific paper — peer-reviewed or preprint — is **not media**, even when it
arrives as a PDF. It has a DOI, a review status, and findings that wire into the
hypothesis graph. If what arrived is a paper, hand the whole job to
`skills/paper-ingest/SKILL.md`. This skill handles the non-paper PDF — a report,
a white paper, a slide deck — alongside video, podcast, book, and repo.

## Input handling

| Format | How the content arrives |
|---|---|
| Video / podcast | Transcription is a **Hermes capability** — you receive the transcript text. You do not run STT yourself. |
| PDF / book | Text extracted from the source; for a book, identify chapters or sections. A scientific-paper PDF goes to `paper-ingest`, not here. |
| Code repo | Read the README and the load-bearing files; reconstruct the architecture. |

## Phases

1. **Receive the content.** For audio or video, work from the transcript text
   Hermes provides. For a PDF, book, or repo, work from the extracted text or
   the repo contents.

2. **Check the brain first.** Use `brain-search` for existing coverage — the
   subject, the speakers, the methods named — before writing. Ingest adds the
   *delta* (`skills/conventions/brain-first.md`).

3. **Distill, do not dump.** A brain page is the analysis, the key claims, and
   the connections — never the raw transcript or a chapter-by-chapter retelling.
   Pull the load-bearing claims and number them.

4. **File by primary subject** (`_brain-filing-rules.md`). A talk about a method
   is a `method` page; a podcast on a framework is a `concept` page; a repo
   implementing a technique is a `method` page. The format never sets the kind.
   One source can distill into more than one page — file each facet under its
   kind and link them.

5. **Archive the raw original.** The video, audio, PDF, or book goes through the
   `_drop/` → R2 pipeline; the git pointer is recorded in the distilled page's
   `sources:` frontmatter (`skills/conventions/raw-source-archive.md`). The original is
   never a brain page.

6. **Link forward.** Add `[[kind/slug]]` wikilinks in prose and typed edges in
   frontmatter to every page this content connects to. Never hand-write
   backlinks — they are derived (`skills/conventions/graph-and-links.md`).

7. **Enrich notable entities.** For every person or institution the media names
   that passes the notability gate (`skills/conventions/quality.md`), chain into
   `skills/enrich/SKILL.md` — collaborators, students, postdocs, paper authors
   → `people/`; labs, universities, consortia, funders → `institutions/`. A
   media item is not fully ingested until its notable entities are enriched.

8. **Connect to the research program.** Read `RESEARCH.md` for the active
   threads and say where this content lands — what it advances, contradicts, or
   opens.

## Page shape

```markdown
---
kind: concept
slug: <slug>
title: "<title>"
importance: 0.0
links: [methods/<slug>, people/<slug>]
tags: []
sources:
  - hash: sha256-...
    r2_key: <kind>/....<ext>
    filename: "..."
    ingested: YYYY-MM-DD
    provenance: "ingested media, YYYY-MM-DD"
---

# <Title>

## Context
Why this matters, against what the brain already holds.

## Key claims
The load-bearing claims, each with a citation.

## Analysis
How this connects to Bryan's active threads. What is new. What it
contradicts.
```

## Anti-patterns

- Dumping a raw transcript instead of distilling it.
- Filing by format (all videos together) instead of by primary subject.
- Leaving a notable person or institution un-enriched "for later".
- Committing the binary original into git instead of archiving it to R2.
- Running STT yourself — transcription is a Hermes capability.
