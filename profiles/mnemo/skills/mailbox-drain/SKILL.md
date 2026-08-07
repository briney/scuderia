---
name: mailbox-drain
description: >
  Drain the feed decisions mailbox — apply Bryan's phone-tapped decisions
  (approve / reject / snooze / dismiss) to the brain with apply-time
  validation. Runs at regular intervals and before any consumer acts on
  pending items (drain-before-act). Superseded and unappliable decisions
  surface visibly — never silently dropped.
triggers:
  - "drain the mailbox"
  - "drain the feed decisions"
  - "apply feed decisions"
---

# mailbox-drain — decisions flow back to the brain

The decisions mailbox is the only place information ever lives outside the
brain, and only transiently (card contract §2). This skill keeps that window
short and observable. Bryan taps approve/reject/snooze/dismiss on the feed;
the decisions land in the D1 mailbox; this skill applies them against
**current** brain state and acks them.

> **Conventions:** `rem-cycle-contract.md` (qids, the decision ledger),
> `queue-drain` (execution semantics for queue items — the queue line is the
> work order), `brain-ops` (never blind-overwrite), `feed-emit` (the outbox
> and its `.state/` files).

## When this runs

- On a regular cadence (host cron), and
- **before any consumer acts on pending items** — drain-before-act: a
  "reject" tapped at 11pm beats the 2am rem-cycle run. Rem-cycle phase 0 and
  interactive `queue-drain` sessions drain the mailbox first.

## Correctness lives at apply time

A cached hour-old card on the phone is always possible, so freshness is never
the mechanism — validation is. For each pending decision, check the item
against the *current* brain:

- item still pending → **apply**, ack `applied`
- item already resolved elsewhere (checked, deleted, drained) → ack
  `superseded`, **touch nothing**
- item changed in ways that make the decision ambiguous → ack `flagged`,
  surface in the drain report

Never force-apply. Never silently drop.

## Phases

1. **Fetch.** `scripts/feed_mailbox.py pending` (env: `FEED_URL`,
   `FEED_READER_KEY`). Empty mailbox → stop, say nothing more.
2. **Validate.** Map each decision to its brain target via `card_id` +
   `item_id`. For `<instance>/remcycle/review-queue` items, the item_id is
   the queue qid: find the `- [ ] \`<qid>\`` line in
   `docs/rem-cycle/QUEUE.md`. Unchecked → applicable. Checked (`[x]`),
   rejected (`[~]`), or absent → superseded.
3. **Apply** (only validated-applicable decisions):
   - `approve` → execute exactly as `queue-drain` would: the queue line is
     the work order (typed edge, page author, frontmatter fix — as
     proposed, no re-judgment). Mark QUEUE.md `[x]` with
     `· approved YYYY-MM-DD (feed)`. Append the `decisions.yaml` ledger
     entry with source `feed`.
   - `reject` → mark QUEUE.md `[~]` with `· rejected YYYY-MM-DD (feed)`,
     ledger entry. Lines are never deleted.
   - `snooze` → feed-side only: record `{qid: until_iso}` in
     `<vault>/feed-outbox/.state/snoozes.json` (default 3 days; the payload
     carries the duration). Brain untouched; the item leaves the card stack
     on the next emit and returns when the snooze elapses.
   - `dismiss` → card-level, feed-side only: record the card's current
     content hash in `<vault>/feed-outbox/.state/dismissed.json`. The card
     reappears when its content changes.
4. **Ack.** `scripts/feed_mailbox.py ack <id> <applied|superseded|flagged>`
   for every decision, applied or not. An unacked decision stays pending and
   blocks re-decision (the 409 duplicate guard) — ack everything you
   processed.
5. **Record + report.** Commit brain changes with
   `mailbox-drain: apply <n> feed decisions (<qids>)`. The report lists each
   decision and its outcome; flagged/superseded ones are called out, not
   buried. The next feed-sync tick rebuilds the card — items resolved in
   the brain leave the stack on their own.

## Anti-patterns

- Applying without validating against current brain state — the tap is not
  the truth; the brain is.
- Silently dropping an unappliable decision — ack it `superseded` or
  `flagged` and say so.
- Executing queue items with fresh judgment — `queue-drain` semantics: the
  queue line is the work order.
- Touching the brain for snooze/dismiss — those are feed-side; only the
  outbox `.state/` files change.
- Letting a drained mailbox go unacked — pending rows block re-decision via
  the duplicate guard.
