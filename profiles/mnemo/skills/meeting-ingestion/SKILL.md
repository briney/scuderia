---
name: meeting-ingestion
description: Ingest a meeting or talk transcript into a meeting page — extract attendees, decisions, action items, and topics, then enrich every notable attendee and institution.
triggers:
  - "process this meeting"
  - "meeting transcript"
  - "meeting notes"
  - a meeting or talk transcript received
eval_contract:
  goal: Distill meeting sources into a verified interaction page with required entity links and warranted action items.
  dimensions:
  - SOURCE — summary-first distillation retains transcript checks and explicit source limits
  - CONTENT — attendees, decisions, owners, and deadlines are source-grounded
  - GRAPH — notable entities and warranted tasks are linked without duplicates
  - PRESERVATION — available originals and supplied archive metadata are retained
  hard_fails:
  - Inventing a decision, attendee identity, deadline, or quote.
  - Claiming complete ingestion without required enrichment or source verification.
---

# Meeting ingestion — distill a meeting transcript

Turn a meeting or talk transcript into an `interaction` page in `interactions/`. The job
is to extract the structure that matters — who, what was decided, what is owed —
and to wire the meeting into the graph.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/quality.md` (citations, forward-only linking, the notability
> gate), `skills/conventions/graph-and-links.md` (the edge forms),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`. Optional:
`raw-source-archive-upload` (when the source recording or original
transcript document is in hand).

## Source hierarchy: summary-first

This skill owns source use for meeting distillation; source adapters supply
labeled material rather than redefining the hierarchy.

- **Summary available:** use it as the starting input for structured notes.
  Check the transcript for exact quotations, ambiguous decisions, owners,
  deadlines, or details the summary may have omitted. A summary is not
  evidence that an exact phrase was spoken. If a check exposes disagreement,
  use the relevant transcript passage and flag any remaining uncertainty.
- **Long transcript:** retain summary-first reading; retrieve relevant
  passages for verification rather than loading the entire transcript at
  once. Length does not make the transcript unusable. Archive the available
  raw transcript under `skills/conventions/raw-source-archive.md` even when
  the summary supplies most of the distillation.
- **No summary:** distill from the transcript, reading it in chunks if needed;
  label the result transcript-only. Do not invent a summary or omit later
  portions of the meeting because the first extraction was truncated.
- **No transcript:** use the available notes, label their provenance, and
  state that transcript verification was unavailable. If neither source has
  substantive content, report the missing source rather than writing a page.

For Granola retrieval, batching limits, and archive transport, load
`skills/granola-meeting-sync/SKILL.md` only when those adapter operations are
needed. For a supplied source bundle, preserve its provided identity and
archive metadata; do not repeat a verified upload. Resolve missing content
through the adapter before distilling.

For a batch, delegate independent meeting distillations when useful. Resolve
recurring attendees across the batch before creating person pages; give
shared entity/task updates one owner and verify the returned pages.

## What this guarantees

- Every meeting becomes an `interaction` page with participants, decisions,
  action items, and topics discussed.
- Every notable attendee and institution is enriched.
- The meeting page forward-links to every attendee page.
- Action items with deadlines become `task` pages where they warrant one.

## Phases

1. **Read the sources using the hierarchy above.** Extract attendees and roles, the date,
   the topics discussed, the decisions made, and the action items with their
   owners and deadlines.

2. **Write the interaction page** at `interactions/<slug>.md` — see the shape below.
   Distill the discussion into structured notes by topic; do not paste the raw
   transcript.

3. **Enrich notable attendees.** For each attendee who passes the notability
   gate (`skills/conventions/quality.md`) — a collaborator, student, postdoc, or
   recurring author — chain into `skills/enrich/SKILL.md` to create or update
   their `person` page. A one-off attendee with no research connection does not
   earn a page.

4. **Enrich institutions.** Every notable lab, university, consortium, or funder
   discussed gets the same treatment — chain into `skills/enrich/SKILL.md` for
   an `institution` page.

5. **Forward-link the meeting page.** Add `[[people/<slug>]]` wikilinks for each
   attendee and `[[institutions/<slug>]]` for each institution, plus typed
   `links:` edges in frontmatter. Never hand-write backlinks — they are derived
   (`skills/conventions/graph-and-links.md`).

6. **Promote action items to tasks.** An action item with a real deadline and
   an owner may become a `task` page in `tasks/`, linked from the meeting page.
   Use judgment: a tracked deliverable warrants a task; an offhand "we should
   look at X" does not.

A meeting is **not fully ingested** until its notable entities are enriched and
linked. Stopping at the meeting page leaves a thin, disconnected page.

## Git closeout

Follow `skills/git-ops/SKILL.md`. A standalone meeting ingest closes the
interaction page and required entity/task updates after source/read-back
verification. Inside a Granola sync or batch, return paths and checks to the
parent; the parent owns coherent batch commits and publication.

## Page shape

```markdown
---
kind: interaction
slug: <slug>
title: "<short descriptive title>"
date: YYYY-MM-DD
channel: video  # in-person | video | phone | email — optional, free text
participants: [people/<slug>, people/<slug>]
granola_id: <granola-meeting-id>  # optional; set when the meeting came from Granola
importance: 0.0
links: [institutions/<slug>, projects/<slug>]
sources:
  - hash: sha256-...
    r2_key: meetings/...
    filename: "granola-<id>-transcript.json"
    ingested: YYYY-MM-DD
    provenance: "Granola MCP sync"
tags: []
---

# <Title>

## Attendees
- [[people/<slug>]] — role

## Decisions
What was decided, with context.

## Action items
- Owner — the item — deadline (→ [[tasks/<slug>]] if tracked)

## Discussion notes
Structured notes by topic.
```

## Anti-patterns

- Writing the meeting page without enriching its notable attendees.
- Creating a `person` page for every attendee regardless of notability.
- Pasting the raw transcript instead of distilling the discussion.
- Hand-writing backlinks on attendee pages — they are derived.
- Leaving notable institutions un-enriched "for later".
- Letting nested workers commit incomplete batches rather than returning them to the parent.

## Procedure-change verification

Apply change-scoped verification in `skills/conventions/skill-hygiene.md`.
When the changed behavior requires an execution check, inspect captured output
without live delivery; do not advance production cursors during validation.
