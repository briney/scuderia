---
name: concept-refresh
description: >
  Re-synthesize a concept's Thesis/Frontier when its Shifts log has outrun it —
  ≥3 shifts since thesis_updated. Drafts the refresh grounded in those shifts,
  every sentence traceable to a cited shift; always propose-tier. Weekly
  rem-cycle delegate (phase 5b) or standalone ("refresh the concepts").
triggers:
  - "refresh the concepts"
  - "which concepts outran their thesis"
  - "re-synthesize concept theses"
---

# concept-refresh — the Thesis re-synthesis loop

`reinforce` appends shifts to a concept's `## Shifts` log; nothing integrates
them into the Thesis. A concept with ten shifts still carries the Thesis it was
seeded with — the cortical rewrite step is missing. This skill is that step:
when a concept's log has outrun its prose, draft the refreshed Thesis/Frontier
**grounded in those shifts**, and queue it for Bryan. Propose-tier only — the
rewrite is generative, so Bryan owns landing it (via `queue-drain`).

> **Conventions:** `synthesis-layer-pages.md` (concept anatomy, the Shifts
> format), `frontmatter.md` (`thesis_updated:`), `rem-cycle-contract.md` (the
> phase result, propose tier, the evidence rule), `quality.md` (cite-or-flag).
> Character: `SOUL.md` — no fabricated confidence; every sentence of the draft
> traces to a cited shift.

## Capabilities

`brain-read`, `brain-write` (the QUEUE proposal only). Universal; no external
I/O — the draft is grounded in pages already in the graph.

## What this guarantees

- **Grounded, never invented.** Every sentence of the drafted Thesis/Frontier
  traces to a cited shift entry (or to the page's existing prose, quoted). If
  the shifts don't support a sentence, the sentence doesn't ship.
- **Propose-tier always.** The concept page is never written by this skill —
  the draft rides in `QUEUE.md` as a `thesis-refresh` proposal carrying the
  full replacement text and the shift list. Bryan approves via `queue-drain`;
  execution is a queue-drain work order like any other.
- **Selective.** Only concepts with ≥3 shifts dated after `thesis_updated:` are
  candidates. A shift-poor concept produces nothing — silence is correct.
- **`[unconfirmed]` shifts count but are flagged** — the draft marks which of
  its load-bearing movements are still unconfirmed, so Bryan sees the trust
  surface he's approving.

## Phases

1. **Select.** Scan `concepts/*.md`; parse `thesis_updated:` and the dated
   `## Shifts` entries (`### YYYY-MM-DD —`). Candidates: pages with ≥3 shift
   entries dated after `thesis_updated`.
2. **Draft.** For each candidate, rewrite `## Thesis` and `## Frontier`
   integrating the shifts: the current best statement now reflects what the
   shifts moved; Frontier maturity markers advance where the shifts warrant.
   Preserve Bryan's verbatim quotes exactly (`_output-rules.md`). Every claim
   cites its shift's trigger page. Name what the shifts collectively moved —
   and what they did *not* establish (the edge).
3. **Propose.** Emit one `proposed[]` entry per candidate
   (`category: thesis-refresh`): target = the concept, `change` = "replace
   Thesis/Frontier with the drafted rewrite", the full draft + the shift list
   in the entry body, confidence, and a count of `[unconfirmed]` shifts the
   draft leans on. Never write the concept page.
4. **Return** the phase result (rem-cycle-contract.md) or, standalone, a
   conversational summary — including a plain "no concept has outrun its
   thesis" when that is the answer.

## As a rem-cycle phase

Phase 5b (weekly, after consolidation). `committed[]` is normally empty;
`proposed[]` carries the refresh drafts, deduped against QUEUE.md and
`decisions.yaml`. `metrics`: `concepts_scanned`, `candidates`, `drafts_proposed`.
No cursor — the scan is cheap (frontmatter + heading dates).

## Anti-patterns

- Manufacturing a refresh for a shift-poor concept — the ≥3-shift gate is the
  whole select step.
- Paraphrasing or inventing Bryan's quotes — verbatim only, or omit.
- Writing the concept page — propose-tier always; landing is Bryan's act.
- A draft sentence with no shift citation — grounded or gone.
- Dropping the `[unconfirmed]` flag on a shift the draft leans on — the trust
  surface must survive into the proposal.
