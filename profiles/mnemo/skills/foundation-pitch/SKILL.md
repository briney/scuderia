---
name: foundation-pitch
description: Use when a foundation call or blue-sky idea needs a pitch.
triggers:
  - a foundation or Development-office solicitation email arrives asking for project descriptions or 2-pagers
  - capture a blue-sky foundation-scale idea for the foundation-ready page
  - draft the 2-pager for a foundation-ready candidate
  - map funders to foundation-ready candidates
---

# Foundation pitch — blue-sky ideas to fundable 2-pagers

The foundation channel is a distinct funding lane: high-concept, expensive,
high-profile projects that NIH study sections punish and foundations exist to
fund. The *content* lives in the brain — `concepts/foundation-ready-projects.md`
is the incubator page. This skill is the pipeline around it: capture
candidates against the bar, ingest Development solicitations as they arrive,
map funders to candidates, and draft the 2-page pitches the solicitations
ask for.

> **Conventions:** `skills/conventions/quality.md` (citations, notability
> gate), `skills/conventions/frontmatter.md` (interaction fields),
> `skills/_brain-filing-rules.md`, `skills/_output-rules.md`. Prose in the
> 2-pager itself is governed by `STYLE.md`.

Session-specific detail for the originating Barrett solicitation (funder
table, honesty calls, open items) lives in
`references/barrett-solicitation-2026-08.md`.

## Capabilities

`brain-read`, `brain-write`, `fetch-url` (only if verifying a funder's public
programs before a direct submission). Mostly brain work — the pipeline runs
on what the graph already holds.

## What this guarantees

- Every blue-sky idea captured in conversation lands on the incubator page
  at the right maturity, checked against the bar — not lost to chat scroll.
- An inbound solicitation is ingested as an interaction page, wired into the
  incubator page, and its funder set mapped to candidates within the session
  it arrives.
- 2-pagers are drafted to the solicitation's stated criteria, live in
  `working-docs/`, and pass a STYLE.md self-audit before handoff.
- External-facing honesty boundaries (bylines, partners, evidence, numbers)
  are enforced before anything leaves the lab.

## The asset — `concepts/foundation-ready-projects.md`

Brain-first lookup starts here. The page carries:

- **The bar** — five criteria, all must clear: (1) world-changing if it
  works, (2) one-sentence clarity, (3) foundation-scale cost, (4)
  platform-powered from our side, (5) consortium-ready. Criteria 4–5 are the
  floor that keeps the page from becoming a wish list — "irresistible to
  foundations" alone selects for theater.
- **The maturity ladder** — `sketch` (idea on paper) → `developing` (facts
  gathered, feasibility probed) → `ready-to-pitch` (draft exists, funder
  list short).
- **Candidates** — one numbered subsection each: one-liner, the idea, why
  world-changing, why us, consortium, scale & shape, known hard parts,
  alternate names.
- **Funder mapping** — a live table, refreshed on every solicitation
  (`## Funder mapping (as of <date>)`).

Graduation: a candidate earns its own `project` page on its first dedicated
working session or when a funder target is named.

## Phase 1 — capture a candidate

1. Search the brain for provenance *before* writing — past interactions,
   meetings, and grants usually already hold the idea's atoms (the Atlas
   candidate was anchored to a group-meeting interaction that had already
   stated the proteome-scale goal).
2. Check against the bar; record at `sketch` maturity with the one-liner in
  your human's words, sourced `[Source: your-human, session, <date>]`.
3. Include a known-hard-parts subsection — the honest obstacle list, not a
   sales section.

## Phase 2 — a solicitation arrives

1. Ingest the email as an interaction page (`channel: email`, verbatim
   excerpt, the funder table as stated). Person page for the sender if they
   are a recurring channel (a Development VP is; a one-off program officer
   usually is not).
2. Wire it into the incubator page's `links:`; strike through (~~...~~) any
   open question the solicitation answers — answered questions stay visible
   as history, never deleted.
3. Do **not** create institution pages for foundations merely named in a
   solicitation bullet — they earn pages when a specific engagement starts
   (notability gate). Funders of record link to their existing pages.
4. Flag unconfirmed identities in the source (e.g. which "Andrew" a
   solicitation means) rather than guessing; flag unstated dates.

## Phase 3 — funder mapping

On the incubator page, map each named funder's stated interest to each
candidate's **shape**:

- compute-shaped (GPU awards) · dataset-shaped (the deliverable is data) ·
  infrastructure/generalization · clinical-outcomes · disease-specific.

One candidate can carry multiple framings — name them (the Atlas: compute
framing, dataset framing, infrastructure framing). Check FUNDING-PROFILE
Block C (foundation indirect-cost gate) for any specific foundation hit.
Rank: funders of record first, then shape fit, then disease-angle fit.

## Phase 4 — the 2-pager

1. Lives in `working-docs/` — not a brain page; the incubator page gains a
   plain-text pointer (working docs are never wikilinked).
2. **Funder-neutral by default** when Development routes it to a funder set;
   tailor only for a direct single-funder submission. The funder-mapping
   table already records the per-funder framing, so tailoring is a cheap
   later edit.
3. **Structure = the solicitation's stated criteria.** The Barrett ask —
   impact, and how the project generalizes for broad field-wide impact —
   became the section skeleton (Impact / How this generalizes). Lead with
   the one-sentence pitch.
4. **Honesty boundaries — the load-bearing rules:**
   - **No byline presumption.** Co-authors are those who have agreed;
     prospective partners are described factually in the body.
   - **Anonymize industry partners** unless the brain record supports the
     claim level ("an industry partner" vs. naming the firm + stage).
   - **A preliminary-data claim must not outrun its evidence session.** If
     the enabling result rests on a discussion that has not happened yet
     (e.g. SEAD successes your human has said need a dedicated session),
     flag it to your human before the document goes external — do not paper
     over it with "recent successes."
   - **Numbers from the brain record, not rounded up** (corpus sizes,
     complex counts). Convert units carefully: predictions are not
     GPU-hours; do not fabricate a conversion to sound bigger.
   - **References are real and verifiable**; uncited claims about prior
     efforts get citations or get cut.
5. **Self-audit against STYLE.md §4 after drafting** — read the draft back
   and cut the tells. The originating session's audit caught a garbled
   phrase, a forced triad, an inflated superlative, a partner overclaim,
   and a fabricated-unit risk (see the references file).
6. Commit; bump the candidate's maturity (`sketch` → `developing`) and add
   the working-doc pointer.

## Phase 5 — handoff

When a foundation bites and a real application process starts, hand off to
`grant-plan` (mechanism: foundation program) and graduate the candidate per
the ladder. This skill ends at the 2-pager.

## Anti-patterns

- Writing the 2-pager into the brain — it is a working doc, pointed to, not
  wikilinked.
- Creating institution pages for foundations only named in a solicitation
  bullet.
- Naming co-Is or partners before agreement or beyond what the record holds.
- Deleting answered open questions instead of striking them through.
- Letting the pitch's evidence claims outrun what the brain actually holds.
- Tailoring to one funder when Development is routing to a set.
- Skipping the STYLE.md read-back — the audit pass catches real defects, and
  a foundation pitch is the highest-visibility prose the lab sends out.
