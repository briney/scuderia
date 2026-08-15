---
name: concept-refresh
description: >
  A concept whose Shifts log has outrun its Thesis (≥3 shifts since
  thesis_updated) is ripe for re-synthesis. In the scheduled rem-cycle
  (phase 5b) this skill is DETECTION-ONLY — it emits notable: ripeness
  signals, never drafts. Standalone ("refresh the concepts"), it drafts the
  refresh grounded in those shifts and lands it in conversation with your
  human — the rewrite is generative, so the waking path owns it.
triggers:
  - "refresh the concepts"
  - "which concepts outran their thesis"
  - "re-synthesize concept theses"
---

# concept-refresh — the Thesis re-synthesis loop

`reinforce` appends shifts to a concept's `## Shifts` log; nothing integrates
them into the Thesis. A concept with ten shifts still carries the Thesis it was
seeded with — the cortical rewrite step is missing. This skill is that step,
and it has two modes with different powers:

- **Scheduled (rem-cycle phase 5b): DETECTION ONLY.** Thesis/Frontier prose is
  opinion, and opinion is never written — or drafted — by the dream
  (`rem-cycle-contract.md`, 2026-08-15 binary gate). The phase scans for
  ripeness and emits one `notable:` entry per ripe concept. Tonight's
  `intersect` reads the signal; a genuinely important one competes for the
  dream report's One-thing slot.
- **Standalone (waking): full draft.** Run in conversation, this skill drafts
  the refreshed Thesis/Frontier grounded in the shifts and lands it with your
  human present — the drafting procedure below governs this path.

> **Conventions:** `synthesis-layer-pages.md` (concept anatomy, the Shifts
> format), `frontmatter.md` (`thesis_updated:`), `rem-cycle-contract.md` (the
> phase result, the binary gate, notable signals), `quality.md` (cite-or-flag).
> Character: `SOUL.md` — no fabricated confidence; every sentence of a draft
> traces to a cited shift.

## The ripeness scan (both paths)

Scan `concepts/*.md` (skip README.md); parse `thesis_updated:` and the dated
`## Shifts` entries (`### YYYY-MM-DD —`). Candidates: pages with ≥3 shift
entries dated after `thesis_updated`. A shift-poor concept produces nothing —
silence is correct.

## Scheduled path — signal, never draft

For each candidate emit ONE `notable:` entry: `what` = "concepts/<slug> is N
shifts behind its Thesis", `why` = one line naming what the shifts collectively
moved (and what they do NOT yet establish, if it tempers the signal),
`sources` = the shift source-paper slugs. Phase result: `committed[]` empty,
`metrics`: `concepts_scanned`, `candidates`. No cursor — the scan is cheap
(frontmatter + heading dates).

## Standalone path — draft and land in conversation

1. **Select** per the ripeness scan; report the candidate list.
2. **Draft.** For each candidate, rewrite `## Thesis` and `## Frontier`
   integrating the shifts: the current best statement now reflects what the
   shifts moved; Frontier maturity markers advance where the shifts warrant.
   Preserve your human's verbatim quotes exactly (`_output-rules.md`). Every
   claim cites its shift's trigger page. Name what the shifts collectively
   moved — and what they did *not* establish (the edge). Mark which
   load-bearing shifts are `[unconfirmed]`.
3. **Land it with your human** — show the draft, take edits, write the page
   only on his go-ahead (never blind-overwrite; read current state first).

## Anti-patterns

- Manufacturing a refresh for a shift-poor concept — the ≥3-shift gate is the
  whole select step.
- Drafting Thesis/Frontier prose in the scheduled phase — detection only;
  the dream never authors opinion.
- Paraphrasing or inventing your human's quotes — verbatim only, or omit.
- A draft sentence with no shift citation — grounded or gone.
- Dropping the `[unconfirmed]` flag on a shift a draft leans on — the trust
  surface must survive into the draft.
