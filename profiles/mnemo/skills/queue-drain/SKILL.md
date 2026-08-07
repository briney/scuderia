---
name: queue-drain
description: >
  Drain the rem-cycle review queue — approve, reject, or auto-execute QUEUE.md
  proposals by qid. Runs conversationally ("approve a3f2", "reject the cites
  edges", "drain the queue"), as the rem-cycle phase-0 delegate (graduated
  autonomy), and from brief replies ("approve 1-2"). Executed changes are
  recorded in the decision ledger.
triggers:
  - "approve queue item"
  - "reject queue item"
  - "drain the queue"
  - "approve <qid list>"
  - "what's in the review queue"
---

# queue-drain — the queue gets a drain

QUEUE.md is the review surface for every judgment call the dream produces
(`rem-cycle-contract.md`). This skill is the action surface: it turns a checked
intent into an executed graph change, exactly as proposed, with an audit trail.

> **Conventions:** `rem-cycle-contract.md` (qids, the decision ledger, the two
> commit tiers, the graduated-autonomy gates), `graph-and-links.md` (forward-only
> edges), `brain-ops` (never blind-overwrite), `quality.md` (cite-or-flag).
> Character: `SOUL.md`.

## Capabilities

`brain-read`, `brain-write`, `brain-search`. Universal; no external I/O.

## What this guarantees

- An approved item executes **exactly as proposed** — the queue line's target,
  change, and evidence are the work order. No re-judgment, no embellishment.
- Every execution is recorded in `docs/rem-cycle/decisions.yaml` (append-only)
  and marked in QUEUE.md in place (`[x]` approved, `[~]` rejected, with a
  decision line). The queue file stays the audit trail; lines are never deleted.
- An item whose target no longer exists or whose change no longer applies is
  reported as `stale` and left for Bryan — never force-applied.
- Auto-executions (phase-0 mode) additionally satisfy all four graduated-autonomy
  gates and carry the revert banner. This skill never widens the whitelist
  itself.

## Phases

1. **Resolve.** Map the request to qids: explicit qids from the trigger; brief
   reply ordinals ("approve 1-2") resolve against the items the last brief
   surfaced (`_state.yaml → briefing.last_surfaced`, in order); "drain the
   queue" walks every unchecked item interactively.
2. **Validate.** For each qid: exists in QUEUE.md and unchecked; not stale
   (target page exists unless the proposal says otherwise; change still
   applicable). Stale → report, skip.
3. **Execute.** Apply the change: add the typed edge / wikilink; author the
   proposed page from its outline+sources (synthesis items); recompute the
   importance. Forward-only; evidence preserved; never touch a protected page.
4. **Record.** QUEUE.md: `[x]` + `· approved YYYY-MM-DD (human/<instance>) · <sha>`.
   Append the `decisions.yaml` entry. Auto-executions add the inline banner
   `[auto-approved YYYY-MM-DD · qid <qid> · revert: git revert <sha>]`.
5. **Commit.** One commit per drain session: `queue-drain: approve <n> items
   (<qids>)` (or `reject`). Rejections: `queue-drain: reject <n> items`.

## As rem-cycle phase 0

The orchestrator (or, post-decomposition, the `rem-drain` cron job) passes
`mode`:
- `detect-and-log` — report what *would* auto-run (gates evaluated, whitelist
  applied) in the dream report; execute nothing.
- `armed` — execute items conforming to the armed whitelist
  (`_state.yaml → autonomy`; grant-armed classes skip the age/track-record
  gates). Cap 20/run for grant-armed classes. **Synthesis items (concepts,
  hypotheses) never auto-execute regardless of mode** — they are always left
  for Bryan (standing grant, 2026-08-04).

Returns the fenced-yaml phase result: `committed[]` (category `auto-approved`),
`metrics` (`items_examined`, `auto_executed`, `would_auto_run`,
`ineligible_by_class`, `too_fresh`, `track_record_not_met`), no cursor.

## Anti-patterns

- Re-judging an approved proposal or "improving" it while executing — the queue
  line is the work order.
- Deleting queue lines, or rewriting unchecked ones — mark in place, never erase.
- Force-applying a stale item — report it instead.
- Executing anything outside the whitelist in phase-0 mode — the gates are
  conjunctive; when in doubt, leave it for Bryan.
- Skipping the ledger entry — an unrecorded execution is indistinguishable from
  a rogue write.
- Widening the whitelist, shortening the age gate, or raising the cap without
  Bryan — those are spec changes, not runtime decisions.
