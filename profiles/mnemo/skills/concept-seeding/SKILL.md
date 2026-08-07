---
name: concept-seeding
description: >
  One-time backward distillation that births the concept layer from the existing
  applied corpus (projects, grants, cited papers). Extracts umbrella concepts,
  proposes a top-down inventory for your human's approval, then authors canonical
  concept pages and wires the applied layer to them. A bootstrap, run once — not
  a recurring rem-cycle phase.
triggers:
  - "seed the concept layer"
  - "distill concepts from the grants"
  - "distill concepts from the projects"
  - "bootstrap the concepts"
  - "build the concept layer"
---

# concept-seeding — birth the concept layer by backward distillation

The brain was built applied-end first: dense `grants/` and `projects/`, an almost
empty `concepts/`. The cross-cutting ideas that belong in `concepts/` are trapped
inside the applied pages' framing. This skill distills them **backward** out of
that corpus — once — so the concept layer exists and the synthesis engine
(reinforce / intersect) and the concept-grounded conversation surface have
something to run on. Full design:
the instance's private `docs/specs/`.

> **Conventions:** `synthesis-layer-pages.md` (**the canonical concept anatomy**
> this authors), `frontmatter.md` + `graph-and-links.md` (concept fields,
> forward-only child→parent edges), `quality.md` (the notability gate,
> cite-or-flag), `_output-rules.md` (verbatim-quote fidelity),
> `rem-cycle-contract.md` (the `QUEUE.md` propose surface bottom-up candidates
> land on), `test-before-bulk.md` (test the extraction on a sample first),
> `skills/conventions/capabilities.md`. Character: `SOUL.md` — **ingest with your own hands** (author
> concepts yourself; delegate only the ephemeral scan), propose-not-auto,
> cite-or-flag.

## Capabilities

- **Required:** `brain-read`, `brain-write`, `spawn-subagent` (Phase 1 scan only).
- **Optional:** `brain-search` (bottom-up clustering; degrades to keyword scan
  under Claude Code — accept wider, noisier candidates).

Universal; needs no external tools. This skill operates only on what is already
in the vault — it fetches nothing.

## What this guarantees

- **A concept is an umbrella with contents.** An umbrella earns a page only if
  **≥1 legitimately plausible candidate hypothesis** marinates in it. Sharp bets
  are Frontier candidates, never their own concepts; a bare topic with no
  plausible bet inside it is not admitted.
- **Two-stage, propose-not-auto.** Top-down concepts materialize **only after
  your human approves the inventory**; bottom-up candidates are proposed to `QUEUE.md`
  and materialize only on approval. Nothing is auto-authored.
- **Authoring is never delegated.** Subagents do the Phase-1 scan (ephemeral
  reconnaissance over already-ingested material); the mind authors every durable
  concept page itself (`SOUL.md`).
- **Never writes `hypotheses/`.** Output is concept pages only. Candidate
  hypotheses land as Frontier bullets; the proving-ground is populated later by
  explicit promotion.
- **Non-destructive, forward-only.** The 2 existing concepts are folded /
  reformatted, never duplicated. `rests_on` goes on the project/grant (child);
  backlinks are derived.
- **Bounded and one-time.** The corpus is small and fixed — a single pass gated
  by the inventory approval, not a rotating cursor.

## Phases

