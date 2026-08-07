---
name: reinforce
description: >
  New and changed papers update the concept layer's `## Shifts` logs — the
  "connections reinforced" half of the synthesis engine. Routes a recent paper to
  the concepts it touches and logs a Shift only when the paper actually *moves* the
  thesis or frontier, not merely when it is relevant. The autonomous, conservative
  lane; runs as a rem-cycle phase (offline, cursored) or standalone. The directed
  lane — an explicit concept call-out at ingest — lives in `paper-ingest`.
triggers:
  - "reinforce the concepts"
  - "update concepts from recent papers"
  - "what recent papers moved our concepts"
---

# reinforce — keep the concept layer current as papers arrive

A concept's `## Shifts` log is its contestable, weekly-read trust surface. This
skill keeps it current: as papers are ingested, it decides which concepts each
one *moves* and records the movement — so when your human comes to discuss a concept
days after reading, the shift is already there. It is the autonomous counterpart
to the directed lane in `paper-ingest`; together they are the reinforce engine.
Full design lives in the instance's private `docs/specs/`.

> **Conventions:** `synthesis-layer-pages.md` (**the `## Shifts` entry format** and
> concept anatomy this writes), `rem-cycle-contract.md` (the phase result, the two
> commit tiers, `dry-run`, the evidence rule), `graph-and-links.md` (the forward
> `links: concepts/…` edges it routes on; forward-only), `quality.md` (cite-or-flag,
> the notability / "so what" gate). Character: `SOUL.md` — no fabricated confidence;
> the hedged Shift format is how an autonomous append stays honest.

## Capabilities

- **Required:** `brain-read`, `brain-write`.
- **Optional:** `brain-search` (semantic routing for papers without explicit
  concept edges; degrades to keyword scan under Claude Code).

Universal; **no external I/O** — reinforce consolidates papers already in the graph,
it never fetches.

## What this guarantees

- **No-op is the default.** A Shift requires the paper to change what we'd think or
  do about the concept (the "so what"), not merely to be on-topic. Most papers
  touching a concept produce nothing.
- **Conservative autonomous bar.** Only *high-confidence* movements auto-append to a
  concept; everything borderline routes to `QUEUE.md` (your human's relevance-triage
  surface). The concept Shifts logs stay high-signal.
- **Never writes `hypotheses/`.** A bet mature enough to spin out is a QUEUE
  *promotion* proposal; this skill only appends Shifts and adjusts Frontier maturity
  markers in place.
- **Honest auto-appends.** Every auto-appended Shift carries the `[unconfirmed]`
  marker and the hedged format (cited trigger; what the source *showed* vs. what it
  *means for this concept* + the edge it does not yet establish).
- **Non-destructive, idempotent.** Append-only; dedup on `(concept, paper,
  category)`; `dry-run` until the phase earns trust.

## Phases

1. **Select.** The recent-paper window — the union of (a) pages under `papers/`
   **added to git since the cursor date** (`git log --since=<cursor>
   --diff-filter=A -- papers/`) and (b) **`stub-filled` packets** in
   `docs/rem-cycle/inbox.yaml` not yet consumed by reinforce — a filled stub
   never appears in the git-added log (the file already existed), so the
   packet is the only way it enters the pipeline. After processing, append
   `reinforce` to each packet's `consumed_by`.
   Use `--diff-filter=A` (added files only) — **not** plain `--since`, which picks
   up retroactive-linking edits to old papers and floods the subagent with 40
   files when only 3 are new. The cursor (`cursors.reinforce` in
   `docs/rem-cycle/_state.yaml`) is a **date watermark**, backfilled to the
   concept-seeding date so the existing corpus is baselined and the first
   scheduled run considers only genuinely new ingests; a re-run over an
   unchanged window is a no-op.
   **Hard cap: 5 papers per run.** If more than 5 new papers are found, process
   only the 5 most recent and advance the cursor to the date of the 5th — the
   remainder will be picked up on the next run. This prevents a large ingest
   batch from overloading the subagent.
