---
name: literature-dive
description: A structured deep literature dive — start from recent high-impact reviews (or semantic search for fast-moving fields), ingest the foundational primary literature tier-by-tier, search for what the initial pass missed, run one informed supplementary pass to close gaps surfaced by the dive itself, and synthesize the result into a concept page.
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
synthesize the result into a durable concept page.

The default entry point is a recent high-impact review, because reviews in
high-impact journals are information-dense maps of a field — they identify
the load-bearing primary papers, the open questions, and the structural
tensions. Starting from a review (rather than a keyword search) means the
dive begins with expert curation, not algorithmic ranking. For fields
moving too fast for reviews to keep up, semantic search is the discovery
engine instead (Phase 1 covers both paths).

Either way, the initial discovery pass runs *uninformed*: before the dive,
the brain lacks the context to know which jargon, which neighboring
subfields, and which uncited-but-load-bearing papers matter. That is why
the dive ends with an informed supplementary pass (Phase 6) before
synthesis — the second pass uses everything the first pass learned.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/brain-first.md` (check the brain first),
> `skills/conventions/quality.md` (citations, forward-only linking),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/conventions/test-before-bulk.md` (validate before scaling),
> `skills/conventions/preprint-retrieval.md` (bioRxiv full text),
> `skills/conventions/paper-stubs.md` (queue/provenance).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url` (`pubmed-fetch`,
`crossref-fetch`, `biorxiv-fetch`, `arxiv-fetch`), `spawn-subagent`.

## Environment preflight

Run these checks at the start of every dive, before any subagent
dispatch:

- **Raise the FD limit.** The macOS default soft limit is 256
  (`ulimit -n`), too low for a dive dispatching parallel subagents —
  observed crash: `OSError: [Errno 24] Too many open files` killing the
  orchestrator and all dispatched subagents (2026-08-05). Run
  `ulimit -n 4096` at the first terminal command of the dive. Each new
  session inherits the login default; do not assume a prior session's
  `ulimit` carries over.
- **Entrez Direct CLI is not installed.** `esearch`/`efetch`/`esummary`
  do not exist on this host. Use the PubMed E-utilities REST API via
  curl (templates in Phase 1).
- **arXiv API curl is blocked.** Direct `curl` to `export.arxiv.org` is
  blocked by the approval gate and times out. Do not put arXiv API curl
  commands in subagent tasks. Use `paperclip cat
  /papers/arx_<ID>/meta.json` for metadata and `fetch_fulltext.py
  --publisher-url https://arxiv.org/html/<ID>` for full text.
- **PubMed rate limits.** E-utilities aggressively returns HTTP 429.
  Batch ID lookups (comma-separated IDs in one `esummary` call), sleep
  3–5s between sequential calls (2s is sometimes insufficient), and
  never loop on 429 — after three consecutive 429s, stop and wait 15+
  seconds. When PubMed 429s repeatedly, Semantic Scholar
  (`api.semanticscholar.org/graph/v1/paper/search?query=...&fields=
  title,externalIds,year`) is the discovery fallback; it also
  rate-limits under load, so if both are blocked, wait 10–15s.

