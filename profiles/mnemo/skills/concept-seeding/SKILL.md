---
name: concept-seeding
description: >
  One-time backward distillation that births the concept layer from the existing
  applied corpus (projects, grants, cited papers). Extracts umbrella concepts,
  proposes one top-down and bottom-up inventory for human approval, then authors canonical
  concept pages and wires the applied layer to them. A bootstrap, run once — not
  a recurring rem-cycle phase.
triggers:
  - "seed the concept layer"
  - "distill concepts from the grants"
  - "distill concepts from the projects"
  - "bootstrap the concepts"
  - "build the concept layer"
eval_contract:
  goal: Bootstrap approved source-grounded concepts from the existing applied corpus, with required graph links.
  dimensions:
    - "GROUNDING — each concept and candidate hypothesis is supported by the source pages"
    - "SCOPE — the approved inventory governs output, regardless of execution mode"
    - "INTEGRATION — distinct page ownership, verification, and applied-layer links are complete"
    - "GUARDING — an already-populated concept layer stops for human confirmation rather than re-bootstrapping"
  hard_fails:
    - Authoring concepts outside the approved inventory or writing hypothesis pages in this skill.
    - Losing source evidence, duplicating existing concepts, or overlapping concurrent writes.
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
> `rem-cycle-contract.md` (the binary gate — this skill is a waking,
> conversational bootstrap, so its candidates land in the inventory for
> your human's approval, never in a retired review queue),
> `test-before-bulk.md` (test the
> extraction on a sample first),
> `skills/conventions/capabilities.md`. Character: `SOUL.md`; retain the
> inventory approval and cite-or-flag requirements when delegating.

## Capabilities

- **Required:** `brain-read`, `brain-write`, `spawn-subagent`.
- **Optional:** `brain-search` (bottom-up clustering; degrades to keyword scan
  under Claude Code — accept wider, noisier candidates).

Universal; needs no external tools. This skill operates only on what is already
in the vault — it fetches nothing.

## What this guarantees

- **A concept is an umbrella with contents.** An umbrella earns a page only if
  **≥1 legitimately plausible candidate hypothesis** marinates in it. Sharp bets
  are Frontier candidates, never their own concepts; a bare topic with no
  plausible bet inside it is not admitted.
- **Two-stage, approve-first.** Top-down concepts materialize **only after
  your human approves the inventory**; bottom-up candidates ride in the same
  inventory (clearly marked) and materialize only on approval. Nothing is
  auto-authored.
- **Delegate independent work.** Workers may scan sources or author approved
  concepts; assign distinct pages and verify their source-grounded results.
- **Never writes `hypotheses/`.** Output is concept pages only. Candidate
  hypotheses land as Frontier bullets; the proving-ground is populated later by
  explicit promotion.
- **Non-destructive, forward-only.** The existing concepts — counted at run
  start, not from a frozen number — are folded / reformatted, never duplicated.
  `rests_on` goes on the project/grant (child); backlinks are derived.
- **Bounded and one-time.** Use the source set established for this bootstrap,
  gated by inventory approval, not a recurring cursor or a presumed corpus size.

## Phases

0. **Check whether this bootstrap has already run.** Count the existing
   `concepts/` pages (excluding `README.md`) at execution time — a simple
   count/check, no registry. A populated, diversified concept layer is
   **evidence the bootstrap probably already ran**, not proof: it is the
   signal to stop and **confirm with your human** (via the existing
   `ask-user` approval pattern) before doing anything, not a basis to
   proceed or to skip. If your human confirms a re-run is wanted, proceed
   with the fold-don't-duplicate discipline below; if not, ongoing concept
   maintenance belongs to `concept-synthesis` and the rem-cycle phases, not
   to a second bootstrap. Proceeding is the human's explicit call, not a
   default.

1. **Scan & extract** *(delegated, ephemeral).* Spawn subagents to run **two
   scans**, each returning candidate `(umbrella, marinating-bet)` pairs with their
   source pages:
   - **Top-down** *(primary)* — read the projects' `## Framing` / `## Open
     questions`, the grants' Significance / Innovation, and the cited papers (with
     `RESEARCH.md` for thread context); these candidates are **anchored** to a
     project/grant.
   - **Bottom-up** — `brain-search`-cluster `papers/`, `methods/`, and the
     existing `concepts/` to surface cross-disciplinary lenses **not anchored to
     any project/grant** (the slot the existing paper-derived concepts occupy);
     flag these as unanchored.

   Reconnaissance only: no authoring, no page writes. Test on a small sample
   before the full scan (`test-before-bulk.md`).

2. **Factor & gate** *(the mind).* Consolidate the candidates into umbrella
   concepts. Apply the gate: admit an umbrella only if ≥1 plausible candidate
   hypothesis marinates in it; demote sharp-bet candidates to that umbrella's
   Frontier; drop bare topics. Dedup against the existing concepts, counted at
   run start (fold, don't duplicate). Split the result: **top-down** umbrellas
   (anchored in a project/grant) and **bottom-up** umbrellas (cross-disciplinary
   lenses not tied to a project) — both land in the same inventory.

3. **Inventory checkpoint** *(human-in-the-loop).* Present the full candidate
   inventory — **both** the top-down umbrellas (anchored in a project/grant)
   and the bottom-up umbrellas (cross-disciplinary lenses, marked as
   bottom-up/unanchored) — for your human to **approve / prune / merge /
   rename** before any page is authored (format in Output). Both routes land
   in the same single inventory and are adjudicated in the same conversation;
   neither is silently dropped. Author nothing until the inventory is
   approved.

4. **Author approved concepts** *(delegate independent pages when useful).* For each approved
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

- **The inventory** — one row per proposed concept from either route, for approval before
  authoring:

  | umbrella | framing | candidate hypothesis(es) | reach | sources |
  |---|---|---|---|---|
  | the concept title | one-line umbrella framing (the `## Thesis` seed) | the ≥1 marinating bet that justifies it (the admission ticket) | threads it cuts across, or "foundational to `<thread>`" | the `projects/` / `grants/` / `papers/` distilled from |

- **Authored concept pages** in the canonical anatomy, each lint-clean
  (`lint-frontmatter.py`) with a seeding `## Shifts` provenance entry.
- **Bottom-up candidates** listed in the inventory (marked bottom-up), never
  auto-materialized.
- **`rests_on` edits** on the relevant projects/grants, surfaced in the Phase-5
  batched review.
- **A refreshed `concepts/README.md`** (via `concept-synthesis`).

## Closeout

The completed unit is the approved concept set, verified source/quote fidelity,
applied-layer links and map after the batched human review. The parent validates
all owned files and closes through `git-ops`; workers return paths and checks,
never stage or commit. An unapproved inventory is not a completed bootstrap.

## Anti-patterns

- Re-running this bootstrap on an already-seeded brain without an explicit
  human decision — the Phase-0 guard exists for that.
- Authoring a concept page for an umbrella with **no plausible candidate
  hypothesis** — that is a topic, not a concept; drop it.
- Writing a `hypotheses/` page. This skill produces concepts only; sharp bets are
  Frontier bullets until an explicit promotion.
- Materializing any concept before your human approves the inventory.
- Duplicating or blind-overwriting the existing concepts instead of folding /
  reformatting them.
- Generic umbrella names ("machine learning", "antibodies"). If you cannot state
  the marinating bet, it is not a concept.
- Reimplementing `concept-synthesis`'s tiering/map instead of calling it, or
  running the full scan before testing extraction on a sample.
- Treating this as a recurring job — it is a one-time bootstrap. Ongoing concept
  discovery is a later rem-cycle phase.
