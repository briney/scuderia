---
name: literature-dive
description: Use when conducting a deep literature dive. Discover and ingest selected evidence, run one informed supplementary pass, and synthesize.
triggers:
  - "deep literature dive"
  - "literature dive on"
  - "comprehensive literature review of"
  - "deep dive into the literature on"
  - "systematic literature dive"
eval_contract:
  goal: Build a source-grounded literature corpus and synthesis through approved tiering and one informed supplementary pass.
  dimensions:
    - "SEARCH — expert curation, gap analysis, learned vocabulary, alternatives, and bounded expansion survive"
    - "EVIDENCE — tiers and findings are attributed to sources actually read"
    - "OWNERSHIP — independent paper workers have clear scope; the parent owns shared writes"
    - "COMPLETION — bibliography decisions, shared wiring, verification, and synthesis are accounted for"
  hard_fails:
    - Claiming skipped bibliography walks created stubs or unread review text established detailed discussion.
    - Clearing enrichment on an abstract-only or substitute-preprint page.
    - Synthesizing as if unwired or unverified intermediates were completed ingests.
---

# literature-dive — deep literature exploration

A literature dive is not a single paper ingest and not a standing scan. It
is a *campaign*: discover the foundational literature, ingest it
tier-by-tier, search for what the initial discovery missed, run one
informed supplementary pass with the context the dive has acquired, and
synthesize the result into a durable concept page. The default entry
point is a recent high-impact review, because reviews in high-impact
journals are information-dense maps of a field — the load-bearing
primary papers, the open questions, the structural tensions — so the
dive begins with expert curation, not algorithmic ranking. For fields
moving too fast for reviews to keep up, semantic search is the discovery
engine instead (Phase 1 covers both paths).

Either way, the initial discovery pass runs *uninformed*: before the
dive, the brain lacks the context to know which jargon, which
neighboring subfields, and which uncited-but-load-bearing papers matter.
That is why the dive ends with an informed supplementary pass (Phase 6)
before synthesis — the second pass uses everything the first pass
learned.

**Ownership split.** `paper-ingest` owns retrieval, per-paper acceptance,
author wiring, and verification — load it, do not restate it.
`batch-drain` owns runtime sizing and dispatch/return discipline.
`topic-synthesis` owns concept-page splitting, supersession mechanics,
and link verification (Phase 7 names the dive-specific triggers). This
skill owns the scientific search design: entry selection, tiering, the
supplementary pass, and the synthesis gate.

**Conditional references (load only when the condition holds):**

- `references/entry-modes.md` — load when the entry point is anything
  other than a straightforward recent-review search (semantic-first or
  anchor-set entry), when a paywalled review's reference list must be
  obtained from graph APIs, when Tier 1 must be identified without a
  bibliography, when validator HOLD entries need resolution, or when
  tiering from an HTML citation graph.
- `references/supplementary-search.md` — load for Phase 6, Prong 2b
  (axis-reframed queries) especially.