1. **Scan & extract** *(delegated, ephemeral).* Spawn subagents to run **two
   scans**, each returning candidate `(umbrella, marinating-bet)` pairs with their
   source pages:
   - **Top-down** *(primary)* — read the projects' `## Framing` / `## Open
     questions`, the grants' Significance / Innovation, and the cited papers (with
     `RESEARCH.md` for thread context); these candidates are **anchored** to a
     project/grant.
   - **Bottom-up** — `brain-search`-cluster `papers/`, `methods/`, and the 2
     existing `concepts/` to surface cross-disciplinary lenses **not anchored to
     any project/grant** (the slot the 2 existing paper-derived concepts occupy);
     flag these as unanchored.

   Reconnaissance only: no authoring, no page writes. Test on a small sample
   before the full scan (`test-before-bulk.md`).

2. **Factor & gate** *(the mind).* Consolidate the candidates into umbrella
   concepts. Apply the gate: admit an umbrella only if ≥1 plausible candidate
   hypothesis marinates in it; demote sharp-bet candidates to that umbrella's
   Frontier; drop bare topics. Dedup against the 2 existing concepts (fold, don't
   duplicate). Split the result: **top-down** umbrellas (anchored in a
   project/grant) for the inventory; **bottom-up** umbrellas (cross-disciplinary
   lenses not tied to a project) for the queue.

3. **Inventory checkpoint** *(human-in-the-loop).* Present the top-down inventory
   for your human to **approve / prune / merge / rename** before any page is authored
   (format in Output). Route bottom-up umbrellas to `QUEUE.md` as concept
   proposals (`rem-cycle-contract.md`) — drained only by your human. Author nothing
   until the inventory is approved.

4. **Author approved concepts** *(the mind, own hands).* For each approved
   umbrella, author the canonical concept page (`synthesis-layer-pages.md`):
   `## Thesis` = the umbrella framing; `## Frontier` = the candidate hypotheses as
   bullets with maturity markers (`*fuzzy*` / `*sharpening*`) — **always a
   Frontier bullet, never a `hypotheses/` page**; `## Open questions` = the
   discriminating questions from the sources; `## Shifts` = one seed entry
   (`seeded YYYY-MM-DD, distilled from [sources]`). Seed `importance`; wire
   `related_concepts` among the new set. Anchor the sharpest framing on a verbatim
   quote where one exists (`_output-rules.md`).

5. **Wire the applied layer & map** *(the mind).* Add `rests_on: [concepts/...]`
   to the projects/grants that draw on each concept (forward edge on the child).
   Refresh `concepts/README.md` and tier the new set by **calling
   `concept-synthesis`** (its map + tiering machinery — do not reimplement). Then
   your human does one batched page-level review covering the authored concepts *and*
   the `rests_on` edits together.

## Output

- **The inventory** — one row per proposed top-down concept, for approval before
  authoring:

  | umbrella | framing | candidate hypothesis(es) | reach | sources |
  |---|---|---|---|---|
  | the concept title | one-line umbrella framing (the `## Thesis` seed) | the ≥1 marinating bet that justifies it (the admission ticket) | threads it cuts across, or "foundational to `<thread>`" | the `projects/` / `grants/` / `papers/` distilled from |

- **Authored concept pages** in the canonical anatomy, each lint-clean
  (`lint-frontmatter.py`) with a seeding `## Shifts` provenance entry.
- **Bottom-up candidates** appended to `docs/rem-cycle/QUEUE.md` as concept
  proposals (highest-confidence first), never auto-materialized.
- **`rests_on` edits** on the relevant projects/grants, surfaced in the Phase-5
  batched review.
- **A refreshed `concepts/README.md`** (via `concept-synthesis`).

## Anti-patterns

- Authoring a concept page for an umbrella with **no plausible candidate
  hypothesis** — that is a topic, not a concept; drop it.
- Writing a `hypotheses/` page. This skill produces concepts only; sharp bets are
  Frontier bullets until an explicit promotion.
- Delegating the *authoring* to a subagent — the Phase-1 scan is delegable, the
  concept prose is not (`SOUL.md`).
- Materializing any concept before your human approves the inventory; auto-clearing or
  auto-approving `QUEUE.md`.
- Duplicating or blind-overwriting the 2 existing concepts instead of folding /
  reformatting them.
- Generic umbrella names ("machine learning", "antibodies"). If you cannot state
  the marinating bet, it is not a concept.
- Reimplementing `concept-synthesis`'s tiering/map instead of calling it, or
  running the full scan before testing extraction on a sample.
- Treating this as a recurring job — it is a one-time bootstrap. Ongoing concept
  discovery is a later rem-cycle phase.
