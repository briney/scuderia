# interface/ — the feed layer

Framework-level machinery for the card feed: a renderer that turns cards into
a page, the card contract that producers emit, and pluggable publishers. The
renderer knows what a *card* is — never what a budget or a concept synthesis
is. Those are profile-declared types; unknown types get the documented generic
fallback (title + body + actions).

The card contract itself (card schema, decision/mailbox protocol, drain
semantics, freshness model) is specified in the design docs; this directory is
its implementation home.

## Status

Seed stage. The real renderer + Pages Functions land after the platform
migration completes. What is here now:

- `reference/cloudflare-spike/` — the validated spike (run 2026-08-07, all
  five checks passed): a single Worker with two routes (`GET /feed`,
  `POST /decide`) over one D1 database holding the card outbox and the
  decisions mailbox, plus a sample card and the drain-side consumer script.
  Kept as the reference implementation the Pages app will be built from.
  Secrets were never in the repo — the Worker reads `FEED_KEY` / `PUSH_KEY`
  from its environment.

## Invariants (load-bearing, from the design)

- **The brain is the sole source of record.** Cards are derived views with
  action affordances; the decisions mailbox is the only place information ever
  lives outside the brain, and only transiently.
- **D1 holds the card outbox and the decisions mailbox. Never raw brain
  content.** Enforced in the syncer (the single writer): schema validation,
  field allowlist, body size cap, no raw page bodies.
- The contract is publisher-agnostic: Cloudflare Pages+D1+Access is the
  default; a tailnet adapter serves the same two routes from a local process.