- `templates/gap-map.md` — copy-and-fill template for Phase 6.1.
- `paper-ingest/references/script-commands.md` — load before invoking
  any helper or running search/retrieval commands (host execution
  discipline, supported command forms, source-specific failure recovery,
  and rate limits).

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/brain-first.md` (check the brain first),
> `skills/conventions/quality.md` (citations, forward-only linking),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/conventions/test-before-bulk.md` (validate before scaling),
> `skills/conventions/paper-stubs.md` (queue/provenance).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url` (`pubmed-fetch`,
`crossref-fetch`, `biorxiv-fetch`, `arxiv-fetch`), `spawn-subagent`.

## Environment preflight

- Check runtime capabilities and process limits before large dispatches;
  follow batch-drain and the conditional helper reference. Do not assume
  a terminal shell's `ulimit` changes the running agent's FD limit.
- **Provider/delegation failure.** An HTTP 429 or capacity error is not
  evidence that full text is unavailable. Inspect written files after
  workers have returned; preserve valid intermediates and defer
  failed/unstarted queued fills per `ingest-pending-papers`. A provider
  failure does not establish source closure and never licenses
  abstract-only closure with `needs-enrichment: false` — `paper-ingest`
  owns the retrieval ladder and source-completeness gates; genuine
  abstract-only distillation sets `fulltext_source: abstract-only` with
  `needs-enrichment: true`, and a substitute preprint also retains
  enrichment.

**Crash recovery.** Reconstruct phase, selections, and dispatched work from
session history and saved state. Diagnose the actual runtime failure before
restarting anything; never restart an active writer's session. Reconcile
partial output as below rather than restarting discovery from Phase 1.

**Resume on verified completion, not reported status.** A dive
interrupted mid-flight may have been continued by another session (cron,
a parallel chat, a later restart). A worker can also report a provider
failure after writing useful output. Before re-dispatching
anything, reconcile three sources — the dive's state doc
(`working-docs/<dive>-state.md`), `git log` filtered to the dive's
commit-naming pattern, and the filesystem — and treat the state doc's
markers as claims to verify, not facts: files can exist yet be partial;
an item marked DISPATCHED may be committed and wired on disk; a
never-started item was never "reported failed." For each item, inspect
the canonical path, readiness (body/source checks), wiring, and
provenance, and resume only the unmet obligations — re-dispatch nothing
that verification shows complete, and never re-dispatch while another
writer is actively working the dive. Fix stale state-doc lines after
verification; maintain the state doc from the first dispatch onward so
this reconciliation is possible at all.

## The two-tier citation system

The dive introduces an explicit tiering for the papers surfaced by a
review's bibliography — a refinement of `paper-ingest` Phase 7's
single-tier stub system, because reviews cite more broadly than primary
papers and the dive needs a way to triage a large bibliography.

| Tier | What it is | Ingestion path |
|---|---|---|
| **Tier 1 (primary)** | The review itself + primary literature the review discusses in detail | Priority paper-ingest, normally in isolated workers; no citation threshold or prerequisite stub. |
| **Tier 2 (secondary)** | Load-bearing citations from Tier 1 papers (methods, datasets, frameworks) | `paper-ingest` Phase 7 stub + threshold gate (5+ `cited_by`). Full ingest deferred to `ingest-pending-papers`. |
| **Dropped** | Background/context citations | Not paged. |

**The Tier 1 bar: "review discusses this paper in detail."** Looser than
`paper-ingest` Phase 7's anchor test ("the paper would lose its argument
without this reference"): a paragraph or more on a paper's findings,
methods, or implications can establish substantive discussion; repeated
citations help locate passages but do not establish the tier alone. A single
cite for a background fact does not qualify. There is no target Tier 1 count. Paper priority and author promotion
are separate — Tier 1 bypasses the paper queue's citation threshold;
author ledger/promotion rules still apply (paper-ingest Phase 8).

## Phases

### 1. Review discovery

Three entry modes; the mechanics of each live in
`references/entry-modes.md` — load it for any mode whose detail you
need:

| Mode | When | Core action |
|---|---|---|
| **Review-anchored** (default) | A recent high-impact review exists | Search PubMed for recent reviews in whitelisted journals; present 3–5 candidates for selection |
| **Semantic-first** | Field moves faster than reviews (6–12 months) | `paperclip search` with 6–10 queries grouped by cluster; present the cluster map + candidate count for scope approval |
| **Seed-corpus (anchor set)** | Human hands you a paper whose load-bearing references form a near-complete causal chain | Resolve and validate the anchors (Phase 3.5), ingest under Phase 4's modes, run review discovery in parallel |

**Journal whitelist (review-anchored mode):** Nature Reviews family;
Trends in family; Annual Reviews family; Cell, Nature, Science reviews
and perspectives; F1000Prime reviews; a bioRxiv/medRxiv review preprint
qualifies on merit if by a recognized authority.

Present the candidates with: title, journal, year, first author, a
one-line description of the review's scope (from the abstract). Let your
human pick 1–3. **Brain-first check:** before presenting, search the
brain for existing review pages on the topic; if a relevant review is
already ingested, note it and offer to use it as a starting point.

The two discovery methods are complementary, not substitutes: a survey
provides taxonomy while semantic search finds the frontier it missed, and
the two surface different Tier 1 sets — neither subsumes the other. Some
dives use both.

### 2. Review ingest

Use `paper-ingest` for selected reviews, delegating to isolated workers
when helpful. Reuse existing verified pages. Review selection already
authorizes the work; no prerequisite stub or separate delegation approval
is needed.

**Unavailable review body.** Follow paper-ingest's retrieval attempts and
closure rules, including authorized browser/repository routes. Justified
abstract-only distillation retains enrichment. A reference list supports
candidate discovery and citation provenance, not claims about unread detailed
discussion; use the alternate-review or targeted-search branch for tiering. The
reference-list discovery ladder (Semantic Scholar → OpenAlex → Europe
PMC, plus the all-empty fallbacks) lives in `references/entry-modes.md`.

**Incremental validation.** After the first review is ingested, pause.
Read the paper page back: source-grounded distillation, declared limitations,
and either a verified reference list or the explicit bibliography-less branch. If the quality is good, proceed to Phase 3; if not, fix the
approach before scaling to additional reviews.

**Review bibliography ownership.** Skip paper-ingest's automatic Phase
7 stub creation for the review; the dive primary classifies the fetched
reference list in Phase 3. Save its source and identifiers. No stubs are
assumed to exist as a result of the skipped phase — Phase 3 compares
candidates against existing brain pages, not imaginary stubs.

### 3. Tier classification

Read the review's full discussion where available and its fetched
reference list. Classify the full reference list, including candidates
beyond the primary-paper anchor test.

**Tier 1 — priority ingest.** A reference qualifies when the review
discusses its findings/methods/implications in detail or repeatedly
across sections — *and it adds new signal* (the non-duplicative filter
below). Read that discussion to establish the bar: a reference list
alone cannot show how a paper was discussed. If the review body is
unavailable, use the alternate-review or targeted-search path
(entry-modes.md) and state that basis explicitly — verified citation
provenance, not a bare list, is what assigns the tier. Approved Tier 1
sources use the same paper-ingest workers whether new or already
stubbed; reuse existing full pages.

**Tiering from the citation graph — an evidence locator, not a
classifier.** When the review is read as HTML, the body's citation
anchors encode which paragraphs cite which reference. Use the tally of
citing paragraphs/sections to prioritize *reading*: heavily-cited
papers get their citing passages read first; a single-paragraph cite
gets its paragraph read before classification (load-bearing mechanism
papers are often cited once, in the paragraph that recounts them). No
paragraph-count threshold assigns a tier by itself — the bar stays
"discusses in detail," established by reading. Preserve the
anchor→reference map with a DOM walk over the article body BEFORE
converting to plain text — text conversion strips the citation markers;
if conversion already destroyed them, re-fetch the source HTML, which
may recover the lost anchors. Publisher-specific DOM detail (the
observed Nature selector and reference-list shape) lives in
`references/entry-modes.md`.

**Tier 2 — threshold-gated stubs.** Create or update source-grounded
load-bearing references (methods, datasets, frameworks) using
`skills/conventions/paper-stubs.md`. During Tier 1 ingestion, the
primary or queue-drain parent performs each paper's Phase 7 walk;
page-only leaves do not create these stubs. A deferred walk is an
explicit outstanding obligation, not confirmation that stubs are in
place.

**Dropped — not paged.** Background/context references do not become
stubs. Neither topic relevance nor campaign selection creates a
`cited_by` edge; only verified citation relations do.

**Dedup against the brain.** Before presenting, check each Tier 1 DOI
against existing `papers/` pages; already-ingested papers are listed
but not re-ingested.

**Non-duplicative filter (standing rule for large dives).** Before
ingesting a Tier 1 candidate, ask: does this paper add something the
brain does not already hold, and something a sibling Tier 1 paper in
the same dive does not already cover? A review that "discusses in
detail" a topic the brain already ingested in a prior dive does **not**
need a second full ingest — note it as already-covered and drop it.
When the dive spans multiple axes, prefer one load-bearing paper per
axis over several that recapitulate the same axis.

**PubMed-driven Tier 1 identification (no bibliography available).**
When the spine review's reference list is unavailable (all sources
empty), identify Tier 1 through targeted PubMed searches instead of a
curated bibliography — the query set and the stricter bar are in
`references/entry-modes.md`.

**Output of this phase:** a list of Tier 1 papers (DOI + title +
one-line reason and source basis for tier classification), plus the
Tier 2 stubs actually created and any explicitly pending bibliography
decisions. Present the Tier 1 list to your human for a quick sanity
check before ingesting — the one gate where a human glance is cheap and
valuable.

### 3.5. Validate identifiers before presenting

Tier-1 identifiers harvested from a review's bibliography (Semantic
Scholar references API, or LLM transcription of the reference list) are
wrong at observed rates of ~70% (ebolavirus dive, 2026-08-05: 7 of 10
Tier-1 task contexts had a wrong PMID, DOI, or both — one DOI off by a
single digit). Before presenting the Tier-1 list to your human, run the
pre-dispatch validator over every candidate:

```bash
python3 skills/paper-ingest/scripts/validate_identifiers.py \
    --batch /tmp/tier1_citations.json --recover
