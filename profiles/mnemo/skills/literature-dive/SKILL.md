---
name: literature-dive
description: A structured deep literature dive — start from recent high-impact reviews, ingest the review and its foundational primary literature, then search for developments the review missed, and synthesize the result into a concept page.
triggers:
  - "deep literature dive"
  - "literature dive on"
  - "comprehensive literature review of"
  - "deep dive into the literature on"
  - "systematic literature dive"
---

# literature-dive — review-anchored deep literature exploration

A literature dive is not a single paper ingest and not a standing scan. It
is a *campaign*: start from a recent high-impact review, use the review as
a curated map to the foundational primary literature, ingest that
literature tier-by-tier, search for what the review missed, and synthesize
the result into a durable concept page.

The review is the entry point because reviews in high-impact journals are
information-dense maps of a field — they identify the load-bearing primary
papers, the open questions, and the structural tensions. Starting from a
review (rather than a keyword search) means the dive begins with expert
curation, not algorithmic ranking.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `conventions/brain-first.md` (check the brain first),
> `conventions/quality.md` (citations, forward-only linking),
> `conventions/capabilities.md` (the harness contract),
> `conventions/test-before-bulk.md` (validate before scaling),
> `conventions/preprint-retrieval.md` (bioRxiv full text).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url` (`pubmed-fetch`,
`crossref-fetch`, `biorxiv-fetch`, `arxiv-fetch`), `spawn-subagent`.

## The two-tier citation system

The dive introduces an explicit tiering for the papers surfaced by a
review's bibliography. This is a refinement of `paper-ingest` Phase 7's
single-tier stub system, motivated by the fact that reviews cite more
broadly than primary papers and the dive needs a way to triage a large
bibliography.

| Tier | What it is | Ingestion path |
|---|---|---|
| **Tier 1 (primary)** | The review itself + primary literature the review discusses in detail | Full `paper-ingest` immediately. No stub. Bypass the threshold gate. |
| **Tier 2 (secondary)** | Load-bearing citations from Tier 1 papers (methods, datasets, frameworks) | `paper-ingest` Phase 7 stub + threshold gate (5+ `cited_by`). Full ingest deferred to `ingest-pending-papers`. |
| **Dropped** | Background/context citations | Not paged. |

**The Tier 1 bar: "review discusses this paper in detail."** This is
looser than `paper-ingest` Phase 7's anchor test ("the paper would lose its
argument without this reference"). A review that devotes a paragraph or
more to a paper's findings, methods, or implications — citing it
repeatedly across multiple sections — clears the Tier 1 bar. A review
that cites a paper once for a fact ("humans have ~10¹⁰ B cells [42]")
does not. The typical review has 200–300 references; Tier 1 is usually
10–20.

**The ledger bypass.** Tier 1 papers bypass the `people/_ledger.yaml`
threshold gate *for the paper itself* — they get a full `paper-ingest`
immediately, not a stub. The **author ledger** still applies normally:
Tier 1 authors go through the standard three-branch logic in
`paper-ingest` Phase 8 (existing page → append `author_on`, ledger entry
→ append citation, new → create ledger entry). The bypass is about the
*paper's* ingestion priority, not the author pipeline.

## Phases

### 1. Review discovery

Search PubMed for recent reviews on the topic, filtered to high-impact
review journals. Present 3–5 candidates for Bryan's selection.

**Journal whitelist:**
- Nature Reviews family (Immunology, Microbiology, Drug Discovery, etc.)
- Trends in family (Immunology, Microbiology, Parasitology, etc.)
- Annual Reviews family (Immunology, Microbiology, etc.)
- Cell, Nature, Science — reviews and perspectives
- F1000Prime reviews
- A bioRxiv/medRxiv review preprint qualifies on merit if by a recognized authority

**PubMed search template:**
```
esearch -db pubmed -query "<topic>[Title/Abstract] AND (review[pt] OR
review literature[pt]) AND (<whitelist journals>)" -mindate <2-3 years>
```

If PubMed returns too few, broaden: drop the journal filter, widen the
date range, or search bioRxiv. If too many, narrow: add the `review[pt]`
publication type filter, or prioritize by citation count (PubMed
Relative Citation Ratio if available, or CrossRef citation count).

Present the candidates with: title, journal, year, first author, a
one-line description of the review's scope (from the abstract). Let
Bryan pick 1–3.

**Brain-first check.** Before presenting, search the brain for existing
review pages on the topic. If a relevant review is already ingested, note
it and offer to use it as a starting point.

### 2. Review ingest (delegate with read-back)

Ingest the selected review(s) with `paper-ingest`. When there is only
one review, ingest it directly (spine — first contact with material
entering the brain). When there are multiple reviews (Bryan's
preference is often comprehensive — he chose "all five" when offered
three), delegate the additional reviews as subagents to keep the
orchestrator's context window clean.

**Delegation vs. direct.** The first review (or the spine review — the
one the tier classification builds on) is ingested directly. Additional
reviews can be delegated with read-back verification, because the
selection decision (Bryan chose them) is the vetted judgment that
justifies delegation, just as the review's citation justifies
delegating Tier 1 papers.

**Review full text is often paywalled.** Most high-impact review
journals (Nature Reviews, Annual Reviews, Elsevier titles) do not have
PMC open access. The distillation will frequently be abstract-only
with `needs-enrichment: true`. This is acceptable — the abstract of a
review is information-dense, and the reference list (obtainable via
Semantic Scholar API even when the full text is paywalled) is the
primary output the dive needs for tier classification.

**Obtaining the reference list when full text is paywalled.** Use the
Semantic Scholar Graph API (`api.semanticscholar.org/graph/v1/paper/
DOI:<doi>?fields=references.title,references.externalIds,references.
year,references.authors`) to retrieve the full reference list with DOIs
and PMIDs. This works even when the publisher page is Cloudflare-blocked
and Europe PMC has no open-access copy. The reference list is the input
to Phase 3.

**Incremental validation.** After the first review is ingested, pause.
Read the paper page back. Check that the distillation is complete and
the reference list was obtained. If the quality is good, proceed to
Phase 3. If not, fix the approach before scaling to additional reviews.

**Do NOT walk the bibliography (Phase 7) for review papers.** The
literature-dive orchestrator handles tier classification separately
(Phase 3). Instruct delegated subagents to skip Phase 7 — the
orchestrator will classify the review's references and dispatch Tier 1
papers itself.

### 3. Tier classification

After the review is ingested, read its full text (or the reference list
obtained via Semantic Scholar) against the stubs Phase 7 created.
Reclassify the bibliography into three tiers.

**Tier 1 — promote to immediate ingest.** A citation is Tier 1 if the
review discusses it in detail: devotes a paragraph or more to the paper's
findings, methods, or implications, or cites it repeatedly across
multiple sections. These get full `paper-ingest` now — no stub, no
threshold gate.

**Identify Tier 1 that Phase 7 missed.** Phase 7's anchor test is tuned
for primary papers, which cite more narrowly than reviews. A review's
bibliography is broader, and some citations that pass the "discusses in
detail" bar may not have triggered Phase 7's anchor test. Scan the
review's full reference list — not just the stubs Phase 7 created — for
additional Tier 1 candidates.

**Tier 2 — leave as stubs.** Citations that are load-bearing for Tier 1
papers (a method they use, a dataset they analyze, a framework they
extend) but are not discussed in detail by the review itself. These
stay as the stubs Phase 7 created. The standard threshold gate applies:
when 5+ independent sources cite a stub, `ingest-pending-papers` drains
it.

**Dropped — not paged.** Context citations ("humans have ~10¹⁰ B cells
[42]") that neither the review nor its Tier 1 papers anchor on.

**Output of this phase:** a list of Tier 1 papers (DOI + title +
one-line reason for tier classification) and confirmation that Tier 2
stubs are in place. Present the Tier 1 list to Bryan for a quick
sanity check before ingesting — this is the one gate in the process
where a human glance is cheap and valuable.

**Dedup against the brain.** Before presenting, check each Tier 1 DOI
against existing `papers/` pages — some may already be ingested (e.g.,
the Locci 2016 paper was already in the brain when the Activin A dive
started). Already-ingested papers are listed but not re-ingested.

**Validate identifiers before presenting (Phase 3.5).** Tier-1
identifiers harvested from the review's bibliography (Semantic Scholar
references API, or LLM transcription of the reference list) are wrong
at observed rates of ~70% (ebolavirus dive, 2026-08-05: 7 of 10 Tier-1
task contexts had a wrong PMID, DOI, or both — including one DOI off by
a single digit). Before presenting the Tier-1 list to Bryan, run the
pre-dispatch validator over every Tier-1 candidate:

```bash
python3 skills/paper-ingest/scripts/validate_identifiers.py \
    --batch /tmp/tier1_citations.json --recover
