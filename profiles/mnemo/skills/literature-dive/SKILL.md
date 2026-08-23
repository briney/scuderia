---
name: literature-dive
description: A structured deep literature dive — start from recent high-impact reviews (or semantic search for fast-moving fields), ingest the foundational primary literature tier-by-tier, search for what the initial pass missed, run one informed supplementary pass to close gaps surfaced by the dive itself, and synthesize the result into a concept page.
triggers:
  - "deep literature dive"
  - "literature dive on"
  - "comprehensive literature review of"
  - "deep dive into the literature on"
  - "systematic literature dive"
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
> `skills/conventions/preprint-retrieval.md` (bioRxiv full text).

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
| **Tier 1 (primary)** | The review itself + primary literature the review discusses in detail | Full `paper-ingest` immediately. No stub. Bypass the threshold gate. |
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
candidate count for scope approval, then dispatch ingestion batches.

The two methods are complementary, not substitutes. Observed 2026-08-10
(DLM dive): the spine survey provided the taxonomy but missed the entire
current-year wave; 8 semantic queries surfaced 75+ Tier 1 candidates in 9
clusters — while the survey's bibliography added 5 Tier 1 papers the
semantic search missed. Some dives will use both: survey for taxonomy,
semantic search for the frontier. Confirmed at scale in a second dive
(protein structure tokenization, 27 papers) with no survey at all.

### 2. Review ingest (delegate with read-back)

Ingest the selected review(s) with `paper-ingest`. When there is only
one review, ingest it directly (spine — first contact with material
entering the brain). When there are multiple reviews (your human's
preference is often comprehensive — he chose "all five" when offered
three), delegate the additional reviews as subagents to keep the
orchestrator's context window clean.

**Delegation vs. direct.** The first review (or the spine review — the
one the tier classification builds on) is ingested directly. Additional
reviews can be delegated with read-back verification, because the
selection decision (your human chose them) is the vetted judgment that
justifies delegation, just as the review's citation justifies
delegating Tier 1 papers.

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

**Do NOT walk the bibliography (Phase 7) for review papers.** The
literature-dive orchestrator handles tier classification separately
(Phase 3). Instruct delegated subagents to skip Phase 7 — the
orchestrator will classify the review's references and dispatch Tier 1
papers itself.

### 3. Tier classification

After the review is ingested, read its full text (or the reference list
obtained via Phase 2) against the stubs Phase 7 created. Reclassify the
bibliography into three tiers.

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

**Dedup against the brain.** Before presenting, check each Tier 1 DOI
against existing `papers/` pages — some may already be ingested.
Already-ingested papers are listed but not re-ingested.

**Non-duplicative filter (your human's standing rule for large dives).**
Before ingesting a Tier 1 candidate, ask: does this paper add something
the brain does not already hold, and does it add something a sibling
Tier 1 paper in the same dive does not already cover? A review that
"discusses in detail" a topic the brain already ingested in a prior dive
does **not** need a second full ingest — note it as already-covered and
drop it from the dispatch list. The Tier 1 bar is "discusses in detail
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
one-line reason for tier classification) and confirmation that Tier 2
stubs are in place. Present the Tier 1 list to your human for a quick
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
human explicitly, not dispatched. Phase 4 dispatches using the
validator's `dispatch` list — never the raw bibliography identifiers.

**PubMed batch verification for HOLD entries.** The validator's
title-matching heuristic is conservative — older papers (1990s–2000s)
with slightly different PubMed title formatting can fail the
title-similarity threshold even when the PMID is correct. When the
validator returns HOLD entries with PMIDs, verify them via a single
PubMed `esummary` batch call: if PubMed returns the expected title for
each PMID, the PMID is correct and the paper can be dispatched. Do NOT
discard a paper solely because the validator's title-match heuristic
failed (astrovirus dive, 2026-08-07: 17 of 33 Tier 1 papers flagged
HOLD; all 17 PMIDs verified correct via PubMed batch, all dispatched
successfully).

### 4. Tier 1 ingest (delegate with read-back)

Ingest each Tier 1 paper. The review's citation is the vetted decision
that this paper belongs in the brain — the equivalent of the upstream
stub-creation decision that justifies the `paper-ingest` queue-drain
carve-out (`SOUL.md` §2). Delegation is appropriate here: spawn
subagents in small batches, then read the resulting pages back to
verify before declaring success.

**Delegation protocol — follow `batch-drain`.** The dispatch/yield/verify
loop for large dives is the `skills/batch-drain/SKILL.md` primitive; load it and
follow it for every multi-batch dive. The dive-specific bits below override only
the *content* of each subagent task, never the scheduling discipline.

