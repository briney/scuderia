---
name: retroactive-linking
description: >
  Re-read a page against the *current* graph and add the forward edges that
  weren't possible at ingest — a note filed in March can now link to an entity
  that only got a page in June. The deep, semantic re-linking pass, cursor-driven
  over the whole corpus. Runs standalone ("link this page", "re-link the brain")
  or as a rem-cycle phase.
triggers:
  - "link this page"
  - "find missing links for"
  - "retroactive linking"
  - "re-link the brain"
  - "what should this page connect to"
---

# Retroactive linking — connect a page to the graph it now lives in

A page's links are frozen at write time. But the graph keeps growing: entities
get pages, concepts get synthesized, papers get ingested. A page written before
those existed under-links the brain until something re-reads it *in the light of
everything the brain now knows*. That re-reading is this skill — the heart of
the `rem-cycle`, and the one phase no existing skill covers.

> **Conventions:** `graph-and-links.md` (the two edge forms, forward-only,
> derived backlinks), `rem-cycle-contract.md` (the phase result, the two commit
> tiers, the evidence rule — when run as a rem-cycle phase), `quality.md`
> (forward-only linking, the notability gate), `brain-ops` (never-blind-overwrite).

## Capabilities

`brain-search`, `brain-read`, `brain-write`. `brain-search` is load-bearing
here — it is the cheap candidate-generator (qmd semantic neighbours under
Hermes, Grep under Claude Code). Universal; degrades to Grep-only gracefully.

## Scope — how this differs from `maintain`

`maintain`'s *missing-forward-links* dimension is the cheap, opportunistic
version: while scanning a page for health, if it names another page's subject
**verbatim** and didn't link it, add the link. It only sees pages it happens to
read, and only verbatim mentions.

This skill is the **dedicated, semantic, cursor-driven** pass. It *generates
candidate* targets that the prose does not name verbatim — semantic neighbours,
shared-neighbour pairs, co-citation — adjudicates each against the text, and
rotates systematically over the whole corpus. `maintain` catches the obvious
ones inline and **chains here** for the deep pass, the same way it chains into
`frontmatter-guard` and `citation-fixer`.

## What this guarantees

- Every edge added is a **forward** edge on the page being read — never a
  hand-written backlink.
- Every edge carries a verbatim **evidence span** from the page; an edge the
  text does not justify is never written. **The span must be verifiable against
  the page as it exists after your edit** — if inserting a wikilink rewrites
  the phrase it anchors to (plain text → `[[slug|display]]`), capture the
  post-edit span including the wikilink markup, or quote a sub-span the edit
  does not touch. A pre-edit excerpt that no longer appears in the page fails
  the aggregator's verbatim check (observed 2026-08-04: 4/4 committed spans
  failed this way).
- The two commit tiers follow `rem-cycle-contract.md`: an evidence-backed
  verbatim mention (canonical abbreviations count) → **auto** wikilink; a
  *typed* relationship edge, and any edge to a page that does not exist yet, →
  **proposed**. A `cites:` edge is proposed only when the citation is
  analytically load-bearing, never for a benchmark or incidental mention.
- A page is read in full before it is edited; a recently-edited page is held.
- The cursor advances; a re-run over an already-linked slice is a no-op.

## The frontier

What gets re-linked in one invocation:

- **Standalone, one page:** just that page.
- **Standalone, "re-link the brain":** the whole corpus, budget permitting.
- **As a rem-cycle phase:** **inbox first** — drain every packet in
  `docs/rem-cycle/inbox.yaml` not yet in your `consumed_by` (these are pages
  ingested or stub-filled since the last run; process them before anything
  else, budget permitting, and append `retro` to each item's `consumed_by`),
  then a **rotating slice** — a fixed-size window advanced from the cursor in
  `_state.yaml`, so every old page is periodically reconsidered without any
  single run exploding in cost. Save the new cursor in the phase result.

## Phases

1. **Select the frontier.** Resolve the page set from the trigger above. Skip
   protected pages (`rem-cycle-contract.md` — `USER/<name>.md`, `SOUL.md`, etc.).
2. **Candidate generation (cheap).** For each page, gather likely targets
   *without* an LLM: exact name/alias and `people/` slug matches,
   `brain-search` semantic neighbours, shared-neighbour pairs in the link graph
   (two pages with many common neighbours likely deserve a direct edge), and
   co-citation. This is the shortlist the expensive step operates on.
3. **Adjudication (expensive, shortlist only).** For each candidate, read the
   page's prose and decide: is a link justified, and is it a plain mention
   (wikilink) or a *typed* relationship (frontmatter edge, and which type)?
   Require a verbatim evidence span for every kept candidate. Discard the rest.
4. **Write / propose.** Sort each kept edge into its tier per
   `rem-cycle-contract.md`. Auto-tier — an evidence-backed verbatim mention of a
   page that **exists** — gets a `[[kind/slug]]` wikilink in the body where the
   mention sits. Typed relationship edges, and edges to a page that does not
   exist yet, go to the propose queue with evidence, confidence, and
   `target_exists`. An edge to a missing page is *valid* (it marks work to do),
   but it is proposed, not auto-written — the slug is a guess until the page
   exists. Where an entity has both an absent `methods/` (or other) stub and a
   real page, link the real page and flag the pair for entity resolution.
5. **Emit the result.** Report per `rem-cycle-contract.md` when run as a phase;
   otherwise report conversationally — what was linked, what is proposed.

## Output

- **As a rem-cycle phase:** the fenced-yaml phase result
  (`rem-cycle-contract.md`) — `committed[]` wikilinks, `proposed[]` typed edges
  with evidence, `metrics.edges_added`, and the advanced `cursor`.
- **Standalone:** the auto-tier links committed, and a short list of proposed
  typed edges surfaced inline for the human to accept or reject.

## Anti-patterns

- Hand-writing a backlinks section — inbound edges are derived
  (`skills/conventions/graph-and-links.md`).
- Adding an edge with no evidence span from the page — a hallucination with an
  arrow on it.
- **Linking inside verbatim regions** — grant pages' `## Verbatim` sections,
  blockquoted text, and numbered reference lists are frozen source text. A
  paper title there is a citation *record*, not a mention to link (observed
  2026-08-04: 47 such links had to be reverted). Link prose, never quotation.
- Auto-committing a *typed* relationship edge, or a wikilink to a page that
  does not exist — both are judgment calls; propose them.
- Flooding the queue with `cites:` edges for benchmark or incidental citations —
  propose a citation edge only when it is analytically load-bearing.
- Running LLM adjudication over every page pair instead of the cheap
  candidate shortlist — exhaust `brain-search` and graph traversal first.
- Editing a page without reading it in full, or overwriting a just-edited page.
- Re-linking `USER/<name>.md` or other protected pages.
- Inventing an alias to force a match — normalize real aliases, never fabricate.