```

Build the batch JSON from the Tier-1 list: `title`, `author`
(first-author surname), `year`, plus any `pmid`/`doi`/`pmcid` already
in hand (~2s per citation). Present Bryan the *validated* list:
`validated` entries as-is; `recovered` entries with their corrected
identifiers (recovery replaces wrong identifiers with PubMed-verified
ones — this is the fix for the ebolavirus failure class); `HOLD`
entries flagged for manual resolution, never silently dispatched. Any
entry flagged `retracted: true` is surfaced to Bryan explicitly, not
dispatched. Phase 4 dispatches using the validator's `dispatch` list —
never the raw bibliography identifiers.

### 4. Tier 1 ingest (delegate with read-back)

Ingest each Tier 1 paper. The review's citation is the vetted decision
that this paper belongs in the brain — the equivalent of the upstream
stub-creation decision that justifies the `paper-ingest` queue-drain
carve-out (`SOUL.md` §2). Delegation is appropriate here: spawn a
subagent per paper (or in small batches), then read the resulting page
back to verify before declaring success.

**Delegation protocol:**
- Spawn one subagent per paper, passing the *validated* DOI/PMID from
  the Phase 3.5 dispatch list (never the raw bibliography identifiers)
  and the context that this is a Tier 1 paper from a literature dive
  (so the subagent knows to do a full `paper-ingest`, not a stub fill).
- The subagent inherits `paper-ingest` and does the full pipeline:
  resolve identity, dedup, distill, file, wire, bibliography walk.
- On return, read the page back. Check: DOI resolved, authors populated
  as `people/<slug>`, `## Findings` with specific results tied to
  figures, `## Analysis` present, `## Limitations` present. If any
  identity field is empty or the body is a stub, the ingest failed —
  retry or do it direct.

