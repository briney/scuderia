---
name: feed-emit
description: >
  Feed card producers — rebuild the instance's local feed outbox from brain
  state. v1 slot: the daily briefing (summary card). (The rem-cycle
  review-queue card was retired 2026-08-15 when the queue was frozen.)
  Invoked by the host's feed-sync wrapper at the commit boundary, never by
  brain-updating skills directly.
triggers:
  - "emit feed cards"
  - "rebuild the feed outbox"
  - "refresh the feed"
---

# feed-emit — producers write the outbox; the syncer pushes

The feed is a defined set of persistent, named, producer-bound slots (card
contract §3.1). This skill owns the v1 producer. Each producer is a
deterministic script: brain state in, card JSON out, no network, no
judgment. The syncer (scuderia `interface/syncer/sync.py`) is the single writer
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
| daily briefing | `<instance>/briefing/daily` | `scripts/emit_briefing_card.py` | `BRIEFING.md` |

Retired: the rem-cycle review-queue card (`<instance>/remcycle/review-queue`,
`emit_review_queue_card.py`) — removed 2026-08-15 when the rem-cycle moved to
the binary commit gate and QUEUE.md was frozen. Git history preserves the
producer if a future attention surface ever needs a card.

The emitter takes `VAULT_ROOT` (required), `FEED_OUTBOX_DIR` (default
`<vault>/feed-outbox`), `FEED_INSTANCE` (default: `instance.yaml` name).

## Contract rules the emitters honor

- **Empty stack ≠ absent card.** An emptied slot emits its "clear" state —
  the dashboard is stable.
- **Dismiss is content-addressed.** The dismissal marker
  (`<outbox>/.state/dismissed.json`) stores the dismissed content hash; the
  card reappears when the briefing content changes.
- **Snooze is feed-side.** `mailbox-drain` records snoozes in
  `<outbox>/.state/snoozes.json`; the brain is untouched by a snooze.
- Salience is producer-assigned (briefing 0.6).

## The outbox is transient

`feed-outbox/` is a derived cache — gitignored in the vault, never committed.
The brain is the sole source of record; the outbox is rebuilt from it.

## Adding a producer (v2+: monitors, funding hits, sweeps)

1. Pick a *slot* you own — never append to someone else's.
2. Write a deterministic emitter script here; keep bodies under the contract
   caps (title 200, body 4000, item title 300, ≤50 items).
3. Wire it into the host feed-sync wrapper alongside the v1 emitter.
