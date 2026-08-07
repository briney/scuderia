---
name: grant-finalize
description: Close out a submitted cluster-written grant — promote the draft to voice corpus, transition the lifecycle to submitted, archive the as-submitted package, and propagate the grant across the knowledge graph.
triggers:
  - "I submitted the grant"
  - "the grant went in"
  - "finalize the submitted grant"
  - the post-submission housekeeping pass
---

# Grant finalize — close out a submitted grant

The post-submission endpoint of the grant-writing cluster. `grant-coherence`
clears the pre-submission gate, Bryan submits, and this skill takes the `grant`
page from `drafting` to a fully-integrated `submitted` page: the draft becomes
voice corpus, the lifecycle transitions, the submitted package is archived, and
the grant propagates across the brain.

A submitted cluster-written grant becomes the same high-value graph object that
`grant-ingest` produces from an external grant — it just skips extraction and
distillation, because the prose and analysis are already on the page. The graph
propagation is therefore **shared with `grant-ingest`**, not reinvented here.

> **Conventions:** `skills/conventions/frontmatter.md` (the `grant` schema and status
> enum), `skills/conventions/raw-source-archive.md` (archiving the submitted package),
> `skills/conventions/graph-and-links.md` (the propagation edges),
> `skills/conventions/importance-scoring.md` (refreshing the salience score),
> `skills/conventions/quality.md` (the notability gate on new pages),
> `skills/conventions/capabilities.md` (the harness contract).
> **Shared procedure:** `skills/grant-ingest/SKILL.md` phase 7 — the graph
> propagation, referenced not restated. Chains to `skills/enrich/SKILL.md`,
> `skills/paper-ingest/SKILL.md`.

## Capabilities

`brain-read`, `brain-write`, `raw-source-archive-upload` (the
as-submitted package).

## What this guarantees

- A submitted cluster-written grant becomes a fully-integrated `grant` page —
  `status: submitted`, indistinguishable in shape from a `grant-ingest` output.
- `## Draft` is promoted to `## Verbatim`: the submitted prose joins the voice
  corpus, with **no provenance segregation** — every grant submitted in Bryan's
  name is Bryan's voice, and counts equally for `grant-section`.
- The as-submitted package is archived to R2; no binary enters git.
- The grant propagates across the brain exactly as an ingested grant does.
- Cross-grant synthesis and new `hypothesis` pages are deliberately not done
  here — same boundaries as `grant-ingest`.

## Phases

1. **Confirm submission.** Bryan confirms the grant was submitted. Identify the
   `grant` page (`status: drafting`). This skill is the submission moment only:
   anything that comes *back* — a summary statement, reviewer critiques — is
   `grant-ingest`'s job, and a resubmission re-enters at `grant-plan`.

2. **Promote the draft to corpus.** `## Draft` → `## Verbatim`. The submitted
   prose is Bryan's voice — no authorship marker, no segregation of
   cluster-written from pre-brain grants (`grant-section` weights all
   `## Verbatim` equally; the post-brain voice is the refined target, not a
   diluted one). Figure captions are kept. The page now matches the
   `grant-ingest` page shape.

3. **Finalize the analysis.** Ensure `## Summary`, `## Significance &
   Innovation`, `## Preliminary Data`, `## Approach`, and `## Future
   Directions` reflect the as-submitted version — the page should read like a
   `grant-ingest` output, not a half-finished draft.

4. **Transition the lifecycle.** Set `status: submitted` and the `submitted:`
   date; clear the submission `deadline` (the attention contract now tracks the
   grant by status until a summary statement arrives). Refresh `importance`
   (`importance-scoring.md`) — a submitted grant is high-salience. Close the
   `## Drafting log` with a dated submitted entry.

5. **Archive the as-submitted package.** The final submitted document(s) →
   `_drop/` → R2; one `sources:` entry per document, each tagged with its
   `role:` (`skills/conventions/raw-source-archive.md`). The NOFO `sources:` entry
   from `grant-plan` stays. No binary enters git.

6. **Propagate into the graph.** Run the propagation of `grant-ingest` phase 7
   — Specific Aims → `project` pages; preliminary data → `concept` / `method`
   evidence callouts; methods and concepts → pages; foundational references →
   `skills/paper-ingest/SKILL.md`; funder → `institution` and program officers
   → `person` via `skills/enrich/SKILL.md`. Follow that procedure; do not
   restate it here.

7. **Surface the program-state delta.** Offer Bryan a suggested `RESEARCH.md`
   funding-context update (e.g. "R01 — submitted, awaiting review"). Do not
   auto-edit `RESEARCH.md` — it is hand-curated program state. Note that the
   grant is now available for cross-grant `skills/concept-synthesis/SKILL.md`;
   do not run that synthesis here.

## Output

A `grant` page in `status: submitted`, indistinguishable in shape from a
`grant-ingest` output and fully wired into the graph; the as-submitted package
archived to R2; the brain's `project`, `concept`, and `method` pages updated
with the grant's contributions; a proposed `RESEARCH.md` funding-context delta
handed to Bryan.

## Anti-patterns

- Running `grant-ingest` on a cluster-written grant — it would re-extract and
  clobber the page. `grant-finalize` is the correct endpoint.
- Restating `grant-ingest`'s propagation procedure instead of referencing its
  phase 7.
- Marking or segregating the promoted `## Verbatim` by authorship — every
  submitted grant is Bryan's voice corpus, full stop.
- Doing cross-grant synthesis, or creating `hypothesis` pages from grant
  content — the same boundaries `grant-ingest` holds.
- Auto-editing `RESEARCH.md` instead of surfacing the delta for Bryan.
- Leaving `status: drafting`, or a live submission `deadline`, after the grant
  has gone in.
- Committing the submitted package binary into git instead of archiving to R2.