```

Build the batch JSON from the Tier-1 list: `title`, `author`
(first-author surname), `year`, plus any `pmid`/`doi`/`pmcid` already in
hand (~2s per citation). Present your human the *validated* list:
`validated` entries as-is; `recovered` entries with corrected
identifiers; `HOLD` entries flagged for manual resolution, never
silently dispatched. HOLD entries with PMIDs get one PubMed `esummary`
batch check before discard — known false-HOLD shapes (older-paper
title formatting, hyphenated surnames, curly apostrophes, bare-digit
and legacy PMCIDs) are enumerated with the verification recipe in
`references/entry-modes.md`; do not discard a paper solely because the
title-match heuristic failed. Any entry flagged `retracted: true` is
surfaced to your human explicitly, not ingested unattended. Phase 4
uses the validator's `dispatch` output as the validated candidate
list, not as delegation authorization; never use the raw bibliography
identifiers.

### 4. Tier 1 ingest

Delegate one selected paper per isolated paper-ingest worker; new
papers and existing stubs use the same page-only mode. A small
standalone ingest can run inline. The dive's existing selection/tiering
rules are sufficient; add no eligibility classifier, approval manifest,
or mandatory session boundary.

Load `skills/batch-drain/SKILL.md` for runtime sizing and dispatch/return
handling. Give each worker the source identifier, assigned output path,
campaign purpose, and unique scratch prefix. Workers read and distill
their sources, return PAGE_READY and source-linked bibliography
candidates, and do not mutate shared files or perform Git operations.
Save campaign progress between waves; do not accumulate every worker's
full extraction transcript in the parent.

**Briefs are source-grounded inputs, not primary evidence.** Authorship,
cohorts, and findings in a brief must come from the source metadata or
abstract read for that input, not recollection; the worker still verifies
the brief against the retrieved paper (paper-ingest's brief-vs-fulltext
reference owns the check).

**Parent wiring.** The parent verifies each PAGE_READY page and its
source-linked bibliography candidates — opening original passages as
needed, not re-reading every manuscript — then performs paper-ingest
Phases 7–9 through
`paper-ingest/references/author-ledger-mutation.md`, which owns
name/slug resolution, ORCIDs, promotion, plain-text mutation, and
read-back. Do not reconstruct the wiring table from a truncated
subagent summary or duplicate its mutation algorithm here.

**Verification and failure recovery.** Follow paper-ingest Phase 10 and
the drain's per-item accounting. Check every returned item on disk
regardless of reported success/failure — a provider can fail before
writing or after a useful intermediate is written, and neither file
existence, headings, nor author count alone establishes a completed
ingest. A page-only result stays queued until parent wiring is complete.
Confirm the actual canonical path after any parent-owned merge;
source-check conflicting identifier resolutions. Do not mutate shared
state while a leaf is still writing.

**Foreground work during a wave.** Only work independent of its outputs
may proceed: read existing concept pages, design searches from the
already-read review, or compile a scratch map. Do not synthesize from
unfinished papers, judge their coverage before read-back, or start
another dispatch. Close coherent verified ingestion units through
git-ops after required wiring; wave completion alone is not the commit
boundary.

### 5. Review-inspired search

After the review and Tier 1 papers are ingested, identify what the
review missed and search for it. **Three search targets:**

1. **Open questions the review names explicitly** ("future directions,"
   "remains unknown," "remains to be determined" sections) — for each,
   run a targeted PubMed/bioRxiv search.
2. **Thin evidence areas** — where the review says data is lacking or
   conflicting, search for papers published since the review's citation
   cutoff that might fill the gap.
3. **Post-review developments** — papers published after the review's
   last citation date; search with a date filter from the review's
   submission date forward.

New papers found are Tier 1 when they directly address an open question
with new primary evidence; Tier 2 still requires a load-bearing citation,
not merely peripheral relevance. Background-only results are dropped;
Tier 1 candidates get identifier validation per Phase 3.5 before
ingestion, and clear the same non-duplicative filter as Phase 3.

**Semantic search (paperclip), conditional.** Open questions and
thin-evidence areas are naturally *semantic* queries — the relevant
papers often use different vocabulary than the review does, which is
exactly where PubMed keyword templates lose recall. When the
`paperclip` CLI and `PAPERCLIP_API_KEY` are available (see the
`paperclip-search` skill), run one semantic query per open question
alongside the PubMed search, phrased in plain language rather than
keyword syntax. If the binary or key is absent, skip silently: keyword
templates are always the default path.

**Stopping criterion.** One round of targeted searches per open
question. If a search surfaces 3–5 new papers, classify and
ingest/stub. Do not recursively expand — the dive stops when new
searches surface already-ingested papers (diminishing returns). A query
that surfaces nothing new is weak evidence, not proof the review was
comprehensive: a badly-framed query also returns nothing, so treat an
empty result as a signal about the query as much as the field.

**Concurrent search is conditional.** While a paper-ingest wave is
running, searches derived solely from the already-read review may
proceed. Searches or coverage judgments that require the wave's unread
outputs wait for its return and verification.

### 6. Informed supplementary pass

The initial pass (Phases 1–5) ran uninformed. Phase 6 is a second,
bounded pass that uses everything the dive has learned to find what the
uninformed pass was structurally incapable of finding. It runs ONCE per
dive, after Phase 5 and before synthesis — so the synthesis (Phase 7)
is built once, over the complete corpus, rather than patched after the
fact.

#### 6.1 The gap map

Read the ingested corpus and write a gap map at
`working-docs/gap-map-<topic>.md` (a transitory working document — no
frontmatter, no lifecycle, not a brain page). A gap belongs on the map
only when all three criteria hold:

1. **Existence** — reasonably high confidence that a gap in our knowledge
   actually exists (not a suspicion, a specific missing piece).
2. **Addressability** — there might be literature the initial ingestion
   missed that could help close it.
3. **Meaningfulness** — leaving the gap unfilled would mean our
   understanding of the topic is incomplete in a meaningful way. This is
   the most important criterion: the map holds MEANINGFUL gaps, not
   trivialities.

There is no minimum and no maximum — zero is a valid count. A dive that
surfaces zero clear gaps proceeds with an empty gap map (prong 1 is
simply skipped); a dive that surfaces 10+ meaningful gaps fills 10+.
Never identify trivial gaps to pad the map. Meaningful examples: for a
dive on models for a specific task, a referenced-but-uningested model
is a meaningful gap; so is a benchmarking study that introduces no new
model but compares models already in the corpus. A minor parameter
variation on an ingested method is not.

The gap map later feeds the concept page's Open Questions section in
Phase 7 — write it with that reuse in mind. A template with format and
examples lives at `templates/gap-map.md`.

#### 6.2 Three discovery prongs

Run all three prongs (subject to the gap map), then consolidate their
candidates in 6.4.

**Prong 1 — gap queries.** For each gap on the map, run one semantic
query against domain-appropriate sources (e.g. `-s pmc,biorxiv,medrxiv`
for biomedical topics, `-s arxiv,biorxiv` for ML) and one keyword query
in a relevant index (PubMed for biomedical topics), phrased to target the
gap. When paperclip is absent, the keyword query is the path.

**Prong 2 — jargon-upgraded queries.** The initial queries were written
in naive vocabulary. Harvest the terminology the dive has acquired —
assay names, model names, domain-specific jargon — from the ingested
paper pages, and identify terms that appear across multiple Tier 1
pages but were absent from the original Phase 1/5 query set. Regenerate
the keyword and semantic queries with the learned vocabulary and run
them. A useful self-check: if an original query returned near-zero hits
where a jargon term now returns many, that quantifies what the
uninformed pass missed.

**Prong 2b — axis-reframed queries.** Jargon upgrades keep the dive's
original *axis*. A corpus can still be structurally blind on the
orthogonal axis — the dimension the original query set was never framed
on (for a systems corpus, often how the systems are *built* rather than
what they do; adapt to the actual domain — it is not always
infrastructure). The method: (1) find the machinery layer's own name for
itself — often coined in industry posts rather than papers, so check
the anchor paper's related-work section for blog/repo citations that
name the practice; (2) run 6–10 plain-language semantic queries on that
vocabulary; (3) dedup against the vault; (4) quantify new-vs-known. A
high new fraction is evidence the initial pass had a structural blind
spot — surface it to your human, who decides whether a supplementary
dive on that axis is warranted before synthesis. If the new axis has
grown to rival the original, propose the concept-page split gate
(Phase 7) before ingesting. The generalized method and worked example
live at `references/supplementary-search.md`.

**Prong 3 — informed snowball.** Read the bibliographies of the dive's
Tier 1 papers with the dive's full context and identify references worth
ingesting. The candidate pool includes the Tier 2 stubs the bibliography
walks created, but the selection is *judgment, not a citation-count
threshold*. A reference qualifies when it is any of:

- **Load-bearing** — an ingested paper's argument, method, or dataset
  depends on it.
- **An alternative approach** — a rival method or competing hypothesis
  not well covered by the ingested corpus, *whether or not it worked*.
  Negative results and abandoned lines of work matter: they keep us
  from repeating past failures, and they map the graveyards.
- **Foundational background** — the intellectual or conceptual roots of
  current approaches. Not the state of the art, but necessary to
  understand why the state of the art looks the way it does.
- **A conceptual or technical innovation** that matters for fully
  understanding the topic or domain.

**Bias toward inclusion.** For deep dives, the token cost of ingesting a
redundant or marginally informative paper is far lower than the cost of
missing something truly valuable. When in doubt, put the candidate on
the list — the human approval gate (6.4), not a rigid filter, is the
volume control.

#### 6.3 Review rediscovery — the re-anchor

If the supplementary searches surface a high-value review the initial
pass missed, treat it as evidence the initial dive had at least one
structural gap — and potentially others. This triggers a **re-anchor**
(Phase 1 lite): obtain the new review's reference list (Phase 2 ladder),
classify its bibliography against the already-ingested corpus, and add
the Tier 1 candidates it implies to the supplementary list. If multiple
new reviews surface, re-anchor on each. A re-anchored review's
bibliography is mined with the same tier bars and the same
non-duplicative filter as Phase 3 — most of its references will already
be ingested; the value is in the ones that are not.

**Once per dive.** If a re-anchor uncovers *yet another* high-value
review, a second supplementary pass requires your human's explicit
approval. State clearly what was found and let him decide. This is the
guard against recursive expansion.

#### 6.4 Consolidation and ingestion

1. Merge the candidates from all three prongs (and any re-anchor).
2. Dedup against the brain and against the dive's existing corpus.
3. Validate identifiers per Phase 3.5 (validator + PubMed batch
   verification for HOLDs).
4. Present the consolidated list to your human, with the reason each
   candidate was surfaced (which gap, which prong, which re-anchored
   review). This is the approval gate.
5. Ingest approved candidates through the same Phase 4 paper workers,
   with parent verification and shared wiring.

**Hard rules.**
- Phase 6 executes exactly once per dive.
- No numeric caps and no citation-count thresholds anywhere in Phase 6 —
  judgment plus the human gate governs volume, with an explicit bias
  toward over-ingesting.
- The Phase 5 stopping criterion still applies within each search: when
  searches return only already-ingested papers, stop.

#### 6.5 Tier 2 processing (unchanged)

Tier 2 papers — from the initial pass and the supplementary pass alike —
stay as stubs created by `paper-ingest` Phase 7. The standard threshold
gate applies: when 5+ independent sources cite a stub,
`ingest-pending-papers` drains it. Confirm each stub's queue flag
follows the shared stub contract: false below threshold unless another
producer already queued it; true at threshold. Never reset an already
queued stub to false. Do not inline-ingest Tier 2 — that is the
exploding paper tree the threshold gate exists to prevent. (Phase 6's
informed snowball is the judgment-driven exception: papers it promotes
are reclassified Tier 1 by human approval, not inline-ingested as
Tier 2.)

### 7. Synthesis

After the supplementary pass is complete, synthesize the result.

**Close ingestion units before synthesizing.** The dive parent completes
required wiring and validates each coherent ingestion unit, then commits
and pushes it through `skills/git-ops/SKILL.md`. Dispatch size does not
determine commit size. The final verified concept synthesis is a separate
unit. Do not commit unrelated pending work or rewrite earlier history.

**Default: invoke `topic-synthesis`.** The dive has now populated the
brain with a review + its foundational literature + the supplementary
pass's additions. `topic-synthesis` consolidates these paper pages into
a single durable `concept` page (or `hypothesis`, when the literature
genuinely falls on both sides of a testable question — the choice is
topic-synthesis's Phase 4) that captures what the brain now knows about
the topic, cited back to the source papers, with tensions and open
questions made explicit. Feed the gap map (6.1) into the concept page's
Open Questions section. The skill is brain-internal — by the time it
runs, the dive has already done the external work; the synthesis is the
internal consolidation of what was ingested.

**Existing concept or hypothesis page — human gate.** If the brain
already has a `concept` or `hypothesis` page for the topic,
`topic-synthesis` gates via `ask-user`: update in place, restructure,
split, or cancel. The dive never authors or restructures an existing
concept page unattended — a change to an existing page needs the human
gate.

**Concept-page split (human-approved, before supplementary wiring).**
When a dive reveals that a concept page is carrying two literatures
that cite each other sparsely and are searched with different
vocabulary, ask whether to split into sibling pages BEFORE ingesting
the supplementary corpus — pages wired once into the right concept are
cheaper than pages re-sorted afterward. The split mechanics (sibling
creation, frontmatter inheritance, cross-linking, Shifts entries, the
no-bulk-repoint rule) are owned by `topic-synthesis`'s split protocol.
After an approved split, the synthesis may produce the sibling pair —
one run covering both pages — and each supplementary paper wires into
the page whose axis it actually evidences (a paper load-bearing for both
axes links from both); do not assume every new paper belongs to the new
page regardless of relevance.

**Concept-page supersession (extending to a broader scope).** When the
dive extends an existing concept page to a genuinely broader scope
(e.g., ebolavirus to filovirus-wide), supersede-and-redirect is another
human-approved option; the full protocol (dormant redirect
stub, preserved Shifts log, no bulk link updates) lives in
`topic-synthesis`'s supersession mechanics. Supersession is right when
the dive's scope genuinely exceeds the old page's scope and the old
content is fully subsumed; ask your human whether to update in place,
supersede, or create a fresh independent page.

**Concept-page link verification.** After enriching a concept page,
verify every frontmatter `links:` entry and body wikilink resolves on
disk, testing both path forms — the `.md`-extension trap and its fix
are owned by `topic-synthesis`'s verification step.

**The synthesis is the deliverable.** The individual paper pages are
the evidence base; the concept page is the output your human reads. The
dive is not complete until the concept page is written.

## Non-negotiable checks

Do not replace substantive tiering with citation counts, skip source/artifact
read-back, inline-expand the Tier 2 tree, or synthesize from PAGE_READY work.
Do not omit or recursively repeat the supplementary pass; extra expansion
requires the existing human gate. A completed dive includes verified synthesis,
not just paper files. Shared writes and Git closeout remain parent-owned.
