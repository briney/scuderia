---
name: monitor-the-situation
description: Standing change-detection watch — maintains MONITORS.md, a hand-editable watchlist of specific things your human is waiting on (a funding call that will drop, a policy that will publish), and on a daily cadence checks each active item against structured open-API sources, judges whether anything genuinely changed, and notifies only on a significant new hit. Stateful by design; silence is the default.
triggers:
  - "monitor the situation"
  - "watch for X"
  - "keep an eye on X"
  - "add a monitor"
  - "notify me when X happens"
  - the scheduled daily monitor sweep
---

# monitor-the-situation — the standing change-detection watch

Where `literature-sweep` runs a *stateless* scan — it re-derives its interest
profile from `RESEARCH.md` every run and re-filters against the brain — this
skill is **stateful by design**. Its entire value is detecting *change*, which
is impossible without remembering what it saw last time. The memory lives in
`MONITORS.md`; the skill diffs current state against it, judges what changed, and
notifies only when a change clears the item's own significance bar.

The distinction that makes this a mind job and not a dumb diff tool: the
skill does not fire on *any* delta. It reads what changed and judges it against
the item's `significant-means` criterion — "a DOE Genesis FOA already existed and
is not what we're waiting for; an NIH Bio Genesis RFA is." A diff tool cannot
make that call; the mind can.

> **Conventions:** `skills/conventions/brain-first.md` (don't re-pitch what the brain
> already holds), `skills/conventions/quality.md` (every notified item lands with a
> resolvable citation), `skills/conventions/funding-sources.md` (the shared open-API source
> layer — endpoints, query params, diff keys), `_output-rules.md` (deterministic
> links, no slop), `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

- **Required:** `read-file`, `edit-file`, `fetch-url`.
- **Optional:** `brain-search` (to check whether a hit is already known).
- **Hermes-only:** `messaging-send` / `deliver-message` — the notification is
  the point. Under a harness without out-of-band delivery this skill still runs
  the sweep and updates `MONITORS.md`, but says plainly it cannot push a
  notification; findings are legible in the file and git history.

## What this guarantees

- **The watchlist is the single source of truth.** One file, `MONITORS.md` at
  vault root — operational state, not a brain page (no `kind`, no page
  directory, excluded from the graph). Hand-editable, git-tracked so its own
  history is the audit log. The sweep never invents an item the file does not
  hold.
- **Change detection diffs on stable IDs, not page text.** Each item stores the
  identifiers it has already seen (Federal Register document numbers, grants.gov
  opportunity numbers). A "new" hit is an ID not in `seen-ids`. This is what
  keeps a page-churn or a re-run from crying wolf.
- **Silence is the default.** A quiet day updates `last-checked` and writes
  nothing else. Most days, most items produce nothing. That is correct — an
  alert that fires on noise gets muted, and a muted monitor is worthless.
- **Every notification carries a resolvable link** — the FR document URL, the
  grants.gov opportunity, the NIH Guide notice. Never a reconstructed guess.
- **The file is the only thing this skill writes.** It does not create brain
  pages. When a hit is worth a `grant` or `paper` page, it flags it for your human;
  ingestion is a separate skill and a separate decision.

## The watchlist — MONITORS.md

One markdown file at vault root, one `##` block per monitored item. The fields
above `state:` are your human's (hand-editable); everything under `state:` is
Mind-maintained.

```markdown
## <human title of what we're waiting on>
- id: <stable-slug>
- type: search-watch
- status: active                    # active | paused | resolved | cancelled
- lifecycle: until-cancelled        # auto-resolve | indefinite | until-cancelled
- routing: both                     # briefing-only | immediate | both
- cadence: daily
- significant-means: >
    <explicit, in-words criterion for what counts as a significant change —
    the bar the mind judges each new hit against>
- sources:
    - federal-register: term="..."; agencies=...
    - grants.gov: keyword="..."
    - nih-guide: keyword="..."
- state:
    last-checked: <YYYY-MM-DD | never>
    seen-ids: [<ids already observed — baseline seeded so known-existing hits never fire>]
    last-fired: <YYYY-MM-DD | never>
```

### The three field groups

**Identity & bar** — `id`, `type`, `significant-means`. The criterion is the
heart of the item: it is what the mind judges against, in plain words, so a human
reading the file knows exactly what would trip the wire.

**Behavior** — `status`, `lifecycle`, `routing`, `cadence`:

- `lifecycle` governs what happens when the item fires:
  - `auto-resolve` — notify once, set `status: resolved`, stop checking. Use for
    a one-shot event ("the paper posts").
  - `until-cancelled` — notify, keep watching. Use when the event has a
    *staggered rollout* — one announcement is not the last, so the watch stays
    live until your human sets `status: cancelled`. (The Bio Genesis Mission is this:
    funding calls will drop over time, not all at once.)
  - `indefinite` — never self-terminates; a standing watch with no expected
    end.
- `routing` decides where a significant hit goes — decided per item:
  - `immediate` — push a Telegram notification the moment it's found.
  - `briefing-only` — write nothing out-of-band; `briefing` folds it into the
    next daily brief (it reads `last-fired` / unreported hits from `MONITORS.md`).
  - `both` — fire immediately *and* let it appear in the brief.

**State** — mind-maintained. `last-checked` bounds the query window;
`seen-ids` is the diff baseline; `last-fired` lets `briefing` tell reported from
unreported hits.

