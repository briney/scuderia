---
name: feed-emit
description: >
  Feed card producers — rebuild the instance's local feed outbox from brain
  state. v1 slots: the rem-cycle review queue (review card) and the daily
  briefing (summary card). Invoked by the host's feed-sync wrapper at the
  commit boundary, never by brain-updating skills directly.
triggers:
  - "emit feed cards"
  - "rebuild the feed outbox"
  - "refresh the feed"
---

# feed-emit — producers write the outbox; the syncer pushes

The feed is a defined set of persistent, named, producer-bound slots (card
contract §3.1). This skill owns the v1 producers. Each producer is a
deterministic script: brain state in, card JSON out, no network, no
judgment. The syncer (soma `interface/syncer/sync.py`) is the single writer
to D1 — it validates against the schema allowlist and pushes diffs.

## When this runs

At the **commit boundary only** — the host's feed-sync wrapper runs the
emitters and then the syncer on every auto_push tick. Do NOT hook emission
into brain-updating skills (ingest, synthesis, capture…): fan-out burden,
and one forgetful skill means a silently stale card. That anti-pattern was
considered and rejected in the card-contract spec §4.4.

## v1 slots

| slot | card_id | script | source |
|---|---|---|---|
| rem-cycle review queue | `<instance>/remcycle/review-queue` | `scripts/emit_review_queue_card.py` | `docs/rem-cycle/QUEUE.md` |
| daily briefing | `<instance>/briefing/daily` | `scripts/emit_briefing_card.py` | `BRIEFING.md` |

Both take `VAULT_ROOT` (required), `FEED_OUTBOX_DIR` (default
`<vault>/feed-outbox`), `FEED_INSTANCE` (default: `brain.yaml` name).

## Contract rules the emitters honor

- **item_id = the queue qid.** Already a stable hash; re-emitting updates in
  place; an item that leaves QUEUE.md leaves the card on the next sync.
- **Empty stack ≠ absent card.** An emptied review queue emits its "queue
  clear" state — the dashboard is stable.
- **Snooze is feed-side.** `mailbox-drain` records snoozes in
  `<outbox>/.state/snoozes.json` (`{qid: until_iso}`); the queue emitter
  holds snoozed items out of the stack until the snooze elapses. The brain
  is untouched by a snooze.
- **Dismiss is content-addressed.** For the briefing card, the dismissal
  marker (`<outbox>/.state/dismissed.json`) stores the dismissed content
  hash; the card reappears when the briefing content changes.
- Salience is producer-assigned (queue 0.8 — it has the measured drain
  problem; briefing 0.6).

## The outbox is transient

`feed-outbox/` is a derived cache — gitignored in the vault, never committed.
The brain is the sole source of record; the outbox is rebuilt from it.

## Adding a producer (v2+: monitors, funding hits, sweeps)

1. Pick a *slot* you own — never append to someone else's.
2. Write a deterministic emitter script here; keep bodies under the contract
   caps (title 200, body 4000, item title 300, ≤50 items).
3. Wire it into the host feed-sync wrapper alongside the v1 emitters.
