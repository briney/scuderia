# interface/pages — the feed Pages app (Cloudflare publisher)

The default publisher for the card feed: a Cloudflare Pages app — static
renderer (`public/`) plus Pages Functions (`functions/`) implementing the
card contract's routes over D1.

This is the only publisher-specific code in soma. The contract is
publisher-agnostic; a tailnet adapter serves the same routes from a local
process.

## Routes

Reader surface (what the settled design calls "exactly two routes"):

- `GET  /feed` — cards for the renderer. Active cards + elapsed snoozes;
  expired and tombstoned cards are excluded.
- `POST /decide` — append a decision to the mailbox. Server-side validation:
  action ∈ {approve, reject, snooze, dismiss}, card exists and is live, item
  exists in the card's stack, no duplicate pending decision (409).

Machine routes (harness; secret-guarded, inherited from the spike contract):

- `POST /push` — upsert a card. Validates schema allowlist + size caps
  before anything touches D1. Also the retention hook: acked decisions are
  deleted after 30 days, tombstoned cards after 7 (piggybacked on writes).
- `GET  /decisions` — read the mailbox (`?status=pending`).
- `POST /ack` — mark a decision `applied` | `superseded` | `flagged`.

## Auth

Two shared secrets, read from env (Pages project secrets — never in the repo):

- `FEED_KEY` — reader. The UI takes it once via `?key=…` and keeps it in
  localStorage; the drain polls with it.
- `PUSH_KEY` — writer. Held only by the harness syncer/drain.

Cloudflare Access (email OTP) layers in front of the reader surface once the
custom domain lands; the key check stays as defense in depth. Per-instance
push credentials are the multi-instance endgame; v1 has one instance.

## Renderer contract

- Dashboard only: cards ordered by salience × recency (server-side).
- Known types: `summary`, `review`, `alert`, `metric`. Unknown types get the
  generic fallback (title + body + actions) — the renderer never learns what
  a "budget" or a "concept synthesis" is.
- Review cards render their item stack; **item IDs are always visible** as
  hash chips (spike UX finding #1). An emptied stack renders its "queue
  clear" empty state — the dashboard is stable, cards don't vanish.
- Gestures: swipe right = approve, swipe left = reject, buttons for
  approve / reject / snooze(3d) / dismiss. The gesture map is printed on
  every empty state so it's discoverable.
- Bodies render a markdown subset (bold, italic, code, links, lists); HTML
  is escaped first. Per-profile accent theming via `data-profile`.

## Deploy

Prereqs: `CLOUDFLARE_API_TOKEN` (scoped: Pages, D1) and the account id.

```sh
# one-time: create the project and bind D1 + secrets
curl -X POST "https://api.cloudflare.com/client/v4/accounts/$ACC/pages/projects" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"name":"soma-feed","production_branch":"main"}'

# bind the D1 database + set secrets (deployment_configs), then deploy:
npx wrangler pages deploy public --project-name=soma-feed
```

`schema.sql` is the authoritative D1 schema; apply it (and any migration
noted at its foot) with `wrangler d1 execute` or the D1 query API.

The spike worker (`reference/cloudflare-spike/`) stays up and untouched —
this app supersedes it without sharing its URL or its keys.