## The search-watch mechanism

Auth-free JSON APIs, the same discipline as `literature-sweep` — no code, the
endpoints are the prose. **The source layer is shared with `funding-sweep` and lives
in `skills/conventions/funding-sources.md`** — the Federal Register, grants.gov, NIH Guide,
and NIH RePORTER endpoints, their query parameters, their stable diff keys, and the
phrase-matching discipline. Read that convention for the mechanics; this section
covers only what is specific to a *named watch*.

The discipline that matters here: run two query strengths for the same item — an
**exact-phrase tripwire** (`"Bio Genesis Mission"`) that today returns zero, so
non-zero *is* the event, and a **broader agency-filtered net** (`"Genesis Mission"`
+ NIH/HHS agency slugs) that catches items phrased differently. Run both; judge every
new hit against `significant-means`.

Apply the convention's phrase-matching rule without exception: match
`\bgenesis mission\b` / `\bbio[\s-]?genesis\b` (case-insensitive) against the title,
never the bare substring "genesis" — a bare-substring filter fires on
`patho·genesis` (e.g. the NIH HIV/NIDDK notice PAR-25-068, "...HIV Pathogenesis..."),
a false positive that looks exactly like a real NIH hit. Known-existing,
not-what-we-want opportunities (e.g. the DOE FOA `DE-FOA-0003612`, "The Genesis
Mission: Transforming Science and Energy with AI") are seeded into `seen-ids` as
baseline so they never fire; the target is an NIH/HHS "Bio Genesis" solicitation.

## Phases

1. **Read the watchlist.** Read `MONITORS.md`. Take only items with
   `status: active` whose `cadence` is due (daily items every run). Skip
   `paused` / `resolved` / `cancelled`.

2. **Sweep each item's sources.** For each active item, run its configured
   queries with `fetch-url`, bounded by `last-checked` where the source supports
   a date filter. Collect current `{id, title, url, date}` per source.

3. **Diff and judge.** For each source, `new = current_ids − seen-ids`. For each
   genuinely new hit, judge it against the item's `significant-means` — this is
   the editorial call, not a mechanical delta. Optionally `brain-search` to
   confirm it is not already known. A new ID that does not clear the bar (wrong
   agency, wrong program, a mention not a solicitation) is *seen but not fired*:
   add it to `seen-ids` so it never re-surfaces, but do not notify.

4. **Fire what clears the bar.** For each significant new hit, act on `routing`:
   `immediate` / `both` → compose and send a Telegram notification now;
   `briefing-only` → record it for `briefing` to fold in. Set `last-fired` on the
   item.

5. **Apply lifecycle.** If the item fired and `lifecycle: auto-resolve`, set
   `status: resolved`. `until-cancelled` and `indefinite` stay `active`.

6. **Update state — carefully.** For every item swept (fired or not), append all
   new IDs to `seen-ids` and set `last-checked` to today. **Never blind-overwrite
   `MONITORS.md`** (`SOUL.md` §2): re-read it immediately before writing in case
   your human hand-edited it during the run, and apply targeted edits to the state
   blocks only — never rewrite his fields. On a quiet sweep, the only change is
   `last-checked`.

## The notification

Sent to Telegram for `immediate` / `both` hits. Short, factual, one hit per
block, every claim carrying its resolvable link:

```
MONITOR — {item title}

{what changed, one line — the significant new hit}
{agency / program} · {date}
{resolvable URL — FR document, grants.gov opp, NIH Guide notice}

{if worth a brain page: "→ worth a grant-ingest / paper-ingest — your call"}
```

No preamble, no "I found." If several items fire in one sweep, one message with
a block each. Silence when nothing clears the bar — do not send an "all quiet"
message; the absence is the signal.

## Adding or changing a monitor

When your human asks to watch something new, add a `##` block to `MONITORS.md`.
Pin down, with him, the fields that need judgment:

- **The sources and queries** — which of the three APIs, and the exact terms.
  Verify the query actually returns something sane before baking it in (a phrase
  that returns thousands of junk hits needs tightening or client-side title
  filtering).
- **`significant-means`** — the explicit bar, in his words.
- **`lifecycle`** — auto-resolve (one-shot), until-cancelled (staggered), or
  indefinite (standing).
- **`routing`** — immediate, briefing-only, or both, decided for this item.
- **Seed `seen-ids`** — run the queries once and baseline the known-existing,
  not-what-we-want hits so the first real sweep does not fire on pre-existing
  noise.

## Anti-patterns

- Firing on any delta instead of judging it against `significant-means` — the
  judgment is the whole point; a dumb diff would be worse than nothing.
- Diffing on page text or HTML instead of stable IDs — guarantees false
  positives on trivial churn.
- Sending an "all quiet / nothing new" message — silence is the signal; a daily
  no-op ping trains your human to ignore the channel.
- Blind-overwriting `MONITORS.md` — re-read before writing; edit only the state
  blocks; never clobber your human's hand-edited fields.
- Not seeding `seen-ids` — the first sweep then fires on everything that already
  exists.
- Inventing an interest the watchlist does not hold, or auto-creating brain
  pages — the sweep writes only `MONITORS.md` and flags page-worthy hits for
  your human.
- Treating `MONITORS.md` as a brain page — it is operational state, same tier as
  `TODOS.md` / `BRIEFING.md`, excluded from the graph.
