---
name: voice-note-ingest
description: Ingest a voice memo — preserve Bryan's exact phrasing verbatim in a block-quoted transcript, then distill it into the right page kind and archive the audio to R2.
triggers:
  - "voice note"
  - "ingest this voice memo"
  - "save this audio note"
  - a voice memo received
---

# Voice-note ingest — capture a voice memo

Turn a voice memo into a brain page. The harness transcribes the audio (via
`voice-transcribe`) — you receive the transcript text. The verbatim transcript
is the primary source and is sacred; the analysis interprets it.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/quality.md` (citations, exact-phrasing preservation),
> `skills/conventions/raw-source-archive.md` (the R2 archive),
> `_output-rules.md` (exact-phrasing preservation),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

- **Required:** `brain-read`, `brain-write`, `voice-transcribe`,
  `raw-source-archive-upload`.
- **Hermes-only:** `voice-transcribe` — under harnesses that don't
  provide a transcription pipeline this skill refuses cleanly. The
  raw transcript can still be ingested via `idea-ingest` once an
  external tool produces the text.

## What this guarantees

- Bryan's exact words are preserved verbatim in a block-quoted transcript
  section — never paraphrased, never cleaned up.
- The content is filed by primary subject into the right page kind.
- The audio original is archived to R2; the binary never enters git.
- The analysis interprets; the transcript stays untouched.

## The transcript is sacred

Preserve Bryan's phrasing **verbatim** — every hesitation, every false start,
every offhand word. The unpolished, stream-of-consciousness phrasing carries
something a cleaned-up paraphrase loses; the language *is* the insight
(`_output-rules.md`).

- Keep: `"the masking ablation only helps if the drift is non-stationary, which I'm not sure we've actually shown"`
- Not: `Bryan questioned whether the masking ablation result holds`

The transcript section is the primary source. The Analysis section is where
interpretation lives — never edit the transcript to match the analysis.

## Phases

1. **Receive the transcript.** Hermes transcribes the audio and provides the
   transcript text. You do not run STT yourself.

2. **File by primary subject** — the decision tree, first match wins
   (`_brain-filing-rules.md`):
   - First-person thinking, a reflection, a reaction — **the common case** →
     `notes/<slug>.md`
   - A scientific principle or framework Bryan is articulating →
     `concepts/<slug>.md`
   - A testable claim worth tracking evidence on → `hypotheses/<slug>.md`
   - New information or an assessment of a person → `people/<slug>.md`
   - New information about an institution → `institutions/<slug>.md`

   If the memo covers more than one subject, file the primary page and
   forward-link to the others.

3. **Write the page.** Distill the memo into an Analysis section, and embed the
   verbatim transcript in a block-quoted section — see the shape below.

4. **Archive the audio.** The audio original goes through the `_drop/` → R2
   pipeline; the git pointer is recorded in the page's `sources:` frontmatter
   (`skills/conventions/raw-source-archive.md`). The binary never enters git.

5. **Link forward.** Add `[[kind/slug]]` wikilinks and typed frontmatter edges
   to every page the memo connects to. Never hand-write backlinks — they are
   derived (`skills/conventions/graph-and-links.md`).

This skill handles one voice note at a time; each is its own ingest cycle.

## Page shape

```markdown
---
kind: note
slug: <slug>
title: "<short descriptive title>"
importance: 0.0
links: [hypotheses/<slug>]
tags: [voice-note]
sources:
  - hash: sha256-...
    r2_key: notes/....ogg
    filename: "YYYY-MM-DD-<slug>.ogg"
    ingested: YYYY-MM-DD
    provenance: "voice memo, YYYY-MM-DD"
---

# <Title>

## Transcript

> Bryan's exact words, verbatim — every hesitation and false start
> preserved. This is the primary source. Do not edit it.

## Analysis

What this means, how it connects to the active research threads, what
question it opens — the interpretation, kept separate from the transcript.
```

**Example.** A voice memo where Bryan thinks aloud about whether a preferential
masking result generalizes files to `notes/` as first-person thinking; the
transcript is preserved verbatim, and the Analysis forward-links to
`[[methods/preferential-masking]]` and any hypothesis it bears on. If the memo
instead lays out a *testable* claim, it files to `hypotheses/` instead.

## Citation

Attribute the memo as a direct statement from Bryan — the highest-authority
source (`skills/conventions/quality.md`):

```
[Source: Bryan, voice memo, YYYY-MM-DD]
```

## Anti-patterns

- Paraphrasing or cleaning up the transcript — the exact words are the signal.
- Editing the transcript to agree with the Analysis.
- Filing a first-person reflection anywhere but `notes/`.
- Committing the audio original into git instead of archiving it to R2.
- Running STT yourself — transcription is a Hermes capability.
