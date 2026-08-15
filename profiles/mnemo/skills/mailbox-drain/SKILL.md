---
name: mailbox-drain
description: >
  Drain the feed decisions mailbox — apply Bryan's phone-tapped decisions
  (dismiss / snooze) with apply-time validation. Runs at regular intervals.
  Superseded and unappliable decisions surface visibly — never silently
  dropped. (The approve/reject path died with the rem-cycle review-queue
  card, retired 2026-08-15.)
triggers:
  - "drain the mailbox"
  - "drain the feed decisions"
  - "apply feed decisions"
---

# mailbox-drain — decisions flow back to the brain

The decisions mailbox is the only place information ever lives outside the
brain, and only transiently (card contract §2). This skill keeps that window
short and observable. Bryan taps dismiss/snooze on the feed; the decisions
land in the D1 mailbox; this skill applies them against **current** brain
state and acks them.

> **Conventions:** `brain-ops` (never blind-overwrite), `feed-emit` (the
> outbox and its `.state/` files). Historical: the approve/reject path
> applied rem-cycle queue items — that surface was retired 2026-08-15
> (`rem-cycle-contract.md`, the binary gate).

## When this runs

On a regular cadence (host cron). (The old drain-before-act rule — a phone
tap beating the nightly rem-cycle — died with the queue; no brain consumer
acts on mailbox state anymore.)

## Correctness lives at apply time

A cached hour-old card on the phone is always possible, so freshness is never
the mechanism — validation is. For each pending decision, check the item
against the *current* brain:

- item still applicable → **apply**, ack `applied`
- item already resolved elsewhere → ack `superseded`, **touch nothing**
- item changed in ways that make the decision ambiguous → ack `flagged`,
  surface in the drain report
- a stale approve/reject for a `<instance>/remcycle/review-queue` item →
  ack `superseded` (the queue is frozen; nothing to apply)

Never force-apply. Never silently drop.

## Phases

1. **Fetch.** `scripts/feed_mailbox.py pending` (env: `FEED_URL`,
   `FEED_READER_KEY`). Empty mailbox → stop, say nothing more.
2. **Validate.** Map each decision to its target via `card_id` + `item_id`.
3. **Apply** (only validated-applicable decisions; all feed-side, the brain
   is untouched):
   - `dismiss` → card-level: record the card's current content hash in
     `<vault>/feed-outbox/.state/dismissed.json`. The card reappears when its
     content changes.
   - `snooze` → record `{item_id: until_iso}` in
     `<vault>/feed-outbox/.state/snoozes.json` (default 3 days; the payload
     carries the duration). The item leaves the card stack on the next emit
     and returns when the snooze elapses.
4. **Ack.** `scripts/feed_mailbox.py ack <id> <applied|superseded|flagged>`
   for every decision, applied or not. An unacked decision stays pending and
   blocks re-decision (the 409 duplicate guard) — ack everything you
   processed.
5. **Report.** The drain report lists each decision and its outcome;
   flagged/superseded ones are called out, not buried. (No brain commit —
   dismiss/snooze are feed-side only.)

## Anti-patterns

- Applying without validating against current brain state — the tap is not
  the truth; the brain is.
- Silently dropping an unappliable decision — ack it `superseded` or
  `flagged` and say so.
- Touching the brain for snooze/dismiss — those are feed-side; only the
  outbox `.state/` files change.
- Letting a drained mailbox go unacked — pending rows block re-decision via
  the duplicate guard.