**Batching.** If Tier 1 has ≤5 papers, delegate all at once. If 6–15,
batch in groups of 3–5. If >15, pause after the first batch and check
quality before continuing — this is the `test-before-bulk` convention.

**Context management.** Each subagent runs in an isolated context, so
the orchestrator's context window does not accumulate 10–20 full paper
distillations. The orchestrator receives only the final summary per
paper. The read-back verification is a single `brain-read` per page —
cheap.

**Subagent failures.** Subagents can time out (1800s limit), return
empty content, or report success without writing the file. After each
batch returns, check the filesystem (`ls papers/<expected-slug>*`) for
the actual file. Missing files must be re-dispatched or ingested
directly. Do not assume "completed" means "file written."

**Delegation pool limits.** The concurrent delegation pool is small
(3 by default). When dispatching more than 3 papers, send them in
batches of 3 — the runtime will queue or run them synchronously. If
the pool is at capacity, subagents run synchronously, which blocks
the orchestrator. Plan batch sizes accordingly.

### 5. Review-inspired search

After the review and Tier 1 papers are ingested, identify what the
review missed and search for it.

**Three search targets:**

1. **Open questions the review names explicitly.** "Future directions,"
   "remains unknown," "remains to be determined" sections. For each,
   run a targeted PubMed/bioRxiv search. New papers found are
   classified Tier 1 (if they directly address the open question with
   new evidence) or Tier 2 (if they are peripherally relevant).

2. **Thin evidence areas.** Where the review says data is lacking or
   conflicting. Search for papers published since the review's
   citation cutoff that might fill the gap.

3. **Post-review developments.** Papers published after the review's
   last citation date. Search PubMed with a date filter from the
   review's submission date forward.

**Semantic search (paperclip).** Open questions and thin-evidence
areas are naturally *semantic* queries — the relevant papers often
use different vocabulary than the review does, which is exactly where
PubMed keyword templates lose recall. When the `paperclip` CLI and
`PAPERCLIP_API_KEY` are available (see the `paperclip-search`
reference skill), run one `paperclip search -s pmc,biorxiv,medrxiv`
query per open question alongside the PubMed search, phrased in plain
language rather than keyword syntax. Use `-s abstracts` for recall
beyond the full-text corpus (paywalled journals appear there as
abstracts). New papers surfaced this way go through the same Tier 1 /
Tier 2 classification — and Tier 1 candidates get identifier
validation per Phase 3.5 before dispatch. If the binary or key is
absent, skip silently: keyword templates are always the default path.

**Stopping criterion.** One round of targeted searches per open
question. If a search surfaces 3–5 new papers, classify and ingest/stub.
Do not recursively expand — the dive stops when new searches surface
already-ingested papers (diminishing returns). If a search surfaces
nothing new, that is itself informative — the review was comprehensive.

