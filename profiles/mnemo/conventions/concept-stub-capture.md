# Convention: concept-stub capture — capture cheap, decide later

The doctrine for transient ideas that may, later, coalesce into a concept.

**The principle.** Capture is cheap; judgment is expensive; and you do not know
ex ante which transient idea is load-bearing. A stub filed today for ~zero effort
can become the root node of a real `concept` months later, when other stubs and
papers coalesce around it. If it was never filed, the coalescence is invisible
and lost. So: **file the stub now, defer the judgment.** (The GBrain insight,
adopted in the form that fits a mnemo brain — see below.)

**The home is `notes/`, not `concepts/`.** The `concepts/` directory is curated
and humanly read; flooding it with hundreds of stubs would bury the pages your
human actually opens. A concept stub is a `note` page (`page-kinds.md` — "a
reflection, a brainstorm capture") carrying a marker that flags it as a concept
candidate. The marker is what lets `concept-coalesce` find it; the `notes/`
home is what keeps it out of your human's curated reading surface.

This is a capture-unit decision, **not a new page kind** (`brain-schema-evolution`
guideline: no new kind without an overwhelming reason). The `note` kind already
means "cheap first-person idea"; a concept stub is a `note` with a known future.

## What a concept stub is

A `note` page with:

```yaml
kind: note
slug: <readable>
is_concept_stub: true          # the marker concept-coalesce scans for
links: [<the page(s) that carries the idea>]
status: open                   # open | promoted | dormant
```

plus a body that is **verbatim + one line of context**, no more:

```markdown
# <idea, in your human's or the source's own words>

> "<verbatim trigger>"

[Source: <your-human, <context>, YYYY-MM-DD> | papers/<slug> | …]
```

A stub is **provenance + a forward edge + a verbatim trigger.** It deliberately
carries **no synthesis, no thesis, no frontier, no tier.** If it never
coalesces, it cost almost nothing and sits harmlessly in `notes/`. If it does,
`concept-coalesce` proposes promoting it and the synthesis is done *then*, with
the benefit of having seen where it went.

## Who emits stubs

Two producers, both **unambitious** — the point is that the promotion decision
is deferred, never made at capture:

1. **`signal-detector`** (ambient, conversational). When your human expresses an
   original idea — a thesis, an objection, a framing — file the `note` and set
   `is_concept_stub: true` when the idea is a *candidate lens* (a recurring
   way of thinking, not a one-off fact). Do **not** decide at capture whether it
   is a "reusable framework" vs "testable claim" vs "riff" — that triage is
   `concept-coalesce`'s job, later.
2. **Ingestion pipelines** (`paper-ingest`, `grant-ingest`, `literature-sweep`,
   `media-ingest`). When an ingested source surfaces an idea the existing
   concept layer does **not** already cover — a lens, a claim, a framing the
   source is advancing — file a `note` stub with `is_concept_stub: true` and a
   forward edge to the source page. This is the generalisation of the
   `author_on:`-edge pattern (`paper-ingest` Phase 8) to concepts: an ingest
   that touches an idea with no node stubs one, cheaply.

Both emit during their normal run; neither spawns a dedicated synthesis. A stub
is a side effect of capture, not a campaign.

## What a stub is not

- **Not a `concept`** — no `## Thesis` / `## Frontier` / `## Shifts`, no
  synthesis anatomy (`synthesis-layer-pages.md`). Naming it a stub but filling
  it like a concept defeats the purpose.
- **Not a `hypothesis`** — no testable claim tracked for evidence yet. A claim
  mature enough to test is a `hypothesis`, and that distinction is made at
  *coalescence*, not capture.
- **Not a duplicate of an existing page.** Before stubbing, check the concept
  layer: if a `concept` already covers the idea (or a `note` stub clearly
  does), add an edge to it rather than stubbing a near-duplicate. A re-stub of
  an idea that already has a node is noise, not signal.

## Promotion

`concept-coalesce` (the rem-cycle phase) reads every `is_concept_stub: true`
`note`, clusters them with the existing concept layer, and **proposes** (never
auto-executes — synthesis is propose-tier, `rem-cycle-contract.md`) promotions:
a stub cluster that clears a proximity + salience gate becomes a QUEUE proposal
to author a real `concept` (or `hypothesis`) page, folding the stub into it. A
stub that never coalesces is simply left in `notes/` — there is no cull, no
reaping pass. A cheap stub that goes nowhere deserves no cleanup cost.

## Anti-patterns

- Writing a concept stub into `concepts/` — the curated directory stays curated.
- Filling a stub with synthesis ("promoting early") instead of leaving it
  verbatim + provenance.
- Deciding at capture that an idea is "not a framework, so skip it" — the whole
  point is to defer that call.
- Stubbing an idea that already has a `concept` node — add an edge instead.
- Running a cull / merge-reap over stubs — an un-coalesced stub is harmless;
  leave it.
- Making a stub `status: promoted` by hand instead of letting `concept-coalesce`
  propose the promotion.
