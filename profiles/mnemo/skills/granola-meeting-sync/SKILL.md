---
name: granola-meeting-sync
description: Pull meetings from Granola via MCP, deduplicate against existing brain pages, and feed new meetings into the meeting-ingestion workflow.
triggers:
  - "pull meetings from granola"
  - "sync granola meetings"
  - "import meetings from granola"
  - cron-driven daily meeting sync
eval_contract:
  goal: Fetch and deduplicate Granola meetings, preserve source identity, and hand them to meeting-ingestion without redefining its source hierarchy.
  dimensions:
  - IDENTITY — granola_id dedup prevents duplicate interaction pages
  - HANDOFF — available notes, transcript, and archive metadata reach the distiller
  - STATE — only successfully completed scheduled syncs advance the watermark
  - FAILURES — unavailable sources and failed ingests are reported
  hard_fails:
  - Fabricating a source, archive verification, or successful ingest.
  - Advancing the watermark past an incomplete sync or on an on-demand pull.
---

# Granola meeting sync — source adapter for Granola meetings

> **Git closeout:** Follow `skills/git-ops/SKILL.md`. The sync parent owns each verified group of interaction/entity/task changes. meeting-ingestion returns paths and checks; update the sync watermark only after successful ingestion, and report Git publication failure separately so a retry does not duplicate meetings.

Granola is your human's meeting recorder. This skill is the **source adapter**: it
pulls meeting data from Granola via the Granola MCP server, deduplicates against
existing `interactions/` pages, and feeds each new meeting into
`skills/meeting-ingestion/SKILL.md` for distillation.

This skill does **not** write meeting pages itself — that is `meeting-ingestion`'s
job. This skill handles: what's new, what's already in the brain, and how to
translate Granola's data into the source bundle that
`meeting-ingestion` expects.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/quality.md` (citations, the notability gate),
> `skills/conventions/graph-and-links.md` (the edge forms).

## Capabilities

`brain-search`, `brain-read`, `brain-write` (for the dedup scan), `terminal`
(for the Granola MCP bridge script fallback — see below), and
`raw-source-archive-upload` (for archiving transcripts to R2).

## Calling Granola MCP — native calls first, bridge script as fallback

**Try native MCP tool calls first.** The Hermes gateway exposes Granola MCP
tools as `mcp__granola__*` (e.g. `mcp__granola__get_meetings`,
`mcp__granola__get_meeting_transcript`, `mcp__granola__list_meetings`,
`mcp__granola__query_granola_meetings`). These should be your first approach.
For batch fetches, `mcp__granola__get_meetings` accepts up to 10 meeting IDs
in a single call — use this to minimize round-trips when ingesting multiple
meetings.

If native calls fail (the model emits prose and stops without making the
function call), a Python bridge script is available as a fallback. It handles
OAuth token loading, the MCP HTTP connection, and tool invocation. It lives at:

```
skills/granola-meeting-sync/scripts/granola_mcp.py
```

Run it with Hermes' venv Python (the system Python lacks the `mcp` package):

```bash
VENV=$HOME/.hermes/hermes-agent/venv/bin/python3
SCRIPT=<scuderia-checkout>/profiles/mnemo/skills/granola-meeting-sync/scripts/granola_mcp.py

# Verify connection and account
$VENV $SCRIPT account_info

# List meetings (default: last_30_days; also: this_week, last_week)
$VENV $SCRIPT list_meetings --range last_week

# Get meeting details (pass one or more meeting IDs)
$VENV $SCRIPT get_meetings MEETING_ID

# Get raw transcript
$VENV $SCRIPT get_transcript MEETING_ID

