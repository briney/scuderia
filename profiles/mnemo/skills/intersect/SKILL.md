---
name: intersect
description: >
  The single-item ranker. Scans the whole brain — concepts, notes, grants,
  papers, everything — and surfaces THE one highest-value cross-cutting attention
  target into the dream report, labeled as opinion. A hypothesis to consider, a
  grant idea, a topic ripe for a deep dive. One item, every run, never a page.
  The "perfect home page": show one thing and you act on it.
triggers:
  - "find concept intersections"
  - "what's the one thing I should look at"
  - "surface the highest-value idea"
  - "intersect the concepts"
---

# intersect — the one thing worth your attention

Where `reinforce` reports facts and `concept-coalesce` aggregates them, intersect
does the one thing only judgment can: it asks, **across the entire corpus, what
is the single highest-value thing for your human to look at right now.** It reads
everything — concepts, notes, hypotheses, grants, papers, projects — and emits
**one** candidate into the dream report. Not a page, not a queue item: an
attention target, explicitly labeled as opinion.

The standard is the *perfect-home-page* ideal: a page so well-tuned it shows one
item, and you buy it immediately. intersect's goal is to be that right — the one
thing, so clearly worth 10 minutes of your thinking that you act on it. It does
**not** dilute that with a ranked list; the runners-up live in the report's audit
section, not the Summary line.

> **Conventions:** `rem-cycle-contract.md` (the fact/opinion line — this is
> *opinion*, so it surfaces labeled and never auto-writes a page; the dream
> report's "One thing" section), `frontmatter.md` (kinds it scans),
> `quality.md`. Character: `SOUL.md` — **honesty about confidence**: a weak
> candidate is labeled weak; a strong one is argued, not asserted.

## Capabilities

- **Required:** `brain-read`, `brain-search` (whole-corpus scan).
- **Optional:** none.

Universal; **no external I/O** — intersect synthesizes what the graph already
holds.

## What this guarantees

- **One item, every run.** Never zero (silence would defeat the purpose), never
  more than one. The discipline is ranking before surfacing, not generating.
- **Labeled as opinion.** Every surfaced item is explicitly a judgment — "I think
  this is worth your attention" — never dressed as a fact. It may propose a
  hypothesis (without writing a page), an idea, or a next-action, but always as
  opinion for your human to take or leave.
- **Honesty about confidence.** A target backed by convergent sources is argued
  with those sources; a thin one says "this is a hunch", not "this is the
  answer".
- **Never writes a page.** intersect surfaces to the report only. It creates no
  `hypothesis`, no `concept`, no `note`.
- **Scans broadly, ranks narrowly.** It reads the whole corpus but emits one thing
  — breadth in, singularity out.

## Phases

1. **Scan.** Enumerate candidate attention targets across the corpus, without
   restricting to the synthesis layer. Sources of a candidate:
   - **tonight's `notable:` signals first** — when run as a rem-cycle phase,
     read that night's `docs/rem-cycle/runs/<date>/*.yaml` and collect their
     `notable:` entries (contradictions, suspected entity pairs, key-conflicts,
     ripe concepts, unsynthesized clusters),
   - a concept whose `## Shifts` log has accumulated new facts that, read
     together, point somewhere (a tension, a convergence, a gap),
   - two-plus concepts whose frontiers have drifted toward one another,
   - a cluster of `note` stubs `intersect`-style coalescence that `concept-coalesce`
     passed over (below floor, but still interesting),
   - a `grant` aim that recent papers now make feasible (or obsolete),
   - a topic we keep "dipping our toes in" — repeated shallow mentions in notes
     and grants — that now warrants a deep dive,
   - an open `hypothesis` whose evidence has quietly accumulated enough to resolve.
2. **Rank.** Score each candidate on **value to your human right now** (would
   acting on it change a decision, a grant, an experiment) × **timeliness** (is
   the evidence newly assembled, or has it been sitting unnoticed) ×
   **grounding** (can it be argued from the graph, not from a vibe). Pick the
   single highest.
3. **Surface.** Write the one item into the phase result (below) for the report's
   "One thing" section. Argue it: what it is, why now, the proposed next action,
   and the confidence — honestly.
4. **Return** the phase result or, standalone, a conversational one-item summary.

## As a rem-cycle phase

The **nightly** phase (phase 8; `rem-cycle-contract.md`). intersect is
surface-only — it writes no page, only the phase result:

- **`committed[]`** — empty (intersect writes nothing to the graph).
- **`notable[]`** — empty (intersect consumes tonight's signals; it reports).
- **Phase-specific field** — the surfacing itself rides in the result file as a
  `surfacing:` block (see below), which the aggregator lifts into the report's
  "One thing" section.
- **`metrics`** — `candidates_scanned`, `candidates_ranked`,
  `notable_signals_seen`, `surfaced` (1).

```yaml
surfacing:
  what: "<one sentence — the target>"
  why_now: "<the evidence assembled from the graph, cited>"
  next_action: "<what your human might do: draft an aim, commission a dive, start a conversation>"
  confidence: "<high | medium | low — honest>"
  runners_up: [ "<2-4 one-line runners-up, for the report's audit section>" ]
```

## Output

The surfaced item is the **standalone conversational answer** or the dream
report's **"One thing"** section. No page is written.

## Anti-patterns

- Emitting more than one item, or a ranked list as the headline — the whole point
  is singularity.
- Manufacturing a candidate for a thin corpus — argue it honestly, or say the
  corpus is too sparse to rank.
- Writing a `hypothesis` or `concept` page — intersect surfaces opinion, it never
  authors.
- Asserting an opinion as fact — the label is non-negotiable.
- Reaching outside the vault — intersect synthesizes the graph, it never fetches.
