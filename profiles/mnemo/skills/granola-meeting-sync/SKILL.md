---
name: granola-meeting-sync
description: Pull meetings from Granola via MCP, deduplicate against existing brain pages, and feed new meetings into the meeting-ingestion workflow.
triggers:
  - "pull meetings from granola"
  - "sync granola meetings"
  - "import meetings from granola"
  - cron-driven daily meeting sync
---

# Granola meeting sync — source adapter for Granola meetings

Granola is Bryan's meeting recorder. This skill is the **source adapter**: it
pulls meeting data from Granola via the Granola MCP server, deduplicates against
existing `interactions/` pages, and feeds each new meeting into
`skills/meeting-ingestion/SKILL.md` for distillation.

This skill does **not** write meeting pages itself — that is `meeting-ingestion`'s
job. This skill handles: what's new, what's already in the brain, and how to
translate Granola's data into the transcript-shaped input that
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
SCRIPT=<soma-checkout>/profiles/mnemo/skills/granola-meeting-sync/scripts/granola_mcp.py

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
- **On-demand sync:** Use the date range Bryan specifies, or default to the last
  7 days if none given.

### 2. Verify the MCP connection

Run the bridge script to check the account:

```bash
VENV=$HOME/.hermes/hermes-agent/venv/bin/python3
SCRIPT=<soma-checkout>/profiles/mnemo/skills/granola-meeting-sync/scripts/granola_mcp.py
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

```bash
$VENV $SCRIPT list_meetings --range last_week
```

This returns JSON with a `meetings` array. Each meeting has: meeting ID, title,
date, attendees. Parse the JSON from the terminal output.

### 4. Deduplicate

For each meeting from Granola, check whether an `interactions/` page already exists
with that `granola_id`. Scan `interactions/*.md` files for `granola_id:` in
frontmatter. If a match is found, skip that meeting.

### 5. Fetch full content for new meetings

For each new meeting, call the bridge script to fetch details and transcript:

```bash
# Get meeting details (AI-enhanced notes + private notes)
$VENV $SCRIPT get_meetings MEETING_ID

# Get raw transcript (if available on your plan)
$VENV $SCRIPT get_transcript MEETING_ID
```

The `get_meetings` command returns the enhanced (AI-generated) notes and private
notes. The `get_transcript` command returns the raw verbatim transcript — the
richest source for distillation.

**Source hierarchy:** Use the Granola AI summary as the **primary source** for
distillation. The transcript is for spot-checking specific details the summary
may have missed, not as the primary input. For long meetings (study sections,
all-day workshops, transcripts >20K chars), the summary is the only practical
source — the transcript is too large to process in a single context window.

If `get_transcript` returns an error about paid plans, use the enhanced notes as
the primary source. The enhanced notes are Granola's AI summary — useful, but
treat as a secondary source when the transcript is available, since the
transcript has the verbatim discussion.

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
- The enhanced notes (as context for distillation).
- The raw transcript (as the primary source for distillation, when available).
- The `granola_id` to set in the meeting page frontmatter.
- The `sources:` entry (hash, r2_key, filename, ingested, provenance) from the
  R2 archive step, so meeting-ingestion includes it in the meeting page's
  frontmatter.

Then chain into `skills/meeting-ingestion/SKILL.md` and let it handle the
distillation, attendee enrichment, institution enrichment, and action-item
promotion. **Do not** write the meeting page directly — delegate to
`meeting-ingestion`.

When chaining, pass the `granola_id` and the `sources:` entry explicitly so
`meeting-ingestion` includes them in the frontmatter of the page it writes.

### 7. Update sync state

After a successful sync, write the current date to
`~/.hermes/profiles/<instance>/.granola-sync-state.json`:

```json
{"last_sync": "2026-07-10"}
```

This is the watermark for the next cron-driven run.

### 8. Report

Summarize what was synced: how many meetings found, how many were new, how many
skipped as duplicates, how many ingested. If any failed, report the failure
with the meeting title and the error.

## On-demand usage

Bryan can request specific meetings or date ranges:
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
- Using the enhanced notes as the primary source when the transcript is available.
- Updating the sync watermark on an on-demand pull of an old date range.
- Fabricating meeting data when the MCP connection is down.
- Assuming native MCP tool calls won't work without trying them first. The
  bridge script is a fallback, not the default path.
