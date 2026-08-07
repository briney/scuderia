---
name: meeting-ingestion
description: Ingest a meeting or talk transcript into a meeting page — extract attendees, decisions, action items, and topics, then enrich every notable attendee and institution.
triggers:
  - "process this meeting"
  - "meeting transcript"
  - "meeting notes"
  - a meeting or talk transcript received
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

When the meeting source is a Granola sync (or any source with an AI-generated
summary), use the **summary as the primary source** for distillation. The
transcript is for spot-checking specific details — not as the primary input.

For long meetings (study sections, all-day workshops, transcripts >20K chars),
the summary is the only practical source — the transcript is too large to
process in a single context window. The raw transcript must still be archived
to R2 (see `skills/conventions/raw-source-archive.md`) so it can be consulted later
if the summary missed something.

If the transcript is available and short enough (<10K chars), read it to
catch nuances the summary may have flattened — but the page is still a
distillation, not a transcript paste.

**No summary available.** Granola occasionally returns an empty or "No
summary" result from `get_meetings` even for meetings that do have a
transcript. In this case, fall back to the raw transcript as the primary
source: call `get_meeting_transcript` with the meeting ID to retrieve the
full transcript, then distill directly from it. The same distillation
rules apply — structured notes by topic, no raw transcript paste. Flag in
the meeting page or to the user that no AI summary was available and the
page was distilled from the transcript only.

**Batch ingestion.** When ingesting multiple meetings in one session,
fetch all summaries (`get_meetings`) and transcripts
(`get_meeting_transcript`) in parallel up front — the Granola MCP calls are
independent of each other. This avoids serial round-trips when the user
provides several Granola IDs at once. Apply the notability gate to all
attendees across all meetings before creating person pages, so a recurring
attendee who appears in multiple meetings gets one page, not duplicates.

**`get_meetings` 10-ID cap.** The `mcp__granola__get_meetings` tool accepts
at most 10 meeting IDs per call. When ingesting more than 10 meetings, split
into multiple calls (e.g., 10 + N) and issue them in parallel — they are
independent.

**Pre-processed metadata entry path.** Sometimes the user has already done
the Granola sync and R2 archiving themselves, and hands you a batch of
meetings with slugs, dates, archive metadata (hash, r2_key, filename),
importance scores, links, and tags already determined. In this case, skip the
source-adapter phase entirely (no `granola-meeting-sync` chaining, no R2
upload) — go directly to fetching the Granola AI summary via
`mcp__granola__get_meetings` for distillation content, then write the pages
using the user-provided metadata for frontmatter. This is the fastest path:
the user is the source adapter; you are the distiller and page writer.

## What this guarantees

- Every meeting becomes an `interaction` page with participants, decisions,
  action items, and topics discussed.
- Every notable attendee and institution is enriched.
- The meeting page forward-links to every attendee page.
- Action items with deadlines become `task` pages where they warrant one.

## Phases

1. **Parse the transcript.** Extract the attendees and their roles, the date,
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

## Committing batch work — race the auto-snapshot

The brain repo has an `auto_push.sh` cron that runs every 5 minutes and
commits any uncommitted files with a generic `auto: snapshot <timestamp>`
message. When writing a batch of pages (e.g., 10+ meetings), this cron can
fire mid-batch and commit some of your files before you do — burying your
descriptive commit message for those files.

**Mitigation:** After writing all files for a batch, `git add` and `git commit`
immediately in a single terminal call. Do not interleave other work between
the last `write_file` and the commit. If the auto-snapshot does catch some
files, verify the committed content is correct (`git diff HEAD -- <file>`)
and commit the remaining files with your descriptive message. The auto-snapshot
does not corrupt content — it only steals the commit message.

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
- Letting the auto-snapshot commit your batch files before you do — commit
  immediately after the last write.