- Batch at most 3 (the concurrent delegation pool limit — a 4-paper
  `delegate_task` call is rejected at dispatch with "Too many tasks:
  max_concurrent_children is 3"). The remainder (list size not a multiple of 3)
  is dispatched as a single-task call, never via batch mode.
- **Yield and wait after each dispatch.** Do not emit new dispatches while a
  batch is in flight (see `batch-drain` — the core invariant). This is the fix
  for the truncation loop (`finish_reason='length'`) and the dropped-remainder
  failure seen on prior dives.
- Pass each subagent the *validated* DOI/PMID from the Phase 3.5 dispatch list
  (never the raw bibliography identifiers) and the context that this is a Tier 1
  paper from a literature dive (so the subagent knows to do a full
  `paper-ingest`, not a stub fill).
- The subagent inherits `paper-ingest` and does the full pipeline: resolve
  identity, dedup, distill, file, wire, bibliography walk.
- On return, verify files on disk, then commit, then dispatch the next batch.
  After the last batch returns, do a bulk read-back verification (a Python script
  checking all files at once — frontmatter parses, DOIs present, authors
  populated, body sections present). Never trust the subagent's "completed"
  report — disk is truth.

**Foreground work during ingestion batches (narrow and gated).** Permitted
*only* when it does not depend on the in-flight batch's outputs (see
`batch-drain`). The legitimate class is: read the existing related concept pages
to map what the brain already knows, use the spine review's framework as the
organizing structure, and compile a working document at `working-docs/<topic>-*
-list.md` (e.g. every virus family, its entry mechanism, receptor, endocytic
route). This working doc is NOT a brain page (no frontmatter) — it is a
transitory document that informs the Phase 7 synthesis. It proceeds in parallel
only because it does not consume the running results. **Do not build the Phase 7
concept page (or any downstream synthesis) while its evidence papers are still
ingesting** — that artifact depends on the in-flight batch and gets rebuilt.

**Context management.** Each subagent runs in an isolated context, so
the orchestrator's context window does not accumulate 10–20 full paper
distillations. The orchestrator receives only the final summary per
paper. The read-back verification is a single `brain-read` per page —
cheap.

**Subagent task construction rules.**
- Specify frontmatter status values: "use `status: preprint` for all
  preprints and arXiv papers, `status: published` only for papers in
  published journal/conference proceedings. Never use `withdrawn`,
  `accepted`, `in review`, or other non-enum values" — the linter only
  accepts `preprint`, `published`, `unknown`. Withdrawal/acceptance
  status is a body detail, not a frontmatter enum.
- Remind subagents the identifiers provided are validated but identity
  verification against PubMed is still Phase 1 of their ingest.
- Do not include arXiv API curl commands (blocked — see Environment
  preflight). Point them at paperclip meta.json + fetch_fulltext.py
  instead. `paperclip cat --full /papers/<id>/content.lines` is a proven
  third-tier full-text fallback when `fetch_fulltext.py` fails
  (Cloudflare blocks, jina misses, new bioRxiv DOI prefixes, arXiv HTML
  not rendered); use `fulltext_source: paperclip-biorxiv` or
  `paperclip-arxiv` accordingly.
- For large dives (>15 papers): instruct subagents to write ONLY their
  paper page — no `people/_ledger.yaml` edits, no concept/method-page
  links, no rem-cycle inbox appends. Subagents return their author lists
  (name + slug + affiliation) in their summary; the orchestrator
  performs all ledger entries and concept/method-page wiring centrally
  after each batch. This eliminates concurrent-write races on shared
  files. For small dives (≤5 papers), subagents do their own wiring as
  in the standard `paper-ingest` pipeline.

**Centralized ledger wiring pitfalls (large dives).**
- *Misplaced citations.* When appending a citation to an existing
  author's ledger entry, the `  - papers/<slug>` line must go inside the
  entry's `citations:` block — between the last existing `  - papers/`
  line and the `  name:` field. Inserted between `orcid:`/`name:` and
  `slug:`, it breaks the YAML ("expected <block end>, but found '-'").
  Safe pattern: find `  slug: <slug>\n`, search backwards for
  `  citations:\n`, insert after the last `  - papers/` line before
  `  name:`. After writing, `yaml.safe_load()` the ledger to validate.
- *Duplicate entries.* If an author was added to the ledger by a
  subagent during the dive AND the orchestrator's new-entry code also
  finds that slug, a duplicate results — one with real affiliations,
  one with `affiliations: []`. After insertion, count slug occurrences;
  remove empty-affiliation duplicates and merge their citations into the
  real entry.
- *Never `yaml.dump` the ledger.* Whole-file rewrites (dedup,
  promoted-entry removal) produce 7000+-line diffs. Use targeted
  `patch` string replacement against the specific entry block.

**Subagent failures — the filesystem is ground truth.**
- *Reported success, no file.* A subagent can report "completed"
  without writing the file (empty model output, timeout after partial
  work). After each batch returns, check the filesystem (`ls
  papers/<expected-slug>*`). Missing files must be re-dispatched or
  ingested directly.
- *Reported failure, file written (provider-cap-after-write).* A
  subagent can hit a provider usage cap (HTTP 403) AFTER writing the
  page but BEFORE generating its return summary. The reported status
  says "failed" but the file is complete on disk. Check `head -1`,
  `grep -c '^## '`, and author count — if sections are present, the
  ingest succeeded regardless of the report. Do not re-dispatch a file
  that is already there.
