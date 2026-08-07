---
name: intersect
description: >
  Detect the hypothesis that lives only at the *combination* of two-plus concepts'
  Frontier bets, and propose it to the queue for Bryan to endorse. The
  "connections made" half of the synthesis engine — rigorous, rare, autonomous.
  Runs as a weekly rem-cycle phase or standalone. Most runs correctly produce
  nothing; that is success, not failure.
triggers:
  - "find concept intersections"
  - "any new cross-concept hypotheses"
  - "intersect the concepts"
---

# intersect — the hypothesis that lives between concepts

The counterpart to `reinforce`: where reinforce records how a paper moves *one*
concept, intersect looks for the hypothesis that **no single concept could
produce** — the bet that lives only at the combination of two-plus concepts'
Frontier bets. That is the novelty premium exactly: novelty in the *combination*,
not in either part. When a combination clears the bar it becomes a **proposed
hypothesis** in the proving-ground funnel, for Bryan to endorse or kill.
Autonomous-only — the directed case (Bryan naming a combination) is already manual
hypothesis seeding (Spec 1). Full design:
the instance's private `docs/specs/`.

> **Conventions:** `synthesis-layer-pages.md` (the concept `## Frontier` bets it
> reads, the hypothesis anatomy it proposes), `frontmatter.md` (hypothesis fields —
> `draws_on`, `promise`, `status`; the graveyard `killed_reason`),
> `rem-cycle-contract.md` (the `synthesis` proposal shape, `dry-run`, dedup),
> `graph-and-links.md` (the `related_concepts` edges it seeds on), `quality.md`
> (the notability gate, cite-or-flag). Character: `SOUL.md` — **no fabricated
> confidence: never manufacture an intersection to produce output.**

## Capabilities

- **Required:** `brain-read`, `brain-write` (the QUEUE proposal only).
- **Optional:** `brain-search` (the semantic latent-pair scan; degrades to keyword
  under Claude Code — narrower recall, which the rarity principle already accepts).

Universal; **no external I/O** — intersect combines concepts already in the graph.

## What this guarantees

- **Silence is success.** A true cross-disciplinary hypothesis is uncommon; **most
  runs produce zero candidates, and that is the correct outcome.** The phase never
  lowers the bar or manufactures a candidate to avoid an empty run — a forced
  intersection fails the spine. High precision over recall.
- **Bet-level, novelty-first.** Candidates are Frontier-bet × Frontier-bet, never
  umbrella × umbrella (that yields truisms). A proposal names the specific bets and
  argues the combination exceeds either part.
- **Rigorous three-gate bar.** promise (a concrete Beat / Unlock / Scale / Explain
  case) **and** a nameable discriminating test **and** novelty (not crystallized,
  open, or killed). A candidate failing any gate is dropped, never softened.
- **Graveyard-respecting.** A `status: killed` hypothesis is never re-proposed.
- **Never auto-creates a `hypotheses/` page.** Intersect only proposes to
  `QUEUE.md`; endorsement and crystallization are Bryan's act.
- **Non-destructive, idempotent.** Dedup against `QUEUE.md` **and** `hypotheses/`
  (including killed); `dry-run` until the phase earns trust.

## Phases

1. **Generate candidates** (bet × bet). Three sources, all used:
   - **Seeded** — pairs that already co-occur: shared `related_concepts` edges,
     shared source papers, and the concept map's flagged **tensions** (a tension is
     a first-class candidate — a hypothesis about which side wins).
   - **Semantic** — a bounded scan (rotating cursor over concept-pairs) for *latent*
     bet-pairs that don't already co-occur — the non-obvious connections.
   - **Reinforce hand-off** — a new Frontier spur opened by `reinforce` since the
     last run gets priority screening against existing bets elsewhere.

   Pairs primary; triples only when a bet genuinely needs three concepts.
2. **Gate** — apply the three gates cheapest-fail-first: **novelty + graveyard**
   (drop if crystallized / open / killed) → **promise** (a concrete
   Beat/Unlock/Scale/Explain case) → **discriminating test** (nameable, or discard).
   A candidate that fails any gate is dropped, not softened. The discriminating-test
   gate is the decisive one — the filter Bryan would apply himself; a promising
   combination you cannot design a test for is a story, not a hypothesis.
3. **Propose** — surviving intersections → `QUEUE.md` as `kind: hypothesis`
   proposals (shape in Output).
4. **Return** the phase result — or, standalone, a conversational summary, including
   an explicit **"no genuine intersection this run"** when that is the (common)
   answer.

## As a rem-cycle phase

The **weekly** phase (phase 8; `rem-cycle-contract.md`) — intersections are rarer
and deeper than paper-arrivals, so not nightly. The orchestrator passes `mode`:

- **`proposed[]` only** — `category: synthesis`, `kind: hypothesis`, deduped against
  `QUEUE.md` **and** `hypotheses/` (including `status: killed`). `committed[]` is
  normally empty (intersect writes nothing but the proposal).
- **Cursor** — a rotating cursor over concept-pairs (the semantic scan doesn't judge
  every pair every run); seeded + reinforce-handoff candidates are screened each run
  regardless.
- **Budget** — bounded `read` (candidates judged) and `mutations` (QUEUE appends).
- **`metrics`** — `pairs_screened`, `candidates_gated`, `hypotheses_proposed`,
  `graveyard_skips`.
- **`dry-run` default** until the phase earns trust.

## Output

- **QUEUE proposal** — one entry per surviving intersection
  (`rem-cycle-contract.md`): `**synthesis** · hypotheses/<slug> ← concepts/<a> ×
  concepts/<b>` carrying the **claim**, the **specific bets** combined, the
  **promise** tag(s) + case, the **discriminating test**, a **novelty note**, and
  the sources grounding the promise case.
- **Standalone** — a conversational summary, or a plain "no genuine intersection
  this run" when nothing clears the bar.

## Anti-patterns

- Manufacturing an intersection to avoid an empty run — silence is the correct
  common outcome (`SOUL.md`). Recall is expendable; the bar is not.
- Umbrella-level "these two concepts are related" truisms — the unit is bet × bet.
- Proposing an intersection with no nameable discriminating test — that is a story,
  not a hypothesis.
- Re-proposing a killed hypothesis (graveyard), or one already crystallized / open /
  queued.
- Auto-writing a `hypotheses/` page — intersect only proposes; Bryan endorses.
- Lowering the bar because "nothing was found this run" — the bar is fixed.
- Reaching outside the vault — intersect combines concepts already in the graph.
