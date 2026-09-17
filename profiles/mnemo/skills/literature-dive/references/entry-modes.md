# Entry modes, bibliography discovery, and identifier recovery

Load when the entry point is anything other than a straightforward
recent-review search, when a paywalled review's reference list must be
obtained, when Tier 1 must be identified without a bibliography, when
validator HOLD entries need resolution, or when tiering from an HTML
citation graph. Core selection rules, tier bars, and gates stay in
SKILL.md; this file carries the mechanics. Host execution discipline
(interpreter, supported command forms, rate limits) is owned by
`paper-ingest/references/script-commands.md` — load it before running
any command here. Dated observations carry their tested scope; they are
not permanent provider-wide claims.

## Entry mode 1 — review-anchored (default)

Search PubMed for recent reviews on the topic, filtered to high-impact
review journals, and present 3–5 candidates (journal whitelist and
presentation format are in SKILL.md Phase 1).

**Search template (REST API; no Entrez Direct installation required):**

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<URL-encoded-query>&retmode=json&retmax=30" -o /tmp/esearch.json
# Then fetch summaries in a SINGLE batch call (comma-separated IDs):
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=<comma-separated-IDs>&retmode=json" -o /tmp/esummary.json
```

Use uniquely prefixed output files and parse the saved JSON. Follow the
supported command forms and protection boundaries in script-commands.md;
a rejected shell syntax may need a file-intermediary form, but an
authorization refusal cannot be bypassed with another tool. Encode raw
query parameters once rather than manually concatenating brackets/parentheses.

Query shape: `<topic>[Title/Abstract] AND (review[pt] OR review
literature[pt]) AND (<whitelist journals>)`, mindate 2–3 years back.
Bracketed field tags need `%5B`/`%5D` encoding in curl. If PubMed
returns too few, broaden: drop the journal filter, widen the date range,
or search bioRxiv. If too many, narrow: add the `review[pt]` filter, or
prioritize by citation count (PubMed Relative Citation Ratio if
available, or CrossRef citation count). Respect the E-utilities rate
limits in script-commands.md.

## Entry mode 2 — semantic-first (fast-moving fields)

When the field moves so fast that reviews lag by 6–12 months, use
`paperclip search -s arxiv,biorxiv` (or the domain-appropriate sources)
with multiple semantic queries covering the field's clusters as the
PRIMARY discovery tool, not just a Phase 5 supplement. The spine survey,
if one exists, provides the taxonomy; the semantic search finds the
frontier the survey missed. For fields where no adequate review exists,
skip the review-anchored protocol entirely and build Tier 1 directly
from semantic search results, grouped by cluster: run 6–10 semantic
queries, dedup against the brain, present the cluster map + candidate
count for scope approval, then ingest under Phase 4's explicit modes.
If semantic search is unavailable, use domain-appropriate keyword sources
and state the recall limitation; keep the same scope and evidence checks.

## Entry mode 3 — seed-corpus (anchor sets)

When your human hands you a paper whose load-bearing references form a
near-complete causal chain — typically an ingested paper whose Ingest
log names deferred anchor stubs (`paper-ingest` Phase 7's deferred-stubs
round trip hands off exactly this shape) — the dive can start from those
anchors directly: resolve and validate every anchor identity (Phase 3.5
rules), ingest them under Phase 4's explicit modes, and run the
review-discovery search in parallel; the spine review, when one exists,
is ingested as a supplementary paper rather than before the corpus.
Tier classification then runs against the anchors' own
deferred-reference logs plus the review when it arrives.

## Bibliography discovery (paywalled reviews)

Use the verified original reference list when available. If the review's
bibliography cannot be retrieved directly, try these metadata sources;
none proves how the review discussed the cited paper:

1. **Semantic Scholar Graph API** (`api.semanticscholar.org/graph/v1/
   paper/DOI:<doi>?fields=references.title,references.externalIds,
   references.year,references.authors`) — the default. Works even when
   the publisher page is Cloudflare-blocked and Europe PMC has no
   open-access copy. Caveats: rate-limits aggressively (429), sometimes
   returns 0 references for valid DOIs (do not treat empty as
   definitive), and reference PMIDs can resolve to completely different
   papers (an observed SS PMID resolved to an unrelated vaccine paper).
   Validate both DOIs and PMIDs under Phase 3.5; neither field is
   guaranteed correct by the provider.
2. **OpenAlex Graph API** (`api.openalex.org/works/doi:<doi>`) — the
   fallback when Semantic Scholar returns 0 references or rate-limits.
   Returns `referenced_works` as OpenAlex IDs; batch-resolve in groups
   of 25 via
   `api.openalex.org/works?filter=openalex:W1|W2|...|W25
   &per_page=25&select=id,title,publication_year,cited_by_count,ids`,
   0.5s sleep between batches. The most reliable reference-list source
   observed (astrovirus dive, 2026-08-07: SS returned 0 refs for a
   valid Elsevier DOI; OpenAlex returned all 158, 149 resolved).
3. **Europe PMC / PubMed source records** — resolve the review's identifiers,
   inspect available reference records or original full-text XML, and use
   the documented article-reference interface when applicable. Do not assume
   every core search response contains `referenceList.reference[]`. Missing
   fields or service errors mean this route is unavailable, not an empty
   scholarly bibliography.

**When ALL reference-list sources return empty.** Very recent reviews
(published within the last few months) may not yet be indexed anywhere.
Do NOT treat this as dive-blocking. Two fallbacks: (1) use the other
selected reviews' bibliographies — the spine review's list is preferred
but not exclusive; (2) PubMed-driven Tier 1 identification (below).
Observed 2026-08-07 (filovirus dive): spine review had no PMC OA, no
Wayback snapshot, SS `references: None`, Europe PMC 0 refs — the Tier 1
list of 13 was built from the other three reviews' bibliographies plus
targeted PubMed searches.

**nature.com review pages:** when the review is read as publisher HTML,
`paper-ingest/references/nature-metadata-extraction.md` owns the
`citation_*` meta-tag technique (including `citation_reference`, the
full reference list from the page head) — load it rather than
re-deriving the extraction.

## PubMed-driven Tier 1 identification (no bibliography available)

When the spine review's reference list is unavailable, identify Tier 1
papers through targeted PubMed searches instead of a curated
bibliography:

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

## Tiering from the citation graph (HTML review bodies)

When the review is read as HTML, the body's citation anchors encode
which paragraphs cite which reference. The tally is an evidence locator
that prioritizes reading (SKILL.md Phase 3 owns the rule); this section
is the extraction mechanics.

**Observed selector (Nature markup, 2026-09):** citation anchors render
as `a[data-test="citation-ref"]` with `href="#ref-CR<N>"`. This is an
observation of one publisher's DOM at one date, not a universal
template — other publishers (and future Nature redesigns) differ, so
inspect the actual page before writing an extractor. In Nature
reference lists, each citation renders as a text paragraph followed by
a link-chrome paragraph carrying the DOI `href`s (URL-encoded, `%2F` =
`/`); PMIDs are not in the hrefs — resolve by title via a PubMed batch
when needed.

**Extraction order matters.** Extract the anchor→reference map with a
DOM walk over the article body BEFORE converting to plain text — text
conversion strips the citation markers and they cannot be recovered
from the text. If the conversion already happened, re-fetch the source
HTML; the anchors may be recoverable from the original page.

**Context, not a bare list.** A paragraph/section tally supports the
"discusses in detail" reading but never replaces it: read the citing
passages before assigning the tier, and preserve the citation's
provenance (which review, which passage) in the tier-classification
output. The main skill's rule holds: no paragraph-count threshold
assigns a tier automatically.

## HOLD resolution (Phase 3.5 detail)

The validator's title-matching heuristic is conservative; a HOLD is a
request for human-verifiable evidence, not a verdict. Known false-HOLD
shapes, each resolved by one PubMed `esummary` batch call over the
HOLD PMIDs — if PubMed returns the expected title and the other
identity fields agree, the paper proceeds:

- **Older papers (1990s–2000s)** with slightly different PubMed title
  formatting can fail the title-similarity threshold even when the
  PMID is correct (astrovirus dive, 2026-08-07: 17 of 33 Tier 1 papers
  flagged HOLD; all 17 PMIDs verified correct via PubMed batch, all
  dispatched successfully).
- **Hyphenated surnames** (observed 2026-09-05, adaptive-immunity-CNS
  dive: "Eme-Scolan" scored 100 on the PubMed title check but OpenAlex
  reported `surname_match: false` against resolved first author "Elisa
  Eme-Scolan", verdict MIXED).
- **Curly-apostrophe title variants** (same dive: "ageing and
  Alzheimer's disease" with U+2019 scored 99.2–100.0 but failed the
  surname check while PMID↔DOI consistency and PMCID resolution both
  passed) — the defect is apostrophe normalization, not identity.
- **Bare-digit "PMCIDs"** — a "PMCID" that lacks the `PMC` prefix (bare
  digits from a parse) is not a PMCID: confirm against the EPMC core
  record before routing retrieval through it.
- **Legacy author-manuscript PMCIDs** — the converse: a
  properly-prefixed PMCID can look wrong and still be right. A recent
  paper carrying an older author-manuscript PMCID (same dive, Antila
  2024 Nat Cardiovasc Res: PMC7616318, MID EMS196559) is the same
  record, not a mis-mapping; `efetch db=pmc` + title match settles it
  before the identifier is discarded.