- *Wrong identity despite validation.* Even a successfully written file
  may have been resolved under a corrected PMID/DOI different from the
  one tasked. On return, verify the written page's PMID/DOI against
  what the subagent's summary actually resolved to. If multiple
  subagents return different corrected PMIDs for the same paper, one is
  still wrong — re-check both against PubMed.
- *Line-number prefix corruption.* Subagents using `execute_code` to
  write files can bake `read_file`-style line prefixes (`1|---`) into
  the file, breaking frontmatter parsing. The read-back checks the first
  line of each file — if it starts with `1|` (not `---`), strip the
  prefixes before committing.
- *The ledger read-back race.* A subagent can write the paper page
  before it writes the author ledger entries. If the orchestrator
  checks the ledger mid-flight, finds authors "missing," and appends
  them, it duplicates entries the subagent adds moments later. The safe
  pattern: wait until the batch's consolidated result message has
  arrived, THEN check the ledger. Treat an early "authors missing" as
  "not yet written," not "failed" — never append on an early negative.
  (For large dives this race is designed out entirely by centralized
  wiring.)

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
examples lives at `references/gap-map-template.md`.

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

#### 6.4 Consolidation and dispatch

1. Merge the candidates from all three prongs (and any re-anchor).
2. Dedup against the brain and against the dive's existing corpus.
3. Validate identifiers per Phase 3.5 (validator + PubMed batch
   verification for HOLDs).
4. Present the consolidated list to your human, with the reason each
   candidate was surfaced (which gap, which prong, which re-anchored
   review). This is the approval gate.
5. Ingest approved candidates via the Phase 4 delegation protocol
   (batches of 3, read-back verification, centralized wiring if the
   batch is large).

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
`ingest-pending-papers` drains it. Confirm the stubs are correctly
tagged with `needs-ingest: false` and move on. Do not inline-ingest
Tier 2 — that is the exploding paper tree the threshold gate exists to
prevent. (Phase 6's informed snowball is the judgment-driven exception:
papers it promotes are reclassified Tier 1 by human approval, not
inline-ingested as Tier 2.)

### 7. Synthesis

After the supplementary pass is complete, synthesize the result.

**Commit before synthesizing — and earlier.** Commit each verified
ingestion batch promptly, not just at the end: the auto-snapshotter
(`auto_push.sh`, every 5 min) can commit subagent-written pages under a
generic `auto: snapshot` message before your explicit commit, burying
the dive's intent (observed 2026-08-05: 28 paper files snapshotted
generic). The window between batch verification and commit should be
minutes. If the snapshotter beats you, the content is preserved — do not
re-commit or amend (that rewrites history). After the final batch and
before starting synthesis, commit any remaining papers, ledger updates,
and link updates with a descriptive message.

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
- Delegation for Tier 1 ingest keeps the orchestrator's context
  window clean; read-back verification (filesystem as ground truth)
  ensures each page is actually filled.
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
- **Skipping the read-back.** Delegated Tier 1 ingest is
  delegation-with-oversight. The oversight is reading the page back —
  and checking the filesystem regardless of what the subagent reported.
  Reported success with no file and reported failure with a complete
  file are both observed failure modes.
- **Trusting subagent "completed" status.** See the full failure-mode
  list in Phase 4: missing files, provider-cap-after-write, wrong
  resolved identity, line-number prefix corruption, ledger read-back
  race. Verify on the filesystem after every batch.
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

## Changelog

- **2026-08-12 — consolidation + Phase 6.** Folded all ten dated patch
  skills (2026-08-04 through 2026-08-10d) into this file and deleted
  them; patch provenance lives in git history. Added Phase 6 (informed
  supplementary pass: gap map, gap/jargon/snowball prongs, single
  re-anchor on review rediscovery), renumbering synthesis to Phase 7
  and superseding the Phase 5b gap-fill patch. Gap-map criteria and the
  snowball's judgment-over-thresholds selection are your human's
  explicit design decisions from the 2026-08-12 brainstorm.
- **Prior history** (from the deleted patches, all validated in live
  dives): batching/pool limits, non-duplicative selection, and the
  ledger race (2026-08-04, bacterial-toxins dive); FD limit, SS PMID
  caution, REST templates, 429 handling, multi-batch delegation,
  auto-snapshotter race, working-doc pattern (2026-08-05, entry-mechanisms
  dives); identifier unreliability (2026-08-05, ebolavirus dive);
  OpenAlex ladder, HOLD verification, line-prefix corruption, empty-
  bibliography fallbacks, PubMed-driven Tier 1, concept supersession,
  yaml.dump hazard (2026-08-07, astrovirus + filovirus dives);
  provider-cap-after-write, centralized ledger wiring and its pitfalls,
  paperclip full-text fallback, arXiv curl block, fast-moving-field
  discovery, no-survey path, gap-fill pattern, frontmatter status enum
  (2026-08-10, DLM + structure-tokenization dives).
