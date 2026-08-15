---
name: synthesis-briefing
description: >
  Compose the weekly PUSH — a human-facing digest of the synthesis engine's output.
  Reads the week's accumulation (the nightly One-thing surfacings, new
  `[unconfirmed]` concept Shifts, the week's notable: signals) since the last briefing
  and writes an archived, dated, hypotheses-first digest to `docs/rem-cycle/briefings/`.
  A pure weekly composer, distinct from the daily-logistics `briefing`; the Hermes
  profile drives its cadence and optional Telegram delivery.
triggers:
  - "weekly synthesis briefing"
  - "compose the synthesis briefing"
  - "what precipitated this week"
---

# synthesis-briefing — the weekly PUSH

The delivery surface that closes the concept layer's loop back to your human. The
synthesis engine — `reinforce` nightly, `intersect` nightly — writes *state* into
concept `## Shifts` logs and the night's `notable:` signals; this composes that
week's movement into a
**reading-shaped** digest. It is deliberately *not* the rem-cycle **dream report**
(a ten-second nightly glance: One thing + Done) and *not* the daily **`briefing`**
(logistics: deadlines, meetings). It is **not a rem-cycle phase** either — it
aggregates the *week's accumulation* across many runs, not any one run's output, so
it is standalone and is **never registered in the rem-cycle phase pipeline**. Full
design: the instance's private `docs/specs/`.

> **Conventions:** `synthesis-layer-pages.md` (the concept `## Shifts` it reads, the
> hypothesis anatomy it surfaces), `rem-cycle-contract.md` (the binary gate, the
> notable signals and dream reports it reads; the dream report it must **not**
> duplicate), `_output-rules.md`
> (deterministic links, no slop, no preamble), `skills/conventions/capabilities.md` (`schedule-job` /
> `deliver-message` are Hermes-side). Character: `SOUL.md` — **quiet weeks read thin;
> never manufacture content.**

## Capabilities

- **Required:** `brain-read`, `brain-write` (its own briefing artifact only).
- **Hermes-only (cadence + delivery):** `schedule-job` (the weekly cron) +
  `deliver-message` (optional Telegram nudge). Under Claude Code the skill composes
  **on demand**; the recurring weekly push is a Hermes-profile binding, not this
  skill.

No external I/O — it reads vault state and writes one markdown file.

## What this guarantees

- **Read-and-compose only.** Mutates nothing but its own
  `briefings/<date>.md` — no concept edits, no rem-cycle state changes.
- **Hypotheses-first.** Leads with the week's precipitated hypotheses (the
  high-value output), then concept movements, then the week's notable signals.
- **Quiet-week honesty.** A thin week reads thin — it never manufactures content to
  look productive (`SOUL.md`), matching the engine's silence-is-fine ethos.
- **Archived, dated, idempotent.** Writes `docs/rem-cycle/briefings/<YYYY-MM-DD>.md`
  **dated by the week's start (the ISO-week Monday)**, so a re-run any day that week
  regenerates the one file, never a duplicate; the top level never accumulates.
- **Since the last briefing.** New hypotheses, new Shifts, and the week's
  One-thing surfacings are the delta since the prior briefing (watermark = the
  latest `briefings/` file), not the whole history.

## Phases

1. **Watermark.** The last briefing date — the most recent file in
   `docs/rem-cycle/briefings/` (or, on the first run, the beginning of time).
2. **Gather.** The *delta* since the watermark — `hypotheses/` pages created
   this week, new `[unconfirmed]` Shifts across `concepts/*.md`, the week's
   One-thing surfacings (from `docs/rem-cycle/history/<date>-nightly.md`), and
   the week's `notable:` signals (from the `-nightly-verbose.md` reports).
3. **Compose** the hypotheses-first digest (structure in Output), skimmable in under
   a minute, highest-impact first. A quiet week says so plainly.
4. **Write** the current week's file `docs/rem-cycle/briefings/<week-start>.md`
   (overwriting any existing file for the current week). Standalone, also surface a
   conversational summary.

## Output

Written to `docs/rem-cycle/briefings/<YYYY-MM-DD>.md` (dated by the week's start;
`_output-rules.md`):

```markdown
# Synthesis briefing — week of {week-start}

**This week:** {N} new hypotheses precipitated · {M} concepts moved · {K} notable signals.

## New hypotheses
- **{claim}** — {promise tags}; combines [[concepts/{a}]] ({bet}) × [[concepts/{b}]] ({bet}).
  *Discriminating test:* {test}. → [[hypotheses/{slug}]]

## What moved on your concepts
### [[concepts/{slug}]]
- {date} — [unconfirmed] {shift}: {hedged one-line — shown vs. concluded + the edge}. → confirm / contest

## The week's One-things
- {date} — {the nightly intersect surfacing, one line each}

## Notable signals
- {the week's notable: observations, highest-impact first — contradictions, ripe concepts, suspected duplicates}
```

On a quiet week: `**This week:** no new hypotheses; {M} Shifts.` and the empty
sections are dropped, not padded.

## The Hermes seam

The **weekly cadence** (`schedule-job` → `hermes cron`) and the **optional Telegram
nudge** (`deliver-message`) live in the **Hermes profile**, not this skill. The skill
composes on invocation; a Hermes session wires the cron once (a weekly entry after
the week's cycles) and, optionally, the "digest ready" ping. Under Claude Code,
invoke on demand — the `.md` in Obsidian is the delivery.

## Anti-patterns

- Manufacturing content on a quiet week — a thin week reads thin (`SOUL.md`).
- Duplicating the audit-shaped dream report — this is the reading-shaped digest, a
  different audience.
- Editing concepts or rem-cycle state — read-and-compose only; the one write is
  its own briefing.
- Accumulating briefings at the vault top level — always archived + dated under
  `briefings/`.
- Re-aggregating the whole history — only the delta since the last briefing.
- Leading with concept movements over hypotheses — the precipitate goes first.
- Registering this in the `rem-cycle` phase pipeline — it is a standalone weekly
  composer over the week's accumulation, not a per-run phase.
- Reporting the *awaiting-your-call* count as this week's delta — it is the full
  standing backlog; a delta would hide aging items.