# Natural-language query
$VENV $SCRIPT query "meetings about grants"
```

The script reads OAuth tokens from `~/.hermes/profiles/<instance>/mcp-tokens/granola.json`.
If the token file is missing (it can be consumed by the gateway on restart), the
script reports the error and tells you to run `hermes mcp login granola`.

## Prerequisites

- Granola MCP server configured in `config.yaml` under `mcp_servers.granola`.
- OAuth completed: `hermes mcp login granola` (interactive terminal, one-time).
  Re-run this if the token expires or if you need to switch accounts.
- The `mcp` Python package installed in Hermes' venv (it is by default).

## What this guarantees

- Every new Granola meeting becomes an `interaction` page via `meeting-ingestion`.
- No meeting is ingested twice — the Granola meeting ID is the dedup key.
- The sync tracks the last successful pull date so it only fetches new meetings.
- On-demand pulls (specific date ranges, specific meetings) are supported.
- Failures (OAuth expired, MCP down, rate limited) are reported, not swallowed.

## The Granola meeting ID

Each Granola meeting has a unique ID returned by `list_meetings`. This ID is
stored in the meeting page's frontmatter as `granola_id`:

```yaml
granola_id: <granola-meeting-id>
```

This field is the **dedup key**. Before ingesting any meeting, scan existing
`interactions/` pages for a matching `granola_id`. If found, skip — the meeting is
already in the brain.

The field is optional on the meeting page shape (not all meetings come from
Granola), but **required** on any meeting page created by this skill.

## Phases

### 1. Determine the pull window

- **Cron-driven sync:** Read the last sync date from
  `~/.hermes/profiles/<instance>/.granola-sync-state.json` (a small JSON file with
  `{"last_sync": "YYYY-MM-DD"}`). Pull meetings since that date. If the file
  does not exist, default to the last 7 days.
- **On-demand sync:** Use the date range your human specifies, or default to the last
  7 days if none given.

### 2. Verify the MCP connection

Call native `mcp__granola__get_account_info` first. If native tools are
unavailable or fail, use the bridge script:

```bash
VENV=$HOME/.hermes/hermes-agent/venv/bin/python3
SCRIPT=<scuderia-checkout>/profiles/mnemo/skills/granola-meeting-sync/scripts/granola_mcp.py
$VENV $SCRIPT account_info
```

This confirms the connection is live and the right Granola account is connected.
If it fails:
- Token file missing → report "Granola OAuth token file not found. Run
  `hermes mcp login granola` in a terminal to authenticate." and stop.
- OAuth expired → report "Granola MCP OAuth token expired. Run `hermes mcp
  login granola` in a terminal to re-authenticate." and stop.
- MCP server down → report the error and stop. Do not proceed with stale data.

### 3. List recent meetings

Use native `mcp__granola__list_meetings` with the phase-1 pull window; use a
custom range when needed. Request the connected user’s meetings rather than
all workspace-visible notes. The bridge fallback below is a last-week example,
not a replacement for the actual window:

```bash
$VENV $SCRIPT list_meetings --range last_week
```

Inspect the returned format before parsing: native tools and the bridge may
return text containing meeting records rather than a JSON `meetings` array.
Extract IDs, titles, dates, and known participant metadata; reconcile the
declared count with the records collected. Participant metadata alone does
not prove attendance. For bridge results without an involvement filter,
verify the user’s involvement before ingesting workspace-accessible notes.

### 4. Deduplicate

For each meeting from Granola, check whether an `interactions/` page already exists
with that `granola_id`. Scan `interactions/*.md` files for `granola_id:` in
frontmatter. If a match is found, skip that meeting.

### 5. Fetch full content for new meetings

For new meetings, fetch details with native `mcp__granola__get_meetings`
(in batches up to its current schema limit) and transcripts with
`mcp__granola__get_meeting_transcript`. Independent requests may run in parallel.
Use the bridge only as a fallback:

```bash
# Get meeting details (AI-enhanced notes + private notes)
$VENV $SCRIPT get_meetings MEETING_ID

# Get raw transcript (if available on your plan)
$VENV $SCRIPT get_transcript MEETING_ID
```

The details response supplies AI-enhanced notes and any private notes; the
transcript response supplies verbatim discussion when available. Pass both
with their source labels. `skills/meeting-ingestion/SKILL.md` owns the
summary-first distillation and transcript-verification rules; this adapter
does not define another hierarchy. If no summary exists, fetch the transcript
for transcript-only distillation. If transcript access fails, report the
limitation and pass the available notes without claiming transcript checks.

### 5a. Archive the transcript to R2

**Every meeting's raw transcript must be archived to R2** as a raw-source
document, following `skills/conventions/raw-source-archive.md`. This ensures the
verbatim source is preserved for future reference and for regenerating
summaries if the models improve.

The archive step:

```bash
# 1. Write the transcript JSON to a temporary file
#    (the bridge script outputs JSON with id, title, transcript fields)

# 2. Hash the source file
HASH=$(shasum -a 256 /tmp/meeting-<granola_id>.json | cut -d' ' -f1)

# 3. Upload to R2 under the meetings/ key prefix
KEY="meetings/${HASH}.json"
RCLONE_CONFIG=$HOME/.config/rclone/rclone.conf \
  rclone copyto /tmp/meeting-<granola_id>.json "<instance>-r2:<instance>-drops/${KEY}" \
  --timeout 120s --contimeout 10s

# 4. Verify round-trip
RCLONE_CONFIG=$HOME/.config/rclone/rclone.conf \
  rclone lsf "<instance>-r2:<instance>-drops/${KEY}" --timeout 30s >/dev/null

# 5. Record the pointer in the meeting page's frontmatter (passed to meeting-ingestion)
#    The sources entry: { hash: sha256-..., r2_key: meetings/..., filename: "granola-<id>-transcript.json", ingested: YYYY-MM-DD, provenance: "Granola MCP sync" }
```

If the transcript is unavailable (paid plan), archive the enhanced notes
summary instead — the best available source is always archived.

The `granola_id`, `hash`, and `r2_key` are passed to `meeting-ingestion` so it
can include them in the meeting page's `sources:` frontmatter.

### 6. Feed into meeting-ingestion

For each new meeting, assemble the input for `meeting-ingestion`:
- The meeting title, date, and attendees from Granola.
- The AI-enhanced summary and private notes, labeled separately.
- The raw transcript when available, or its retrieval failure; source use is
  governed by meeting-ingestion.
- The `granola_id` to set in the meeting page frontmatter.
- The `sources:` entry (hash, r2_key, filename, ingested, provenance) from the
  R2 archive step, so meeting-ingestion includes it in the meeting page's
  frontmatter.

Then chain into `skills/meeting-ingestion/SKILL.md` and let it handle the
distillation, attendee enrichment, institution enrichment, and action-item
promotion. Delegate independent meeting distillations when useful; assign
non-overlapping writes and verify each returned page before advancing state.

When chaining, pass the `granola_id` and the `sources:` entry explicitly so
`meeting-ingestion` includes them in the frontmatter of the page it writes.

### 7. Update sync state

Only after the scheduled pull window is fully processed and every new
meeting is ingested and verified, write the current date to
`~/.hermes/profiles/<instance>/.granola-sync-state.json`. On any retrieval or
ingestion failure, retain the prior watermark; completed pages are deduped
on retry. An on-demand pull never changes this state. Example shape:

```json
{"last_sync": "2026-07-10"}
```

This is the watermark for the next cron-driven run.

### 8. Report

Summarize what was synced: how many meetings found, how many were new, how many
skipped as duplicates, how many ingested. If any failed, report the failure
with the meeting title and the error.

## On-demand usage

your human can request specific meetings or date ranges:
- "Pull my meetings from last week" → sync the last 7 days.
- "Pull meetings from June" → sync a specific date range.
- "Pull the meeting with Sam about X" → use the bridge script's `query` command
  to find the meeting, then fetch and ingest it.

On-demand pulls do **not** update the sync watermark — only cron-driven syncs
do. This prevents an on-demand pull of an old date range from resetting the
watermark backward.

## Cron-driven sync

The cron job runs daily. It reads the watermark, pulls since that date, and
ingests new meetings. The job prompt is self-contained and loads this skill.

If the MCP connection fails, the cron job reports the failure and exits — it
does not silently skip. The failure is visible in the cron job output.

## Anti-patterns

- Writing a meeting page directly instead of chaining into `meeting-ingestion`.
- Ingesting a meeting twice because the `granola_id` dedup was skipped.
- Proceeding without verifying the MCP connection (silent failures).
- Redefining source precedence instead of following meeting-ingestion.
- Updating the sync watermark on an on-demand pull of an old date range.
- Fabricating meeting data when the MCP connection is down.
- Assuming native MCP tool calls won't work without trying them first. The
  bridge script is a fallback, not the default path.

## Procedure-change verification

Edits require the no-regression read-back in `skills/conventions/skill-hygiene.md`.
For scheduled consumers, re-run a representative task and inspect its real
output without live delivery; do not advance production cursors during a check.