2. **Route.** For each paper, the concepts it touches, in priority order: its
   `links: concepts/…` edges → its `## Analysis` section → semantic match of its
   abstract/analysis against concept `## Thesis` / `## Frontier`.
   **Then route to the hypothesis layer:** for each `hypotheses/*.md` page with
   `status: open`, ask whether the paper's Analysis or abstract bears on the
   hypothesis's Claim — support, refute, or irrelevant. Irrelevant is the
   default; only a real bearing routes.
3. **Classify** each `(paper × concept)` pair — **reinforce** / **complicate** /
   **new-spur** / **mature-to-promote** / **contradict-thesis** / **merely-relevant
   (no-op)** — and apply the conservative bar.
4. **Apply.**
   - High-confidence **reinforce / complicate / new-spur** → append an
     `[unconfirmed]` Shift (hedged). A **reinforce** additionally bumps the moved
     Frontier bullet's maturity marker (`*fuzzy* → *sharpening*`) where warranted.
   - Borderline movements, and every **mature-to-promote** / **contradict-thesis**
     → a `QUEUE.md` proposal (never in-place).
   - **Hypothesis edges are always propose-tier** (`cites:`-class typed edges are
     never auto — contract). A bearing routes as a proposal:
     `category: typed-edge`, change = `add supports: hypotheses/<slug>` (or
     `refutes:`) on the paper page, with the evidence span. Dedup against the
     paper's existing edges, QUEUE.md, and `decisions.yaml`.
   - **Grant relevance (weekly scope only):** does the paper's topic bear on an
     active/preparing grant's aims? A hit proposes `category: grant-relevance` —
     a `links:` edge + one-line note ("papers/<slug> bears on [[grants/<slug>]]
     aim N — <evidence span>"). Cap 5/week, highest-importance grants first.
5. **Return** the phase result (below) or, standalone, a conversational summary.

## As a rem-cycle phase

Phase 6 of the pipeline (`rem-cycle-contract.md`). The orchestrator passes `mode`;
this skill returns the fenced-yaml phase result:

- **Mode:** `dry-run` (report intended Shifts in `committed[]`, write nothing) or
  `normal` (auto-append high-confidence Shifts; queue the rest).
- **`committed[]`** — the auto-appended Shifts (`category: shift`), each carrying
  the cited trigger and the reasoning span.
- **`proposed[]`** — the QUEUE items (`category: shift-proposed` | `promotion` |
  `contradiction`), highest-confidence first, deduped against `QUEUE.md`.
- **`cursor`** — the date watermark, advanced to this run's date; **`metrics`** —
  `papers_scanned`, `concepts_touched`, `shifts_committed`, `shifts_proposed`,
  `promotions_proposed`, `no_ops`, `hypothesis_edges_proposed`,
  `grant_relevance_proposed`.

## Output

- **Auto-appended Shift** — a `[unconfirmed]`-marked entry in the concept's
  `## Shifts` in the canonical format (`synthesis-layer-pages.md`), e.g.
  `### 2026-07-07 — [unconfirmed] <spur>: fuzzy → sharpening` + `**Trigger:**` +
  `**Reasoning:**` separating shown from concluded and naming the edge.
- **QUEUE proposal** — one checkbox line per `rem-cycle-contract.md`
  (`**shift-proposed** · concepts/<slug> ← papers/<slug> → …`).
- **Standalone** — a conversational summary: what moved, what was queued, what was
  no-op'd.

## Anti-patterns

- Logging a Shift for a merely-relevant paper — no-op is the default; the `link`
  already records relevance.
- Auto-appending a borderline movement instead of queuing it — the autonomous bar
  is conservative.
- Writing a `hypotheses/` page — promotion is a QUEUE proposal, not an in-place act.
- Dropping the `[unconfirmed]` marker or the hedged "does-not-yet-establish" edge —
  that is what keeps an autonomous append honest.
- Re-appending a Shift a prior run already logged — dedup on `(concept, paper,
  category)`.
- Handling an explicit concept call-out here — that is `paper-ingest`'s inline
  directed hook; this skill is the autonomous lane.
- Fetching anything — reinforce consolidates ingested papers, it never reaches
  outside the vault.
