---
name: funding-sweep
description: Standing funding-opportunity scan — reads FUNDING-PROFILE.md (the lab's research translated into funder vocabulary, plus eligibility and indirect-cost facts), scans tiered sources (NIH + grants.gov, named foundations, a general net) for opportunities that fit the lab, hard-filters on fit × eligibility × feasibility, and returns a ranked shortlist. Stateful (dedupes surfaced opportunities); the weekly profile regeneration is gated through QUEUE.md. Invoked by `briefing`; also runs on request.
triggers:
  - "funding sweep"
  - "any new funding opportunities"
  - "what grants should I look at"
  - "scan for funding"
  - the scheduled morning brief (invoked by `briefing`)
---

# funding-sweep — the standing funding-opportunity scan

Where `literature-sweep` scans for *publications* that touch the research program,
this skill scans for *funding opportunities* that fit the lab. It sits between the
two standing-scan patterns already in the brain:

- Like `literature-sweep`, it is **profile-driven** — no named target; it derives
  its interest profile from persisted state and returns a ranked shortlist.
- Like `monitor-the-situation`, it is **stateful** — it remembers which
  opportunities it already surfaced (`seen-ids`), so a live R01 NOFO does not
  re-pitch every morning.

It is **not** `monitor-the-situation`. That skill watches for *named, specific*
things Bryan is already waiting on ("tell me when the Bio Genesis RFA drops"). This
skill scans the whole firehose and judges *what fits the lab* — a fundamentally
different, higher-dimensional relevance call. When both would surface the same
opportunity, this skill **defers** (see Dedupe).

> **Conventions:** `conventions/funding-sources.md` (the shared open-API source
> layer — the endpoints live there, not here), `conventions/brain-first.md` (don't
> re-pitch what's already funded/being pursued), `conventions/quality.md` (every
> item lands with a resolvable link), `_output-rules.md` (deterministic links, no
> slop), `conventions/rem-cycle-contract.md` (the QUEUE.md format the gated
> regeneration writes into), `conventions/capabilities.md` (the harness contract).

## Capabilities

- **Required:** `read-file`, `edit-file`, `fetch-url`.
- **Optional:** `brain-search` / `brain-read` (to check whether an opportunity is
  already funded or being pursued, and to justify profile regeneration from brain
  activity), `user-model-query` (Bryan's priors sharpen the relevance bar),
  `browser-render` (the JS-rendering browser stack — Tier-2 Gates/Grand Challenges
  needs it; degrade to skipping that one source when unavailable).
- **Hermes-only:** `deliver-message` — folded into `briefing` for delivery. Standalone
  invocation returns the shortlist as text. Under a harness without delivery it still
  composes the shortlist and updates `FUNDING-PROFILE.md` state.

## What this guarantees

- **The profile is the single source of truth.** `FUNDING-PROFILE.md` at vault root
  (operational state — no `kind`, excluded from the graph) holds the funding areas,
  eligibility facts, indirect-cost table, negative constraints, and named
  foundations. The sweep never invents an interest the profile does not support.
- **A flagged call deserves serious consideration.** The relevance bar is high and
  multi-dimensional (below). Clearing it means "worth real writing effort," not "keyword
  matched." Most hits do not clear it. Silence is an acceptable — expected — result.
- **Stateful dedupe.** Diff on stable opportunity IDs (`conventions/funding-sources.md`).
  A surfaced opportunity is added to `seen-ids` and never re-pitched.
- **Read-only against the brain.** The sweep writes only `FUNDING-PROFILE.md` state
  (and, on the weekly cadence, proposals into `QUEUE.md`). When a call clears the bar
  it flags "→ worth a grant-plan" and Bryan decides; opening the engagement is
  `grant-plan`, a separate skill and a separate decision.
- **Honest source tiers.** Tier 1 (federal APIs) is reliable; Tier 2 (named
  foundations) is best-effort and labeled as such; Tier 3 (general net) is a wide,
  lower-precision catch-all explicitly flagged "verify eligibility yourself."

## The relevance bar — a weighting, not a checklist

Clearing the bar means the opportunity is worth serious consideration for a
submission. It is the product of several dimensions — a hard fail on eligibility
kills it; the rest trade off against each other:

- **Fit** — does it fund what the lab actually does (Block A funding areas)? This is
  the dominant term. An *extraordinary* fit justifies extraordinary effort.
- **Eligibility (hard gate)** — PI status, mechanism, geography, and indirect-cost
  cap (Block B, C). A call restricted to early-career, or a foundation whose indirect
  cap the institution cannot accept, fails outright. Fail here → dropped, not weighted.
- **Deadline feasibility — a weighting, NOT an auto-defer.** Do **not** reflexively
  push a good call to "next cycle" because the deadline is close. An extraordinarily
  good fit is worth an extraordinary two-week push; a marginal fit is not worth a
  last-minute scramble. Weigh fit magnitude against time remaining. Only an
  *objectively impossible* timeline (due tomorrow, due today) auto-defers — and even
  then, surface it as "impossible this cycle, note for next" rather than dropping it
  silently. When a great-fit call has a tight-but-possible deadline, say so loudly:
  "T-14, tight, but the fit warrants the push."
- **Effort vs. reward** — award size against writing burden (Block B soft floor). A
  tiny award with a full R01-scale application is a poor trade unless fit is
  exceptional.
- **Non-duplication** — not already funded, not already being pursued, not already
  watched by `monitor-the-situation`. Check the brain and `MONITORS.md`.

## Dedupe — against the brain, active grants, and MONITORS.md

Before surfacing a hit:
1. Is it in `seen-ids`? → already surfaced, drop.
2. Is a `grant` page already targeting it, or is the lab already funded for this? →
   `brain-search`; if yes, drop.
3. Is `monitor-the-situation` already watching this specific opportunity
   (`MONITORS.md`)? → **defer to the monitor**; it owns the named watch. Do not
   double-report.

## Source tiers

The federal endpoints and their query/diff discipline live in
`conventions/funding-sources.md` — read it; do not restate the endpoints here.

**Tier 1 — federal (reliable).** NIH Guide + grants.gov for opportunities; NIH
RePORTER for fit context ("who already holds funding here"). Build queries from Block
A funding-area terms. Apply the phrase-matching discipline from the convention
(word-boundary title filtering — never bare substring). Bound to the recency window
(last sweep → now).

**Tier 2 — named foundations (best-effort, labeled).** The foundations in Block E.
No unified API — each is a per-source RFP-page check, brittle by nature. The three
named sources need **three different extraction patterns** (confirmed by live trial —
see Block E for the specifics):
- **Gates** → open calls are at Grand Challenges, a JS-rendered app behind
  Cloudflare Access. **Requires the browser stack**, not `fetch-url`. When it can't
  be rendered, say so — do not return empty silently.
- **Burroughs Wellcome Fund** → plain `fetch-url` on the index works, but deadlines
  need a **two-hop crawl** (index → per-program detail page). Lean on the Block B
  career-stage auto-drop; most BWF programs are early-career-gated and fail eligibility
  before extraction even matters.
- **Keck** → **timeline-watch, not call-scan.** Read the grant-cycle timeline and
  surface the nomination-window state; Keck has no open-call list to scrape.
Label every Tier-2 hit as best-effort. When a foundation site has redesigned and the
fetch/render yields nothing parseable, say so plainly ("Gates challenges page didn't
render — needs a look") rather than silently returning empty.

**Tier 3 — general net (wide, lower precision, flagged).** grants.gov across all
agencies (NSF, DOD, DOE, other) plus any smaller foundations not named in Block E.
Looser matching, so precision is lower — every Tier-3 hit is explicitly flagged
"wider net — verify eligibility and fit yourself."

## The indirect-cost check (foundations only)

For any **foundation** hit (Tier 2 or Tier 3), consult Block C before surfacing:
- Funder in the table as ELIGIBLE (Gates) → surface normally.
- Funder in the table as INELIGIBLE (CZI) → auto-drop; add to `seen-ids` so it does
  not re-surface.
- Funder not in the table → surface, but **flag**: "verify indirect-cost cap before
  investing writing time — the institution needs full/high F&A recovery." Federal and industry
  hits skip this check entirely.

## Phases

1. **Read the profile.** Read `FUNDING-PROFILE.md` — funding areas (Block A),
   eligibility facts (B), indirect table (C), negative constraints (D), named
   foundations (E), and `state` (last-swept, seen-ids). Build query terms from Block A.

2. **Sweep the tiers.** Tier 1 (federal APIs, per `conventions/funding-sources.md`),
   then Tier 2 (named foundations), then Tier 3 (general net). Bound Tier 1 to the
   window since `last-swept`. Collect `{id, title, funder, mechanism, deadline, url,
   tier}` per hit.

3. **Filter and judge.** For each hit: apply the eligibility hard gate (B), the
   indirect check for foundations (C), the negative constraints (D), and the dedupe
   chain. Then weigh what survives against the relevance bar. Most hits do not clear
   it — that is correct.

4. **Rank and shortlist.** Order survivors by fit magnitude first, then feasibility.
   A handful is a good sweep. Mark each hit's tier and, where relevant, its flags
   (indirect-verify, geography, Keck-nomination, tight-deadline-but-worth-it).

5. **Update state — carefully.** Re-read `FUNDING-PROFILE.md` immediately before
   writing (Bryan may have hand-edited during the run — never blind-overwrite,
   `SOUL.md` §2). Append all surfaced and auto-dropped IDs to `seen-ids`; set
   `last-swept` to today; write the ranked shortlist to `last-surfaced` (date +
   items) so `briefing` can read it without re-running the sweep. On a quiet sweep,
   set `last-swept`, leave `seen-ids` unchanged if nothing new was seen, and set
   `last-surfaced.items: []` with today's date — an explicit "swept, nothing surfaced."

## The weekly profile regeneration (Block A) — gated

On a slower cadence (weekly, aligned with the synthesis briefing), regenerate the
Block A funding areas from actual brain activity — recent paper ingests, active
`project` pages, in-flight `grant` pages, `RESEARCH.md` threads. Compare against the
current Block A and **propose** changes:
- an area to add (new active thread not yet represented),
- an area to drop (no brain activity in ~6 months),
- a reframing (a thread whose funder vocabulary has shifted).

Write proposals into `docs/rem-cycle/QUEUE.md` in the standard format
(`conventions/rem-cycle-contract.md`), so `synthesis-briefing` surfaces them under
"Awaiting your call" and Bryan confirms or declines. **Never auto-apply a Block A
change** — a silently drifting profile starts flagging junk, and the whole value is
that a flagged call is trustworthy. Set `last-regenerated` after proposing.

```markdown
## <YYYY-MM-DD> (funding-profile)
- [ ] **funding-area** · FUNDING-PROFILE.md → add "structural vaccinology / immunogen design"
      · conf 0.7 · _basis: 4 immunogen-design paper ingests since last regen; [[projects/...]] active_
- [ ] **funding-area** · FUNDING-PROFILE.md → drop "B-cell aging" — no brain activity since 2026-01
      · conf 0.6 · _basis: no paper ingest or project edit touching the area in ~6 months_
```

## Output

A ranked shortlist, returned to the caller — `briefing` folds it into the brief near
the DEADLINES surface (funding is deadline-bearing); a direct request gets it as
delivered text. Not a brain page.

```
FUNDING OPPORTUNITIES — sweep {date}

- {title} — {funder}, {mechanism}
  {one line: why this clears the bar — the funding area it fits, the fit magnitude}
  Deadline: {date} (T-{N}){, tight but worth the push — if applicable}
  {flags: [Tier 2 best-effort] / [Tier 3 — verify yourself] / [verify indirect cap] / [Keck: internal nomination] / [foreign — confirm no legal difficulty]}
  {resolvable URL — grants.gov opp, NIH Guide notice, foundation RFP}
  → worth a grant-plan — your call
```

A standout opportunity is flagged "→ worth a grant-plan," not acted on — Bryan
decides, and `grant-plan` reads the NOFO and runs the Aims go/no-go. The sweep itself
opens no engagement.

## The driver and the briefing contract

**One driver owns state.** funding-sweep is stateful (`seen-ids`), so exactly one
process may run it per cycle — otherwise the first run consumes the new hits into
`seen-ids` and the second returns empty. The **daily cron is the sole driver.** It
runs the sweep, updates `seen-ids` / `last-swept`, and writes the shortlist to
`last-surfaced`.

**`briefing` reads, never re-runs.** Unlike `literature-sweep` (stateless, spawned
by briefing), funding-sweep follows the `monitor-the-situation` pattern: `briefing`
reads `last-surfaced` from `FUNDING-PROFILE.md` and folds those items into the
DEADLINES surface. It does **not** spawn the sweep. If `last-surfaced.date` is stale
(older than ~2 days — the cron failed), briefing says so rather than presenting old
hits as fresh.

**Current scope: Tier 1 only.** The wired cron runs **Tier 1 (federal APIs) only**.
Tiers 2–3 (foundations, general net) are not yet reliable enough to schedule — they
run only on explicit manual invocation until their extraction is trusted, at which
point the cron scope widens. A cron-driven sweep that hits an untrusted tier and
returns junk would poison the attention contract; keeping the scheduled path to the
reliable tier is deliberate.

## Anti-patterns

- Sweeping without reading `FUNDING-PROFILE.md` — a profile-less sweep is a noise
  generator.
- Auto-deferring a great-fit call to "next cycle" because the deadline is close — an
  extraordinary fit is worth an extraordinary push; only an objectively impossible
  timeline auto-defers.
- Re-pitching an opportunity already in `seen-ids`, already funded, already in a
  `grant` page, or already watched by `monitor-the-situation`.
- Auto-dropping an unknown foundation on indirect grounds instead of flagging it for
  verification — the table compounds by resolving unknowns, not by guessing.
- Treating Tier-2/Tier-3 hits as reliable — label best-effort and wide-net hits
  honestly.
- Auto-applying a Block A profile change instead of proposing it through QUEUE.md —
  the regeneration is gated by design.
- Returning every hit instead of a hard-filtered shortlist; padding a quiet sweep.
- Auto-creating `grant` pages — the sweep is read-only against the brain; opening an
  engagement is `grant-plan`.
- Blind-overwriting `FUNDING-PROFILE.md` — re-read before writing; edit only the
  `state` block; never clobber Bryan's hand-edited facts.
- Restating the federal endpoints here instead of citing `conventions/funding-sources.md`
  — the source layer is shared to prevent drift.
- Running the sweep from both a cron and `briefing` — the double-run consumes new
  hits into `seen-ids` on the first pass and the second returns empty. The cron is
  the sole driver; briefing reads `last-surfaced`.
- Scheduling Tiers 2–3 before their extraction is trusted — the cron runs Tier 1
  only; untrusted tiers on an unattended path poison the attention contract.