New papers found in this phase that clear the Tier 1 bar ("directly
addresses an open question with new primary evidence") are ingested
immediately via the same delegation protocol as Phase 4. Papers that
are Tier 2 become stubs.

**Run Phases 4 and 5 concurrently.** The review-inspired search
(Phase 5) can run while Tier 1 papers from Phase 4 are still being
ingested by subagents. The orchestrator can run PubMed searches in
the foreground while delegations run in the background. This is the
right pattern — the search is a read-only operation that does not
conflict with the writes the subagents are doing.

### 6. Tier 2 processing

Tier 2 papers stay as stubs created by `paper-ingest` Phase 7. No
change from the standard process. `ingest-pending-papers` drains them
when the threshold gate fires (5+ `cited_by` from independent sources).

This phase is a *no-op* during the dive itself — it exists to make the
tier classification explicit and to confirm that the stubs are
correctly tagged with `needs-ingest: false` (single citation, below
threshold) and will be picked up by future `ingest-pending-papers`
runs.

### 7. Synthesis

After all Tier 1 papers are ingested and the review-inspired search is
complete, synthesize the result.

**Default: invoke `topic-synthesis`.** The dive has now populated the
brain with a review + its foundational literature. `topic-synthesis`
consolidates these paper pages into a single durable `concept` page
that captures what the brain now knows about the topic — cited back
to the source papers, with tensions and open questions made explicit.

The `topic-synthesis` skill is brain-internal — it reads `paper` pages,
not external literature. By the time it runs, the dive has already
done the external work. The synthesis is the *internal* consolidation
of what was ingested.

**When the synthesis is a testable claim, not a framework.** If the
ingested literature falls on both sides of a question (papers support
X, papers refute X), `topic-synthesis` should produce a `hypothesis`
page with typed `supports:`/`refutes:` edges, not a `concept` page.
The `topic-synthesis` skill already handles this choice (Phase 4).

**Existing concept page.** If the brain already has a `concept` page
for the topic, `topic-synthesis` will gate via `ask-user`: update in
place, restructure, or cancel. The dive's synthesis enriches the
existing page with the newly ingested literature.

**The synthesis is the deliverable.** The individual paper pages are
the evidence base; the concept page is the output Bryan reads. The
dive is not complete until the concept page is written.

**Commit before synthesising.** After all Tier 1 papers are written
and before starting the synthesis, commit the papers, ledger updates,
and concept-page link updates with a descriptive message. The
auto-snapshotter commits uncommitted work with a generic message —
commit explicitly so the dive's intent is preserved in git history.

## What this guarantees

- The dive starts from expert curation (a high-impact review), not
  algorithmic ranking.
- Tier 1 papers — the foundational literature the review builds on —
  are fully ingested immediately, not queued behind a citation
  threshold.
- Tier 2 papers — load-bearing but not foundational — follow the
  standard stub + threshold gate, so the brain does not grow stubs
  faster than it can fill them.
- Delegation for Tier 1 ingest keeps the orchestrator's context
  window clean; read-back verification ensures each page is actually
  filled.
- The review-inspired search catches what the review missed: open
  questions, thin evidence, post-review developments.
- The dive ends with a synthesis — a concept page that consolidates
  what the brain now knows — not just a pile of paper pages.

## Anti-patterns

- **Starting from a keyword search instead of a review.** The whole
  point is expert curation as the entry point. If no suitable review
  exists, say so and offer `literature-research` as the fallback.
- **Tier 1 bar too loose.** "The review cites this paper" is not
  enough — every paper in the bibliography is cited. The bar is
  "discusses in detail": a paragraph or more, or repeated citation
  across sections.
- **Tier 1 bar too tight.** "The review's argument would fail without
  this paper" is the `paper-ingest` anchor test — too strict for
  reviews, which build arguments from many papers in a way that no
  single one is load-bearing. The bar is "discusses in detail," not
  "argument fails without."
- **Ingesting Tier 2 papers inline.** Tier 2 papers are stubs. The
  threshold gate and `ingest-pending-papers` own the fill. Inline
  ingest of Tier 2 is the "exploding paper tree" the threshold gate
  exists to prevent.
- **Skipping the read-back.** Delegated Tier 1 ingest is
  delegation-with-oversight. The oversight is reading the page back.
  A subagent that reports "done" with an empty `authors:` field or
  a stub body has not succeeded — catch it at the read-back.
- **Trusting subagent "completed" status.** A subagent can report
  "completed" without writing the file (empty model output, timeout
  after partial work). Always verify on the filesystem (`ls papers/`)
  after each batch returns. Missing files must be re-dispatched.
- **Skipping the synthesis.** A dive that ends with 15 paper pages
  and no concept page is a pile of evidence with no argument. The
  synthesis is the deliverable.
- **Recursive expansion.** The dive stops when searches surface
  already-ingested papers. Chasing every citation's citations is the
  exploding paper tree.
