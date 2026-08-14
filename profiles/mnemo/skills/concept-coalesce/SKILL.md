---
name: concept-coalesce
description: >
  Read the concept-stub notes and the existing concept layer together, cluster
  the stubs that point at the same idea, and propose promoting a coalesced
  cluster to a real concept (or hypothesis) page. The promotion-shaped,
  non-culling counterpart to GBrain's concept-synthesis — capture cheap, decide
  later. Runs as a rem-cycle phase (weekly) or standalone ("coalesce the
  concepts").
triggers:
  - "coalesce the concepts"
  - "coalesce concept stubs"
  - "which stubs should become concepts"
  - "promote my concept stubs"
---

# concept-coalesce — from stubs to durable concepts

The concept-stub pipeline (`conventions/concept-stub-capture.md`) files cheap,
verbatim `note` pages for transient ideas — a lens, a framing, a bet — that may
later coalesce. This skill is the **decide later** half: it reads the stubs
alongside the concept layer and *proposes* (never auto-executes) promoting a
stub cluster into a real page, now that the recurrence is visible.

It is promotion-shaped, not culling-shaped: a stub that never coalesces is left
in `notes/`, untouched. There is no reaping pass, no delete, no merge tax. The
wager is that Deferring judgment until the recurrence is visible produces better
concepts than judging a single mention at capture — and that a cheap stub that
goes nowhere deserves no cleanup cost.

> **Conventions:** `concept-stub-capture.md` (what a stub is, the
> `is_concept_stub: true` marker, the homes), `rem-cycle-contract.md` (the
> phase result, propose-tier — synthesis always proposes, never auto-executes),
> `synthesis-layer-pages.md` (the concept/hypothesis anatomy the promotion
> promises to author), `graph-and-links.md` (forward-only edges),
> `quality.md` (the notability/"so what" gate). Character: `SOUL.md` — no
> fabricated confidence; a cluster with no real recurrence is reported as such,
> not dressed up.

## Capabilities

`brain-read`, `brain-search` (semantic + keyword clustering), `brain-write` —
but only to propose, never to author a page. Universal; no external I/O.

## What this guarantees

- **Read-only against `concepts/` and `notes/`.** This skill proposes
  promotions; it never authors a `concept` or `hypothesis` page in-place. The
  standing grant (`rem-cycle-contract.md`) is explicit: synthesis always
  proposes, never auto-executes.
- **Recurrence is the bar.** A stub is promoted only when it *coalesces* — at
  least two independently-generated signals point at the same idea (two stubs,
  or a stub + an existing under-developed concept, or a stub cluster + a paper
  with no concept edge). A lone stub is reported, never promoted.
- **Honest no-op.** Most runs correctly produce nothing. That is success, not
  failure (`intersect` shares this posture).
- **Distinct from `intersect`.** `intersect` proposes a *hypothesis* from a
  cross-concept Frontier-bet intersection; this skill proposes a *concept* (or
  single-idea hypothesis) from a stub cluster. They sit adjacent in the weekly
  schedule and never claim the same target.

## Phases

1. **Select.** Enumerate every `notes/*.md` with `is_concept_stub: true` plus
   every `concepts/*.md` (to check overlap and under-developed nodes). The
   stub set is the input; the concept layer is the reference. Grep the corpus —
   this is a cheap scan, unbudgeted.
2. **Cluster.** Group stubs by the idea they point at. Use forward-link
   proximity (stubs linking the same `papers/` or `concepts/` page), title /
   verbatim-trigger overlap, and one `brain-search` pass for semantic
   neighbours. A cluster is ≥2 signals for one idea.
3. **Classify each cluster.**
   - **Promote-to-concept** — a lens/framing with real recurrence and a
     "so what": will the mind or your human reference this again, does it sit on a
     `RESEARCH.md` thread. Propose authoring a `concept`.
   - **Promote-to-hypothesis** — a testable claim, not just a lens. Propose a
     `hypothesis` (with a discriminating test in the outline).
   - **Under-developed-concept** — the cluster points at a `concept` that
     already exists but is thin; propose a `restructure-thin-page` enrichment,
     not a new page.
   - **No-coalescence** — a lone stub, or a cluster that fails the "so what".
     Report in `metrics.no_ops`; leave the stub in place.
4. **Propose.** For each promote cluster, write a `QUEUE.md` proposal
   (`rem-cycle-contract.md`): `category: synthesis`, `kind: concept |
   hypothesis`, `sources: [<stub slugs + source pages>]`, an `outline:`,
   `coherence: tight | loose`, and dedup against `QUEUE.md` and `decisions.yaml`.
   Fold-links are recorded in the proposal so approval can wire the promotion
   (stub → `status: promoted`, `links:` onto the new page).
5. **Return** the phase result (below) or, standalone, a conversational summary.

## As a rem-cycle phase

A weekly phase (5c). The orchestrator passes `mode`; this skill returns the
fenced-yaml phase result:

- **Mode:** this skill is propose-only — `dry-run` and `normal` are identical
  for it (nothing is ever auto-committed). It writes `proposed[]`, never
  `committed[]`.
- **`proposed[]`** — the QUEUE items (`category: synthesis`), highest-salience
  first, each with `sources`, `outline`, `coherence`, and the fold-links.
- **`metrics`** — `stubs_scanned`, `clusters_found`, `promotions_proposed`,
  `under_developed_proposed`, `no_ops`.
- **No cursor** — this phase scans the current stub set each week; it is
  stateless and idempotent (a cluster already queued is deduped away).

## Output

- **QUEUE proposal** — one checkbox line per `rem-cycle-contract.md`, e.g.
  `- [ ] \`a3f2\` **synthesis** · concepts/<slug> ← notes/a + notes/b + papers/c
  · conf 0.7 · outline …`
- **Standalone** — a conversational summary: clusters found, what each promotes
  to, what stayed a lone stub.

## Anti-patterns

- Authoring a `concept`/`hypothesis` page in-place — synthesis always proposes.
- Promoting a lone stub with no second signal — recurrence is the bar.
- Running a cull/merge-reap over stubs — leave the un-coalesced ones alone.
- Overlapping `intersect` — this skill is concept-from-stubs; `intersect` is
  hypothesis-from-concept-intersections.
- Dressing a thin cluster up as "real recurrence" to justify a promotion — the
  no-op is honest.
- Fetching anything — this skill consolidates the graph, it never reaches outside.