**`curl | python3` pipe is blocked by the security scanner.** The
Phase 1 PubMed search templates below use `curl ... | python3 -c "..."`
but Hermes blocks pipes from curl to interpreters (security scan: "Pipe
to interpreter"). Use `execute_code` with `urllib.request` instead — it
handles URL encoding correctly and avoids both the pipe block and a
second issue: unencoded parentheses in PubMed query URLs cause `curl -o`
to fail with exit code 3. `urllib.parse.urlencode` in `execute_code`
handles this transparently. The `execute_code` path also lets you batch
multiple PubMed searches in one call and parse results with the full
Python stdlib.

**Provider/delegation failure.** An HTTP 429 or capacity error is not evidence
that paper full text is unavailable. Inspect written files after workers have
returned; preserve valid intermediates and defer failed/unstarted queued fills
per `ingest-pending-papers`. Respect retry guidance without asserting that a
single observed limit lasts for every session. Use another available execution path or defer the affected papers without
weakening source checks; a provider failure does not establish source closure.

`paper-ingest` owns the retrieval ladder and source-completeness gates. Genuine
abstract-only distillation sets `fulltext_source: abstract-only` and
`needs-enrichment: true`; a substitute preprint also retains enrichment.
Attribute review-derived context to the review, not to an unread primary
paper. Do not use a provider failure to bypass manuscript/supplement attempts
or the abstract-only closure gate.

**Crash recovery.** If a dive crashes mid-flight: restart Hermes (clears
FD leaks), `ulimit -n 4096` immediately, use `session_search` to
reconstruct state (phase, selections, batches dispatched), check the
filesystem for partial writes (`ls papers/`), and resume from the failure
point — never restart from Phase 1.

## The two-tier citation system

The dive introduces an explicit tiering for the papers surfaced by a
review's bibliography. This is a refinement of `paper-ingest` Phase 7's
single-tier stub system, motivated by the fact that reviews cite more
broadly than primary papers and the dive needs a way to triage a large
bibliography.

| Tier | What it is | Ingestion path |
|---|---|---|
| **Tier 1 (primary)** | The review itself + primary literature the review discusses in detail | Priority paper-ingest, normally in isolated workers; no citation threshold or prerequisite stub. |
| **Tier 2 (secondary)** | Load-bearing citations from Tier 1 papers (methods, datasets, frameworks) | `paper-ingest` Phase 7 stub + threshold gate (5+ `cited_by`). Full ingest deferred to `ingest-pending-papers`. |
| **Dropped** | Background/context citations | Not paged. |

**The Tier 1 bar: "review discusses this paper in detail."** This is
looser than `paper-ingest` Phase 7's anchor test ("the paper would lose
its argument without this reference"). A review that devotes a paragraph
or more to a paper's findings, methods, or implications — citing it
repeatedly across multiple sections — clears the Tier 1 bar. A review
that cites a paper once for a fact ("humans have ~10¹⁰ B cells [42]")
does not. The typical review has 200–300 references; Tier 1 is usually
10–20.

**Paper priority and author promotion are separate.** Tier 1
bypasses the paper queue's citation threshold; author ledger/promotion rules
still apply. Follow paper-ingest's execution modes and Phase 8 reference.

## Phases

### 1. Review discovery

Search PubMed for recent reviews on the topic, filtered to high-impact
review journals. Present 3–5 candidates for your human's selection.

**Journal whitelist:**
- Nature Reviews family (Immunology, Microbiology, Drug Discovery, etc.)
- Trends in family (Immunology, Microbiology, Parasitology, etc.)
- Annual Reviews family (Immunology, Microbiology, etc.)
- Cell, Nature, Science — reviews and perspectives
- F1000Prime reviews
- A bioRxiv/medRxiv review preprint qualifies on merit if by a recognized authority

**PubMed search template (REST API — Entrez Direct is not installed):**

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<URL-encoded-query>&retmode=json&retmax=30" | python3 -c "
import sys, json; d = json.load(sys.stdin); print(','.join(d['esearchresult']['idlist']))
"
# Then fetch summaries in a SINGLE batch call (comma-separated IDs):
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=<comma-separated-IDs>&retmode=json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for uid in d['result']['uids']:
    r = d['result'][uid]
    print(f'PMID {uid} | {r.get(\"fulljournalname\",\"\")} | {r.get(\"pubdate\",\"\")}')
    print(f'  {r.get(\"title\",\"\")}')
"
```

Query shape: `<topic>[Title/Abstract] AND (review[pt] OR review
literature[pt]) AND (<whitelist journals>)`, mindate 2–3 years back. If
PubMed returns too few, broaden: drop the journal filter, widen the date
range, or search bioRxiv. If too many, narrow: add the `review[pt]`
filter, or prioritize by citation count (PubMed Relative Citation Ratio
if available, or CrossRef citation count). Respect the rate limits in
Environment preflight.

Present the candidates with: title, journal, year, first author, a
one-line description of the review's scope (from the abstract). Let
your human pick 1–3.

**Brain-first check.** Before presenting, search the brain for existing
review pages on the topic. If a relevant review is already ingested, note
it and offer to use it as a starting point.

**Fast-moving fields: semantic search as primary discovery.** When the
field is moving so fast that reviews lag by 6–12 months, the
review-anchored protocol needs adaptation. Use `paperclip search -s
arxiv,biorxiv` with multiple semantic queries covering the field's
clusters as the PRIMARY discovery tool, not just a Phase 5 supplement.
The spine survey (if one exists) provides the taxonomy; the semantic
search finds the frontier the survey missed. For fields where no adequate
review exists, skip the review-anchored protocol entirely and build Tier
1 directly from semantic search results, grouped by cluster: run 6–10
semantic queries, dedup against the brain, present the cluster map +
candidate count for scope approval, then ingest under Phase 4’s explicit modes.

The two methods are complementary, not substitutes. Observed 2026-08-10
(DLM dive): the spine survey provided the taxonomy but missed the entire
current-year wave; 8 semantic queries surfaced 75+ Tier 1 candidates in 9
clusters — while the survey's bibliography added 5 Tier 1 papers the
semantic search missed. Some dives will use both: survey for taxonomy,
semantic search for the frontier. Confirmed at scale in a second dive
(protein structure tokenization, 27 papers) with no survey at all.

**Seed-corpus entry (anchor sets).** When your human hands you a paper
whose load-bearing references form a near-complete causal chain —
typically an ingested paper whose Ingest log names deferred anchor
stubs — the dive can start from those anchors directly: resolve and
validate every anchor identity (Phase 3.5 rules), ingest them under
Phase 4’s explicit modes, and run the review-discovery search in
parallel; the spine review, when one exists, is ingested as a
supplementary paper rather than before the corpus (observed 2026-09-05,
adaptive-immunity-CNS dive: the park-2026 anchor set was ingested
first, and the Smyth/Kipnis "Redefining CNS immune privilege" review
surfaced in the discovery search and landed mid-dive). Tier
classification then runs against the anchors' own deferred-reference
logs plus the review when it arrives.

### 2. Review ingest

Use `paper-ingest` for selected reviews, delegating to isolated workers when
helpful. Reuse existing verified pages. Review selection already authorizes
the work; no prerequisite stub or separate delegation approval is needed.

**Review full text is often paywalled.** Most high-impact review
journals (Nature Reviews, Annual Reviews, Elsevier titles) do not have
PMC open access. The distillation will frequently be abstract-only
with `needs-enrichment: true`. This is acceptable — the abstract of a
review is information-dense, and the reference list is the primary
output the dive needs for tier classification.

**Obtaining the reference list when full text is paywalled.** Three
sources, tried in order:

1. **Semantic Scholar Graph API** (`api.semanticscholar.org/graph/v1/
   paper/DOI:<doi>?fields=references.title,references.externalIds,
   references.year,references.authors`) — the default. Works even when
   the publisher page is Cloudflare-blocked and Europe PMC has no
   open-access copy. Caveats: rate-limits aggressively (429), sometimes
   returns 0 references for valid DOIs (do not treat empty as
   definitive), and reference PMIDs can resolve to completely different
   papers (observed 2026-08-05: an HEV VLP reference's SS PMID resolved
   to a Japanese encephalitis vaccine paper). Semantic Scholar is
   reliable for DOIs, less so for PMIDs — Phase 3.5 validation is
   mandatory.
2. **OpenAlex Graph API** (`api.openalex.org/works/doi:<doi>`) — the
   fallback when Semantic Scholar returns 0 references or rate-limits.
   Returns `referenced_works` as OpenAlex IDs; batch-resolve in groups
   of 25 via `api.openalex.org/works?filter=openalex:W1|W2|...|W25
   &per_page=25&select=id,title,publication_year,cited_by_count,ids`,
   0.5s sleep between batches. The most reliable reference-list source
   observed (astrovirus dive, 2026-08-07: SS returned 0 refs for a
   valid Elsevier DOI; OpenAlex returned all 158, 149 resolved).
3. **Europe PMC REST** (`europepmc.org/webservices/rest/search?query=
   DOI:<doi>&resultType=core&format=json` → `referenceList.reference[]`)
   — third resort; returns 0 references for many paywalled articles.

**When ALL reference-list sources return empty.** Very recent reviews
(published within the last few months) may not yet be indexed anywhere.
Do NOT treat this as dive-blocking. Two fallbacks: (1) use the other
selected reviews' bibliographies — the spine review's list is preferred
but not exclusive; (2) PubMed-driven Tier 1 identification (Phase 3).
Observed 2026-08-07 (filovirus dive): spine review had no PMC OA, no
Wayback snapshot, SS `references: None`, Europe PMC 0 refs — the Tier 1
list of 13 was built from the other three reviews' bibliographies plus
targeted PubMed searches.

**Incremental validation.** After the first review is ingested, pause.
Read the paper page back. Check that the distillation is complete and
the reference list was obtained. If the quality is good, proceed to
Phase 3. If not, fix the approach before scaling to additional reviews.

**Review bibliography ownership.** Skip paper-ingest's automatic Phase 7
stub creation for the review; the dive primary classifies the fetched reference
list in Phase 3. Save its source and identifiers. No stubs are assumed to exist
as a result of the skipped phase.

### 3. Tier classification

Read the review's full discussion where available and its fetched reference
list; compare candidates against existing brain pages, not imaginary Phase 7
stubs. Classify the full reference list, including candidates beyond the
primary-paper anchor test.

**Tier 1 — priority ingest.** A reference qualifies when the review discusses
its findings/methods/implications in detail or repeatedly across sections.
Read that discussion to establish the bar. A reference list alone cannot show
how a paper was discussed; if the review body is unavailable, use the alternate
review or targeted-search path below and state that basis explicitly.
Approved Tier 1 sources use the same paper-ingest workers whether new or
already stubbed; reuse existing full pages.

**Tier 2 — threshold-gated stubs.** Create or update source-grounded
load-bearing references (methods, datasets, frameworks) using
`skills/conventions/paper-stubs.md`. During Tier 1 ingestion, the primary or
queue-drain parent performs each paper's Phase 7 walk; page-only leaves do not
create these stubs. A deferred walk is an explicit outstanding obligation,
not confirmation that stubs are in place.

**Dropped — not paged.** Background/context references do not become stubs.
Neither topic relevance nor campaign selection creates a `cited_by` edge;
only verified citation relations do.

**Dedup against the brain.** Before presenting, check each Tier 1 DOI
against existing `papers/` pages — some may already be ingested.
Already-ingested papers are listed but not re-ingested.

**Non-duplicative filter (your human's standing rule for large dives).**
Before ingesting a Tier 1 candidate, ask: does this paper add something
the brain does not already hold, and does it add something a sibling
Tier 1 paper in the same dive does not already cover? A review that
"discusses in detail" a topic the brain already ingested in a prior dive
does **not** need a second full ingest — note it as already-covered and
drop it from the ingestion list. The Tier 1 bar is "discusses in detail
AND adds new signal," not "discusses in detail" alone. When the dive
spans multiple axes (diversity, mechanism, evolution, intervention),
prefer one load-bearing paper per axis over several papers that
recapitulate the same axis.

**PubMed-driven Tier 1 identification (when no review bibliography is
available).** When the spine review's reference list is unavailable
(all Phase 2 sources empty), identify Tier 1 papers through targeted
PubMed searches instead of from a curated bibliography:

1. Search by major protein / component — `<topic> <protein>[Title/
   Abstract]`, mindate ~2015, retmax 5.
2. Search by lifecycle stage / mechanism axis — `<topic> <stage>[Title/
   Abstract]`.
3. Search for comparative / extended-scope papers.
4. Dedup against existing brain pages (grep `papers/` for the PMID).
5. Validate identifiers (Phase 3.5) — PMID-sourced identifiers are
   substantially more reliable than bibliography-harvested ones
   (filovirus dive: 13/13 validated clean).

The Tier 1 bar here is stricter than the review-bibliography bar,
because there is no expert curation: "directly defines or extends the
molecular mechanism for a lifecycle stage / axis of the target topic."

**Output of this phase:** a list of Tier 1 papers (DOI + title +
one-line reason and source basis for tier classification), plus the Tier 2
stubs actually created and any explicitly pending bibliography decisions. Present the Tier 1 list to your human for a quick
sanity check before ingesting — this is the one gate in the process
where a human glance is cheap and valuable.

**Validate identifiers before presenting (Phase 3.5).** Tier-1
identifiers harvested from a review's bibliography (Semantic Scholar
references API, or LLM transcription of the reference list) are wrong
at observed rates of ~70% (ebolavirus dive, 2026-08-05: 7 of 10 Tier-1
task contexts had a wrong PMID, DOI, or both — including one DOI off by
a single digit). Before presenting the Tier-1 list to your human, run the
pre-dispatch validator over every Tier-1 candidate:

```bash
python3 skills/paper-ingest/scripts/validate_identifiers.py \
    --batch /tmp/tier1_citations.json --recover
```

Build the batch JSON from the Tier-1 list: `title`, `author`
(first-author surname), `year`, plus any `pmid`/`doi`/`pmcid` already
in hand (~2s per citation). Present your human the *validated* list:
`validated` entries as-is; `recovered` entries with their corrected
identifiers (recovery replaces wrong identifiers with PubMed-verified
ones); `HOLD` entries flagged for manual resolution, never silently
dispatched. Any entry flagged `retracted: true` is surfaced to your
human explicitly, not ingested unattended. Phase 4 uses the validator’s
`dispatch` output as the validated candidate list, not as delegation
authorization; never use the raw bibliography identifiers.

**PubMed batch verification for HOLD entries.** The validator's
title-matching heuristic is conservative — older papers (1990s–2000s)
with slightly different PubMed title formatting can fail the
title-similarity threshold even when the PMID is correct. When the
validator returns HOLD entries with PMIDs, verify them via a single
PubMed `esummary` batch call: if PubMed returns the expected title for
each PMID and the other identity fields agree, the paper can proceed under
Phase 4’s execution modes. Do NOT
discard a paper solely because the validator's title-match heuristic
failed (astrovirus dive, 2026-08-07: 17 of 33 Tier 1 papers flagged
HOLD; all 17 PMIDs verified correct via PubMed batch, all dispatched
successfully). Hyphenated surnames are another false-HOLD source
(observed 2026-09-05, adaptive-immunity-CNS dive: "Eme-Scolan" scored
100 on the PubMed title check but OpenAlex reported `surname_match:
false` against resolved first author "Elisa Eme-Scolan", verdict
MIXED) — the PubMed `esummary` batch check resolves it like any other
HOLD. Separately, a "PMCID" that lacks the `PMC` prefix (bare digits
from a parse) is not a PMCID: confirm against the EPMC core record
before routing retrieval through it. Curly-apostrophe title variants
are a third false-HOLD source (same dive: "ageing and Alzheimer's
disease" with U+2019 scored 99.2–100.0 but failed the surname check
while PMID↔DOI consistency and PMCID resolution both PASSed) — the
defect is apostrophe normalization, not identity; the PubMed batch
check confirms. And the converse of the bare-PMCID rule: a
properly-prefixed PMCID can look wrong and still be right — a recent
paper carrying an older author-manuscript PMCID (same dive, Antila
2024 Nat Cardiovasc Res: PMC7616318, MID EMS196559) is the same
record, not a mis-mapping; `efetch db=pmc` + title match settles it
before the identifier is discarded.

### 4. Tier 1 ingest

Delegate one selected paper per isolated paper-ingest worker; new papers and
existing stubs use the same page-only mode. A small standalone ingest can run
inline. The dive’s existing selection/tiering rules are sufficient; add no
eligibility classifier, approval manifest, or mandatory session boundary.

Load `skills/batch-drain/SKILL.md` for runtime sizing and dispatch/return
handling. Give each worker the source identifier, assigned output path,
campaign purpose, and unique scratch prefix. Workers read and distill their
sources, return PAGE_READY and source-linked bibliography candidates, and do
not mutate shared files or perform Git operations. The parent verifies each
result and completes shared wiring before clearing the queue flag or counting
completion. Save campaign progress between waves; do not accumulate every
worker’s full extraction transcript in the parent.

**Briefs are source-grounded inputs, not primary evidence.** Authorship,
cohorts, and findings in a brief must come from the source metadata/abstract
read for that input, not recollection. The worker still verifies the brief
against the retrieved paper. Use paper-ingest's source-specific metadata
ladder: jina may drop bylines and mirrors may be incomplete or stale; author
identity is not inferred from the available body text alone.

**Parent wiring.** The parent verifies each PAGE_READY page and source-linked
bibliography candidates, opening original passages as needed, then performs
paper-ingest Phases 7–9. The shared
procedure is `paper-ingest/references/author-ledger-mutation.md`: it owns
name/slug resolution, ORCIDs, new versus existing entries, promotion,
plain-text mutation, and read-back. Do not reconstruct the wiring table from
a truncated subagent summary or duplicate its mutation algorithm here.

**Verification and failure recovery.** Follow paper-ingest Phase 10 and the
drain's per-item accounting. Check every returned item on disk regardless of
reported success/failure: a provider can fail before writing or after a useful
intermediate is written. Neither file existence, headings, nor author count
alone establishes a completed ingest. A page-only result stays queued until
parent wiring is complete. Confirm the actual canonical path after any
parent-owned merge; source-check conflicting identifier resolutions. If a
write contains `read_file` line prefixes such as `1|---`, repair only verified
prefix corruption from preserved text and repeat parsing/source checks; do
not strip arbitrary text from a scientific source. Do not inspect an in-flight
leaf's missing authors as a final failure or mutate shared state on that basis.

**Foreground work during a wave.** Only work independent of its
outputs may proceed: read existing concept pages, design searches from the
already-read review, or compile a scratch map. Do not synthesize from unfinished
papers, judge their coverage before read-back, or start another dispatch.
Close coherent verified ingestion units through git-ops after required wiring;
wave completion alone is not the commit boundary.

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
validation per Phase 3.5 before ingestion. If the binary or key is
absent, skip silently: keyword templates are always the default path.

**Stopping criterion.** One round of targeted searches per open
question. If a search surfaces 3–5 new papers, classify and ingest/stub.
Do not recursively expand — the dive stops when new searches surface
already-ingested papers (diminishing returns). If a search surfaces
nothing new, that is itself informative — the review was comprehensive.

New papers found in this phase that clear the Tier 1 bar ("directly
addresses an open question with new primary evidence") are ingested
under the same explicit execution modes as Phase 4. Papers that
are Tier 2 become stubs.

**Concurrent search is conditional.** While a paper-ingest wave is
running, searches derived solely from the already-read review may proceed.
Searches or coverage judgments that require the wave's unread outputs wait
for its return and verification.

### 6. Informed supplementary pass

The initial pass (Phases 1–5) ran uninformed: before the dive, neither
the search terms nor the tier classifications could draw on context the
brain did not yet have. Phase 6 is a second, bounded pass that uses
everything the dive has learned to find what the uninformed pass was
structurally incapable of finding. It runs ONCE per dive, after Phase 5
and before synthesis — so the synthesis (Phase 7) is built once, over
the complete corpus, rather than patched after the fact.

#### 6.1 The gap map

Read the ingested corpus and write a gap map at
`working-docs/gap-map-<topic>.md` (a transitory working document — no
frontmatter, no lifecycle, not a brain page). A gap belongs on the map
only when all three criteria hold:

1. **Existence** — reasonably high confidence that a gap in our
   knowledge actually exists (not a suspicion, a specific missing piece).
2. **Addressability** — there might be literature the initial ingestion
   missed that could help close it.
3. **Meaningfulness** — leaving the gap unfilled would mean our
   understanding of the topic is incomplete in a meaningful way. This
   is the most important criterion: the map holds MEANINGFUL gaps, not
   trivialities.

There is no minimum and no maximum. A dive that surfaces zero clear gaps
proceeds with an empty gap map — prong 1 (below) is simply skipped. A
dive that surfaces 10+ meaningful gaps fills 10+. Never identify trivial
gaps to pad the map. Meaningful examples: for a dive on models for a
specific task, a referenced-but-uningested model is a meaningful gap; so
is a benchmarking study that introduces no new model but compares models
already in the corpus. A minor parameter variation on an ingested method
is not.

The gap map later feeds the concept page's Open Questions section in
Phase 7 — write it with that reuse in mind. A template with format and
examples lives at `references/gap-map-template.md`. For the
axis-reframed query pattern (Prong 2b), session detail with the full
query set, the paperclip output-parsing gotcha, and the
dedup-quantification step lives at `references/axis-reframed-probe.md`.

#### 6.2 Three discovery prongs

Run all three prongs (subject to the gap map), then consolidate their
candidates in 6.3.

**Prong 1 — gap queries.** For each gap on the map, run one `paperclip
search -s arxiv,biorxiv` semantic query and one PubMed keyword query,
phrased to target the gap specifically. (This absorbs the former
"Phase 5b post-dive gap analysis": 7 gap queries surfaced 7 papers in
the 2026-08-10 DLM dive, every one of them Tier 1.)

**Prong 2 — jargon-upgraded queries.** The initial queries were written
in naive vocabulary. Harvest the terminology the dive has acquired —
assay names, model names, domain-specific jargon — from the ingested
paper pages, and identify terms that appear across multiple Tier 1 pages
but were absent from the original Phase 1/5 query set. Regenerate the
keyword and semantic queries with the learned vocabulary and run them.
A useful self-check: if an original query returned near-zero hits where
a jargon term now returns many, that quantifies what the uninformed pass
missed.

**Prong 2b — axis-reframed queries (the harness-probe pattern).**
Jargon upgrades keep the dive's original *axis* — what the systems do.
A corpus can still be structurally blind on the orthogonal axis: how
the systems are *built*. Observed 2026-09-05 (autoresearch dives 1–2 →
dive 3): two application-seeded dives (AIRA, SENPAI) produced an
applications-heavy corpus; 8 semantic queries reframed on
infrastructure-design vocabulary (agent harness, harness engineering,
runtime substrate, control plane, system of record, checkpoint/restore,
transactional sandboxing, agent memory as database, git/PR
communication backbone) surfaced 113 unique papers of which 111 were
not in the vault — a self-named 2026 field the systems papers never
cite. The method: (1) find the machinery layer's own name for itself —
often coined in industry posts rather than papers, so check the anchor
paper's related-work section for blog/repo citations that name the
practice; (2) run 6–10 plain-language semantic queries on that
vocabulary; (3) dedup against the vault; (4) quantify new-vs-known.
A high new fraction (>90%) is evidence the initial pass had a
structural blind spot and a supplementary dive on that axis is
warranted before synthesis. If the new axis has grown to rival the
original, split the concept page FIRST, then begin ingestion — see
the split pattern in Phase 7.

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

**Bias toward inclusion.** For deep dives, the token cost of ingesting
a redundant or marginally informative paper is far lower than the cost
of missing something truly valuable. When in doubt, put the candidate
on the list — the human approval gate (6.3), not a rigid filter, is
the volume control.

#### 6.3 Review rediscovery — the re-anchor

If the supplementary searches surface a high-value review the initial
pass missed, treat it as evidence the initial dive had at least one
structural gap — and potentially others. This triggers a **re-anchor**
(Phase 1 lite): obtain the new review's reference list (Phase 2 ladder),
classify its bibliography against the already-ingested corpus, and add
the Tier 1 candidates it implies to the supplementary list. If multiple
new reviews surface, re-anchor on each.

A re-anchored review's bibliography is mined with the same tier bars and
the same non-duplicative filter as Phase 3 — most of its references will
already be ingested; the value is in the ones that are not.

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
`ingest-pending-papers` drains it. Confirm each stub’s queue flag follows the shared stub contract: false
below threshold unless another producer already queued it; true at threshold.
Never reset an already queued stub to false. Do not inline-ingest
Tier 2 — that is the exploding paper tree the threshold gate exists to
prevent. (Phase 6's informed snowball is the judgment-driven exception:
papers it promotes are reclassified Tier 1 by human approval, not
inline-ingested as Tier 2.)

### 7. Synthesis

After the supplementary pass is complete, synthesize the result.

**Close ingestion units before synthesizing.** The dive parent completes
required wiring and validates each coherent ingestion unit, then commits and
pushes it through `skills/git-ops/SKILL.md`. Dispatch size does not determine
commit size. The final verified concept synthesis is a separate unit. Do not
commit unrelated pending work or rewrite earlier history.

**Default: invoke `topic-synthesis`.** The dive has now populated the
brain with a review + its foundational literature + the supplementary
pass's additions. `topic-synthesis` consolidates these paper pages into
a single durable `concept` page that captures what the brain now knows
about the topic — cited back to the source papers, with tensions and
open questions made explicit. Feed the gap map (6.1) into the concept
page's Open Questions section.

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

**Concept-page split (human-approved).** When a
dive reveals that a concept page is carrying two literatures that cite
each other sparsely and are searched with different vocabulary (the
application/harness split), ask whether to split into sibling pages
BEFORE ingesting the supplementary corpus. Rationale: pages
wired once into the right concept are cheaper than pages re-sorted
afterward, and a single page carrying both axes buries each. The split
protocol: (1) create the new concept page with the orthogonal axis's
map, inheriting the relevant links from the old page's frontmatter;
(2) rewrite the old page's self-description to scope it to its own
axis and cross-link the sibling in both `related_concepts` and body
prose; (3) both pages get Shifts entries documenting the split, the
new page's entry explaining what moved and why; (4) do NOT
bulk-repoint inbound paper links — the old page still resolves them;
a future retroactive-linking pass can migrate them deliberately.
(5) The supplementary dive wires into the NEW page only.

**Concept page supersession (extending to a broader scope).** When the
dive extends an existing concept page to a genuinely broader scope
(e.g., ebolavirus to filovirus-wide), there is a fourth path beyond
`topic-synthesis`'s three: **supersede and redirect**.

1. Author the new concept page at a new slug, folding the old page's
   content into the broader scope.
2. Replace the old page with a redirect stub: `status: dormant` (NOT
   `superseded` — not a valid frontmatter enum; the linter rejects it),
   `superseded_by: concepts/<new-slug>`, and a one-line redirect body.
3. Do NOT bulk-update inbound links inline. When 40+ pages link to the
   old slug, the redirect stub ensures they resolve; a future
   `retroactive-linking` or `maintain` pass can update them.
4. Copy the old page's `links:` and `related_concepts:` lists into the
   new page and append new papers/concepts.
5. Preserve the old page's Shifts log entries (with original dates) and
   add a new shift entry documenting the supersession.

Ask your human whether to update in place, supersede, or create a fresh
independent page. Supersession is right when the dive's scope genuinely
exceeds the old page's scope and the old content is fully subsumed.

**Concept-page link verification (the `.md`-extension trap).** After
enriching a concept page, verify every frontmatter `links:` entry and
body wikilink resolves ON DISK — but note that `links:` values are
extensionless (`papers/<slug>`), so a verifier that checks
`os.path.exists(vault + "/" + link)` reports EVERY link missing and
looks like a total graph failure. The correct check tests both forms:
`vault + "/" + target + ".md"` OR `vault + "/" + target`. When a
verification pass fails *wholesale*, suspect the verifier's path
convention before touching the artifact — the same suspicion-the-
verifier-first rule as the ledger's bare-slug wiring-table bug.

**The synthesis is the deliverable.** The individual paper pages are
the evidence base; the concept page is the output your human reads. The
dive is not complete until the concept page is written.

## What this guarantees

- The dive starts from expert curation (a high-impact review) or, for
  fast-moving fields, from cluster-mapped semantic search — never from
  a bare keyword template.
- Tier 1 papers — the foundational literature — are fully ingested
  immediately, not queued behind a citation threshold.
- Tier 2 papers — load-bearing but not foundational — follow the
  standard stub + threshold gate, so the brain does not grow stubs
  faster than it can fill them.
- Isolated paper workers prevent full extraction conversations from
  accumulating in the parent; verification and shared wiring remain explicit.
- The review-inspired search catches what the review missed: open
  questions, thin evidence, post-review developments.
- The informed supplementary pass catches what the *uninformed
  discovery process itself* missed: meaningful gaps visible only after
  ingestion, queries rewritten in the field's actual jargon, and
  load-bearing or field-shaping references that no review cited — with
  one bounded re-anchor if a missed review surfaces.
- The dive ends with a single synthesis over the complete corpus — a
  concept page that consolidates what the brain now knows — not a pile
  of paper pages, and not a synthesis that has to be patched after a
  second pass.

## Anti-patterns

- **Starting from a keyword search instead of a review.** The whole
  point is expert curation as the entry point. If no suitable review
  exists and the field is not fast-moving, say so and offer
  `literature-research` as the fallback. (The fast-moving-field
  semantic-search path in Phase 1 is the sanctioned exception.)
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
- **Skipping the read-back.** Inline and delegated ingests require source
  and artifact verification. A child’s
  PAGE_READY or failure report is not the final outcome; the parent checks
  every returned item under paper-ingest Phase 10 and the drain’s accounting.
- **Trusting file presence as completion.** Phase 4’s verification/recovery
  rules require identity, source, body, and wiring checks after
  workers return; never repair shared state while a leaf is still writing.
- **Skipping the supplementary pass.** A dive that goes straight from
  Phase 5 to synthesis locks in the blind spots of the uninformed
  discovery pass. Phase 6 is a standard component of every dive, not an
  optional extra — though its gap map may legitimately be empty.
- **Padding the gap map.** The gap map has no quota. Trivial gaps
  identified to reach a count waste ingestion budget and dilute the
  meaningful ones. Three criteria, meaningfulness above all; zero is a
  valid count.
- **Numeric thresholds in the supplementary snowball.** Prong 3 is
  judgment over the bibliographies, not a `cited_by` filter. Rigid
  cutoffs reintroduce exactly the blindness Phase 6 exists to remove.
  The human gate is the volume control; bias toward inclusion.
- **Iterating the supplementary pass.** Phase 6 runs once. A re-anchor
  runs at most once. If a re-anchor surfaces yet another high-value
  review, stop and get explicit human approval before going further —
  present what was found and let your human decide. Beyond that single
  sanctioned loop, the old rule stands: the dive stops when searches
  surface already-ingested papers. Chasing every citation's citations
  is the exploding paper tree.
- **Skipping the synthesis.** A dive that ends with 15 paper pages
  and no concept page is a pile of evidence with no argument. The
  synthesis is the deliverable.
- **`yaml.dump` on the people ledger.** Whole-file rewrites of the
  4900+-entry ledger (for dedup or promoted-entry removal) produce
  7000+-line diffs. Use targeted `patch` string replacement against the
  specific entry block.
