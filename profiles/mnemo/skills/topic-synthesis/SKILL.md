---
name: topic-synthesis
description: Consolidate what the brain knows about a topic — synthesize many existing paper pages into one durable concept (a framework or principle) or hypothesis (a testable claim with evidence pro and con). Read-only against papers; writes a single new concept or hypothesis page.
triggers:
  - "synthesize what we know about"
  - "build me a concept page on"
  - "what does the brain say about"
  - "consolidate the papers on"
  - "synthesize across papers on"
  - "what's the brain's view on"
---

# topic-synthesis — consolidate paper pages into a durable concept or hypothesis

The brain accumulates `paper` pages faster than it builds the synthesis layer
above them. This skill closes that gap for one topic at a time: read every
relevant paper in the brain, pull the claims and the counter-evidence, and
write a single `concept` or `hypothesis` page that captures what *the brain*
already knows — cited back to its sources.

> **Conventions:** `skills/conventions/brain-first.md` (the lookup chain),
> `skills/conventions/quality.md` (citations, the notability gate, forward-only
> linking), `skills/conventions/graph-and-links.md` (typed edges),
> `skills/conventions/page-kinds.md` (concept vs hypothesis; readable short-name
> slug shape), `skills/conventions/capabilities.md` (the harness contract),
> `_brain-filing-rules.md` (file by primary subject),
> `_output-rules.md` (no slop).

## Capabilities

`brain-search`, `brain-read`, `brain-write`. Universal — works under any
harness. `brain-search` optional; falls back to keyword scan, with a
lower-recall caveat carried into the output.

## What this guarantees

- The synthesis is grounded in `paper` pages that actually exist in the
  brain — never fabricated from general knowledge, never silently
  expanded with external lit.
- The output is **one** page — a new `concept` or `hypothesis` (or an
  update to an existing one when the topic is already covered).
- Every substantive claim cites its source paper(s) by slug or DOI.
- Counter-evidence is *included*, not suppressed: a `hypothesis` page
  carries `supports:` and `refutes:` typed edges; a `concept` page
  names known limits.
- The new page forward-links to every source paper; backlinks are left
  for the `maintain` pass.
- A topic with too few papers refuses cleanly — synthesis from one or
  two papers is summary, not synthesis.

## Boundary against neighbouring skills

This skill is one of four ways to interrogate the brain. Pick the right one:

- **`query`** — answers a one-shot question, conversationally. Does not
  file a page. Use when your human wants the answer right now.
- **`literature-research`** — scans for *new* external literature on a
  topic and files a `note` with the delta. Use when the question is
  "what's new about X" — the brain is the baseline, the lit is the
  target.
- **`concept-synthesis`** — dedupes and tiers `concept`/`note` stubs
  capturing your human's *own* recurring thinking. Operates on your human's
  intellectual history, not on the literature. Use when "synthesize my
  concepts" or "find patterns across my notes."
- **`topic-synthesis` (this skill)** — consolidates *paper* pages into a
  durable `concept` or `hypothesis`. Operates on the literature already
  in the brain. Use when "what does the brain know about X" warrants a
  permanent page, not just a conversational answer.

A topic-synthesis output may later become an input to `concept-synthesis`
if your human riffs on the same idea in notes — that is fine; the two layer
without conflict.

## Phases

1. **Resolve the topic to a query.** Get a tight phrasing from your human if
   the request is vague ("what does the brain know about HIV bnAb
   germline targeting" is a topic; "antibodies" is not). The query is the
   axis the synthesis is organized around.

2. **Find the relevant `paper` pages.** Run `brain-search` for the
   topic; rank candidates by relevance and `importance`. Read the
   excerpts to confirm fit — drop the false positives. Aim for the
   genuine set, not a cap; a small topic has 3–8 papers, a large one has
   30+.

   - **Refuse cleanly below threshold.** Fewer than 3 relevant papers
     means there isn't enough in the brain to synthesize. Tell your human
     plainly; offer `literature-research` to expand the brain first, or
     `query` if the question is conversational.
   - **Flag stubs.** A `paper` page with `needs-ingest: true` is a stub —
     it has frontmatter but no distilled body. Synthesizing from stubs
     is risky. Either run `ingest-pending-papers` first to drain the
     queue, or proceed with the caveat (noted in the output) that
     evidence is preliminary.

3. **Read and extract.** For each paper page (`brain-read`), pull:
   - The **claims** the paper actually makes (`## Findings`,
     `## Analysis`).
   - The **evidence** the paper rests on (assay, cohort, sample size,
     effect size where stated).
   - **Counter-evidence** or limits the paper itself acknowledges
     (`## Limitations`).
   - The paper's identifier (DOI / PMID) and slug for citation.

   Maintain claim / evidence / hope separation (`SOUL.md` §3): what was
   shown, what was concluded from it, what would merely be nice.

4. **Choose the page kind.**
   - **`concept`** when the synthesis is a *framework* or *principle* —
     a way of organizing what the field believes ("affinity maturation
     trajectories in HIV bnAb lineages"). Concepts can carry tension
     without being broken; they describe the shape of the field.
   - **`hypothesis`** when the synthesis is a *testable claim* — there
     is something the literature would either support or refute, and
     papers genuinely fall on both sides ("germline-targeting
     immunogens elicit broadly neutralizing precursors at clinically
     useful frequencies"). Hypothesis pages carry typed `supports:` /
     `refutes:` edges to the source papers.
   - **If genuinely ambiguous** — the topic could honestly be either —
     gate on your human via `skills/ask-user/SKILL.md`. Do not silently pick;
     the choice is load-bearing for how the page reads.

5. **Draft.** Write the page in the documentary register the brain uses
   for `concept` and `hypothesis` (see existing examples once they exist;
   for now, mirror the structured `Analysis` voice of well-distilled
   `paper` pages). Cite every claim inline with the source paper slug
   and DOI. For a hypothesis, build evidence-pro and evidence-against
   sections explicitly; do not bury contradictions in prose.

6. **File.** Write the page (`brain-write`) at `concepts/<slug>.md` or
   `hypotheses/<slug>.md`. Slug shape: lowercase, hyphen-separated,
   readable short-name per `skills/conventions/page-kinds.md` "Slug
   conventions." Frontmatter follows the spine plus per-kind fields
   (`skills/conventions/frontmatter.md`). Forward-link to every source paper in
   the body (`[[papers/<slug>]]`) and in the `links:` (or `supports:` /
   `refutes:` for a hypothesis) typed edge list. Never hand-write
   backlinks — the `maintain` pass picks up the reverse edges
   (`skills/conventions/graph-and-links.md`).

   - **Existing page on the topic.** If `brain-search` surfaces an
     existing `concept` or `hypothesis` page for the topic, gate via
     `ask-user`: **(a) update in place** (read current state, add the
     new synthesis without clobbering — the never-blind-overwrite rule
     in `SOUL.md` §2 spine applies), **(b) refuse and route to
     `restructure-thin-page`** if the existing page is a stub that needs
     restructuring first, or **(c) cancel** if the existing page is
     fine.

## As a rem-cycle phase

Invoked by the orchestrator as part of **phase 5 (consolidation)**, this skill
does **not author** in an unattended run (`skills/conventions/rem-cycle-contract.md`) —
authoring a durable page is expensive, quality-sensitive, and the graph is
your human's to curate. It **detects and proposes** instead:

- **Mode.** `dry-run` (report only) or `normal` (queue the proposals).
- **Detect ripe topics.** Cluster `paper` pages by the ripe signals —
  **`project` membership** and **shared-tag co-occurrence** are first-class
  (papers link the project/tag layer far more than the concept layer), alongside
  a dead `concepts/<slug>` linked by **≥3** papers (`maintain`'s
  under-population signal) and co-citation. A ripe topic clears **≥3 papers** and
  has **no** existing `concept`/`hypothesis` page.
- **Propose, never write.** For each ripe topic emit a `proposed[]`
  `category: synthesis` entry with the phase-specific fields
  (`rem-cycle-contract.md`): `kind` (recommended `concept` vs `hypothesis`) and
  `kind_ambiguous: true` when the pro/con test can't settle it — uniform support
  with an unresolved-*future* "con" is not literature disagreement; flag it and
  your human picks the kind on approval. Plus `sources`, `outline`, `coherence`
  (`tight` = a real draft head-start / `loose` = a strawman your human will re-scope),
  and `related_proposals` for topics sharing sources (so two half-overlapping
  pages aren't both authored). `target_exists: false`. Authoring happens on
  approval (a waking `topic-synthesis` run), never in the dream.
- **Output.** The fenced-yaml phase result — an empty `committed[]` (this
  delegate authors nothing unattended), `proposed[]` syntheses, `metrics`
  (`topics_ripe`, `syntheses_proposed`, `papers_scanned`). No chaining.

## Output

A single new (or updated) `concept` or `hypothesis` page, plus a short
report to your human: the topic, the page kind chosen and why, the count of
source papers, any stubs flagged, the path to the new page. The page
itself is the deliverable; the report is for traceability.

## Anti-patterns

- **Synthesizing from zero or one paper.** Refuse the request — there is
  nothing to consolidate. Use `query` or `literature-research` instead.
- **Filing a `concept` when the synthesis is a testable claim.** If
  papers fall on both sides of a question, it is a `hypothesis`. Use the
  pro/con structure; do not hide the disagreement in concept prose.
- **Synthesizing from stubs without flagging them.** A `needs-ingest:
  true` paper page has no body to read from; treating it as ingested
  silently inflates the evidence count.
- **Fabricating connections that aren't in the source papers.** Every
  synthesis claim points back to a paper that actually makes it; "the
  literature converges on X" is fine only when X is something multiple
  papers actually argue.
- **Going external.** This skill is brain-first by construction — if the
  brain is thin on the topic, the right answer is `literature-research`
  to expand the brain *first*, not to inject external literature into
  this synthesis pass.
- **Hand-writing a backlinks section.** Forward-only — the `maintain`
  pass picks up reverse edges (`skills/conventions/graph-and-links.md`).
- **Blind-overwriting an existing page on the topic.** Gate via
  `ask-user`; honor the never-blind-overwrite rule.
