---
name: paper-ingest
description: "Use when ingesting one paper or filling a paper stub. Resolve identity, retrieve sources, distill, integrate, and verify."
triggers:
  - "ingest this paper"
  - "ingest a paper"
  - "paper ingest"
  - "fill a paper stub"
  - "stub fill"
  - "ingest this DOI"
  - "add this paper to the brain"
eval_contract:
  goal: Resolve and faithfully distill one paper, then complete its required bibliography, author, and graph integration.
  dimensions:
    - "IDENTITY — title, identifiers, version, and complete individual authors match verified sources"
    - "EVIDENCE — findings and limitations reflect the retrieved source and its completeness"
    - "OWNERSHIP — each worker owns its assigned paper; shared writes have one owner"
    - "COMPLETION — citation provenance, author wiring, propagation, and final checks all land"
  hard_fails:
    - Declaring an unwired page-only result a complete ingest.
    - Clearing enrichment on abstract-only or substitute-preprint distillation.
    - Losing citing edges or wiring to a known wrong author identity.
---

# paper-ingest — single-paper ingestion

Resolve, retrieve, distill, integrate, and verify one paper. New papers and
existing stubs use the same pipeline. A direct request or the calling
workflow authorizes ingestion; delegation adds no eligibility classifier,
prerequisite stub, or session boundary. Small jobs may run inline.

## Ownership and completion

- **Inline/full:** the primary owns the paper and its bibliography, author,
  graph, propagation, and final-verification work.
- **Delegated/page-only:** the worker owns only its assigned paper and
  uniquely prefixed source/scratch files. It resolves author identities but
  does not mutate people, the ledger, concepts, bibliography stubs, or the
  inbox; it does not rename/delete other pages or perform Git operations.
  Parallel paper workers always use this mode. The parent owns shared writes.
- After distillation remove the stub tag but retain `needs-ingest: true`.
  Return PAGE_READY with source-linked bibliography candidates and remaining
  obligations. Only the primary/parent clears the flag after integration and
  verification. `needs-enrichment` describes source limitations, independently.
- Return `status` (PAGE_READY, SUCCESS, FAILURE, or SKIP), `input_path` when
  updating, `canonical_path`, `changed_paths`, `remaining_obligations`, and
  `diagnostic`. Report holds explicitly in the diagnostic; do not count them
  as success. A vanished input path does not prove a merge succeeded.
- Save source metadata or re-fetchable identifiers, not merely author counts
  or a child summary that may be truncated. Parents read returned pages and
  source-linked evidence, opening original passages as needed; they do not
  routinely reload every manuscript. File existence is not completion.

Read the profile conventions for `frontmatter.md`, `page-kinds.md`,
`quality.md`, `graph-and-links.md`, `paper-stubs.md`, and `author-ledger.md`.
They resolve under `skills/conventions/` through the profile binding.

## Conditional reading

| Situation | Read |
|---|---|
| Invoking a helper | `references/script-commands.md`; resolve `scripts/` from this skill, use Python >=3.10 and required dependencies. |
| New production ingest retaining any PDF | `references/source-package-integration.md`, `references/qualified-enrichment.md` and the document-format-parsing skill; use the deployed source workflow and qualified figure/table enrichment. |
| PubMed identity or PMC source | `references/pubmed-pmc-retrieval.md` |
| arXiv, bioRxiv/medRxiv, or a conference/published twin | `references/preprint-conference-retrieval.md` |
| Publisher access failure, archive fallback, or browser download | `references/publisher-blocks.md`; for Nature markup/access states also `references/nature-metadata-extraction.md`. |
| XML parse failure, omitted tables/captions, or reference extraction | `skills/pmc-xml-tools/SKILL.md` |
| Brief/source disagreement or suspect sibling attribution | `references/brief-vs-fulltext-verification.md` |
| Author alignment and parent-owned wiring | `references/author-ledger-mutation.md` |
| Explicit satellite topology or an erratum reassigning results | `skills/paper-ingest-vault-modes/SKILL.md` |

Do not load every retrieval reference for every paper. Keep scripts/tests at
this skill's `scripts/` path; they are executable helpers, not required prose.

## Phases

### 1. Identity resolution

Resolve the intended paper before writing. Compare the source title against
the request/citation title, then verify authors, year, venue, identifiers,
and version. A DOI match against a wrong PMID can confirm the wrong paper;
identifier agreement alone never replaces the title check. Seed identifiers,
brief warnings, and bibliography metadata remain candidates until verified.

For PubMed-indexed papers use the article's PubMed XML and EPMC record;
otherwise use the original preprint/venue/publisher metadata. Crossref,
DataCite, and other indexes supplement these sources. A complete matching
primary record can establish identity when another index is unavailable.
Resolve contradictory records against the primary article, not an automatic
ranking of index names. Record corrected identifiers and venue/author claims.
A venue-only mismatch with otherwise matching identity is not a new paper.

Use the complete individual-author list, including middle authors; do not
reduce collective-associated authorship to the corresponding author. An
explicit `doi: null` or `authors: []` is valid only with source evidence of
no DOI or no named individuals, respectively. Resolve author slugs before
writing through Phase 8. A wrong seed first author does not justify a wrong
citation or identity; flag any assigned-filename conflict to the parent.

Distinguish paper DOIs from dataset/structure DOIs. A `10.2210/pdb...` record
identifies a structure; look for the associated article rather than using
its DOI as an unverified article identity. When no article DOI exists,
record that absence and preserve the structure identifier separately.

### 2. Dedup against the brain

Run `dedup_check.py` with resolved DOI/PMID/title and the explicit target
instance before a page write. Exit 0 permits creation; exit 1 names matches
and their STUB/FULL state; exit 2 is an invocation error. Title-only matches
need identity review: corrections, replies, and related papers can share
similar titles. Enrich an existing full page or fill its stub rather than
creating a second page at the requested slug.

For a fill or merge, preserve `cited_by`, producer/source provenance, citation
seed, and attempt history under `paper-stubs.md`. A page-only child proposes
cross-page merges/renames; the parent verifies the canonical target, preserves
the union of citation/provenance data, and repairs inbound references before
removing a duplicate. Re-read current files before mutation.

### 3. Retraction and integrity check

Check publication types and correction/withdrawal relations in the canonical
records. Distinguish the primary paper, erratum (`ErratumFor`/`ErratumIn`),
and commentary (`CommentOn`). Load-bearing retracted work can be retained,
but carries a prominent body warning and an explicit retraction flag in
handoffs. A preprint withdrawal is not automatically a retraction; preserve
the notice and investigate the superseding version. Use vault-modes when an
erratum reassigns results inside the paper. Never silently select stale data.

### 3.5. Pre-dispatch identifier validation

For bulk dispatch, run `validate_identifiers.py --batch … --recover` before
sending workers. Its validated/recovered dispatch list supplies checked
identities, not delegation authorization. Review HOLD results against the
primary record; older title formatting, surname variants, and punctuation
can defeat heuristics. Confirm title, authors, year, and identifier relations
before releasing a hold; log the source-backed override. Surface retractions
and unresolved identities instead of silently dispatching them.

### 4. Full-text retrieval

Use the applicable source reference. `fetch_fulltext.py` provides a useful
HTTP ladder, not the full retrieval procedure: it lacks browser/paperclip
routes and abstract-only closure. Validate every returned candidate even
when provenance is nonempty. Exit 0 or `provenance: none` proves neither
successful retrieval nor source unavailability. Follow remaining routes when
the helper misses, selects the wrong version, or returns a preview.

**Independent obligations:** attempt readable body text, the original
manuscript PDF, and each relevant supplement separately. Use observed source
links rather than guessed attachment paths. Record which were obtained,
failed, or unavailable; do not infer one from another. Archive only through
the source-archive convention when required/requested; no R2 pointer is
claimed without verified archival. Retrieval alone does not imply archival.

**Retained-source production route:** for new ingests retaining any PDF, follow
`references/source-package-integration.md`. Enable `fetch_fulltext.py
--evidence-dir` and preserve other-route originals and failed attempts in new
source/attempt directories. Record the inspected attachment listing and each
retrieval disposition; unavailable raw responses remain explicit limitations.
Readable body text may be extracted from a retained original PDF, with its
source recorded; obtaining text does not replace retaining the PDF.

Run `source_package.py prepare` with operator-verified identity, observed
links, explicit endpoint and application-post budget. Use every physical page
and all accepted extraction channels for manuscript and supplementary PDFs.
Retain non-PDF attachments with deferred-extraction dispositions; deferred
extraction alone is not an automatic completion hold or permission to make
claims from unread data. Acquisition and PDF-extraction failures remain holds.

Use the registered workflow capability (Hermes: `paper_workflow`) for actual
phases. Preparation, counting, sealing, separately authored approval and
execution remain distinct gates. Preserve the accepted method settings and
use absolute paths and a fresh external attempt directory for every operation.
Require subprocess status plus matching phase evidence; report success can
still describe incomplete work. Never automatically retry consumed or uncertain
requests. A hard-killed launcher may leave a child requiring inspection.

**Acceptance:** verify the retrieved title/identifier/version against Phase 1.
For PDFs, require PDF bytes, successful parsing, and paper-specific content
beyond the first page. A browser page-print is not the manuscript. Validate
non-PDF supplements by their format and content. A supplement may lack an
article DOI or cite an unrelated standard: retain the observed article-to-
attachment hyperlink and check its role/content association rather than
requiring its first DOI to match the paper.

**Completeness:** headings, byte count, paragraph count, and HTTP 200 are
insufficient. Reject login/challenge HTML, abstracts with reference lists,
and truncated extracts as full body text. Check the source's actual section
structure, including thematic headings. Parsers may omit table cells,
reference lists, floats, equations, or captions; inspect the original XML,
PDF, HTML tables, or supplements for claims dependent on those elements.
No fixed paragraph threshold establishes completeness. For source/crop
inspection on the retained-source route, use the dedicated pinned inspection
capability (Hermes: `paper_vision_inspect`), not generic vision routing. Supply
original pages and ordered crop fragments when visual evidence is required.

**Abstract-only closure:** exhaust applicable authorized retrieval routes and
record actual source responses. For PubMed-indexed papers the existing
three-source check requires an EPMC record indicating `inPMC: N` and
`isOpenAccess: N`, Unpaywall indicating closed/not OA, and Semantic Scholar
`openAccessPdf` null/CLOSED. A GREEN/BRONZE or other available-copy lead must
be attempted. A valid PMCID is also a lead despite stale EPMC flags. Empty
results, missing credentials, a provider failure, and 403/429/5xx responses
are unavailable evidence, not closed records. Contradictory access metadata
requires investigation, not an abstract-only conclusion. Record an unresolved
access blocker if closure cannot be established; do not claim this gate passed.
For preprints not covered by those indexes, check the original versioned
source, published twin, and applicable repository/mirror routes as described
in the preprint reference; unavailable APIs never count as closed evidence.

When justified abstract-only distillation is used, set `fulltext_source:
abstract-only` and `needs-enrichment: true`. A preprint used instead of an
existing published article also retains enrichment. A complete preprint
without a published twin need not be flagged. Attribute preview/caption-only
claims to those exact sources; do not invent missing methods/results.

### 5. Distillation and page write

For the retained-source PDF route, first verify the source-only v1 handoff;
then follow `references/qualified-enrichment.md` through the deployed enrichment
capability (Hermes: `paper_enrichment`) and final v2 handoff. The code-owned
roster includes all eligible figures/tables; algorithms are deferred by default.
Retain failed/partial/unavailable outcomes and unreviewed scope. Import actual
review findings without replacing original extraction. An empty finding list
or model-authored coverage is not certification. Preserve exact-use qualifications
beside affected content and the canonical qualification register in the paper.
A source-only v1 handoff is intermediate evidence, not completion of this new
route. Read the final handoff's exact generated summary,
`facts.json`, acquisition dispositions and source material. Use the handoff's
package-relative paths to native text, original pages, ordered crop fragments
and classification/association artifacts; counts and model labels are not
scientific findings. Text-only operators use saved inspection findings and
cannot claim personal pixel inspection. Same-model extraction and inspection
are not independent verification. Mechanical completion does not establish
exhaustive recall or human acceptance; new outputs do not inherit historical
acceptance, and the development pilot does not impose human crop approval on
every production ingest.

Add unformatted `Source package: <relative-path-to-v2-handoff.json>` and
`Annotated enrichment: <relative-path-to-annotated.html>` lines in the existing
Ingest log, relative to the paper page; do not add frontmatter fields. Preserve
the exact v2 `qualifications.txt` text in the paper. Record source versions,
limitations and scientific review decisions.
An explicitly source-limited draft may proceed from incomplete evidence, but
acquisition/extraction holds retain `needs-ingest: true` and appropriate
`needs-enrichment: true`; they are not silently waived by body-only prose.
A fixture/test-only handoff never qualifies as production completion.

Read a recent sibling page for the vault's style and the paper-kind schema
for required fields; an existing page is not scientific evidence for this
paper. Write Abstract / Context / Approach / Findings / Limitations /
Analysis / Citation / Ingest log. Preserve the canonical abstract verbatim;
for an editorial with none, say so and use its body rather than inventing one.

Verify the brief's findings and terminology against the retrieved source.
Use the paper's claims when they disagree, flag the discrepancy, and leave
cross-page/working-document correction to its owner. The conditional brief
reference covers synonyms, conflation, absent terms, and sibling citations.
A failed term search does not prove the term never exists in the field.

Findings include specific results and their source locations, separating
observations from interpretation and future work. For abstract-only input,
read every sentence: capture stated structural resolution/composition,
discovery method, epitope, animal model/survival/time window, cross-reactivity,
and affinity/potency where present. Do not assume unstated details from the
lab's reputation. Note unresolved internal numerical inconsistencies rather
than averaging or silently correcting them.

For a dive, look up the paper's identifiers in the campaign working document.
Carry its verified role/open question into Context; no match is not an error.
Keep review-derived context attributed to the review, not to an unread primary.

Frontmatter uses `status: published|preprint|unknown`, complete aligned
`authors`, and truthful `fulltext_source` provenance under `frontmatter.md`.
The helper's label describes a candidate route, not evidence that its body
was accepted. Never label a retrieved PDF as user-provided or HTML to satisfy
a supposed enum. Keep exact source URL, version, and limitations in the log.

On fills, preserve original `stub_source`, valid citing edges and their order,
and previous failure counts. Initialize absent `ingest_attempts` to zero;
success does not reset it. Increment only actual failed attempts, recording
date/diagnostic. Holds/skips are not failures. Page-only results retain the
queue flag until parent completion; source-limited success retains enrichment.

### 7. Bibliography walk

Create/update stubs for load-bearing references: methods, datasets, and
frameworks without which the paper's argument would fail. Background citations
are not stubs. Use source citation text/identifiers, not recollection, and the
shared `paper-stubs.md` shape and five-distinct-citing-source queue rule.
Never reset an already queued stub or recursively ingest the reference tree.
Only actual paper/grant citations belong in `cited_by`, not topic relevance.

Page-only workers return source-linked candidates; the parent verifies them
and writes shared stubs. A literature dive explicitly owns review-bibliography
tiering and may defer that review's automatic stub creation to its Phase 3;
this does not mean the skipped walk created stubs.

For a direct single-paper ingest opening a thread the brain may not pursue,
record source-backed anchors as `### Deferred stubs` in the Ingest log instead
of minting isolated stubs. Include identifiers and one-line roles. Dive
work does not use this shortcut for required Tier 2 stubs. A later anchor-set
dive can reuse the deferred list only after identity validation and dedup.

### 8. Author ledger

Before page writing, load `references/author-ledger-mutation.md` and align
all named individuals against both people pages and ledger entries. The
helper is a candidate finder; inspect abbreviations, particles, surname
collisions, ORCIDs, affiliations, and source history before reusing slugs.
An unresolved identity conflict holds completion.

The primary/parent performs the canonical mutation branches: existing person
gets `author_on`, existing ledger entry gets `citations`, new author gets an
entry, and threshold/manual promotion follows `enrich` and the convention.
The append-new helper is not an existing-entry updater. Preserve source names,
verified identifiers, and previous citations. Verify every paper-author edge,
not merely that each slug resolves. Do not reconstruct missing source values
from a truncated child summary or a count-only Ingest log.

### 9. Graph wiring and propagation

The primary/parent searches existing concept/project pages and adds relevant
forward typed edges according to the graph convention. Use targeted patches
on shared lists, not whole-page rewrites. Do not create backlinks sections.
When no relevant target exists, leave `links: []` and record the search
outcome in the ingest log; never link an unrelated page to avoid an empty
list.

Append a deduplicated propagation event under `items:` in
`docs/rem-cycle/inbox.yaml`, preserving the existing list's indentation:

```yaml
- consumed_by: []
  date: YYYY-MM-DD
  event: ingest            # or stub-filled
  id: <YYYY-MM-DD>-<slug>
  page: papers/<slug>
```

The usual file uses column-zero items and two-space fields. Parse after the
append and verify the intended item/count and absence of duplicate IDs/keys.
A paper worker never edits this inbox.

### 10. Verification

This completed-fill contract is shared by dives and queue drains. Verify:

- YAML, `kind: paper`, slug/filename agreement, nonblank title/venue, positive
  integer-valued year (integer or decimal string, not boolean), allowed status,
  explicit verified bare DOI or source-confirmed null, complete distinct
  `people/<slug>` authors, no stub tag, and accepted-source provenance.
- Source-backed exceptions only: `authors: []` requires no named individuals;
  missing metadata or dropped authors is not that exception. If no identifier
  is usable by the helper, its canonical result remains UNVERIFIED; obtain
  independent source evidence and report the unresolved machine check.
- All eight body sections contain source-grounded content or explicit source
  limitations. Source-limited distillations carry enrichment. Compare findings,
  authorship, and version to the source; count equality alone is insufficient.
- Original citation/provenance/attempt fields survive; merges preserve the
  citation union and resolve at the returned canonical path.
- Required bibliography decisions, each author's `author_on`/`citations` edge,
  graph integration, and the propagation event are complete and read back.

Run `verify_ingest.py <bare-slug> --instance <brain> --require-filled`.
For the retained-source PDF route, add both `--source-package-handoff
<absolute-handoff.json>` and `--source-package-method <absolute-trusted-method>`
using the documented PDF interpreter. For every new retained-PDF ingest also
supply `--require-enriched-source --enrichment-integration <trusted-integration>
--enrichment-root <trusted-frozen-enrichment-root>`. These options are mandatory
for this route, including PAGE_READY checks; the final handoff must be v2 and
its qualifications and annotated pointer must survive in the paper. Legacy
v1 verification remains available for historical/non-enriched routes only.
Revalidation binds the current sources, workflow,
launcher evidence and exact generated summary to the paper identity and its
relative Ingest log pointer. An earlier completion flag is insufficient.
For PAGE_READY add `--page-only`: the queue flag remains true and only
well-shaped unresolved author references are deferred; other errors fail.
After parent integration set `needs-ingest: false` and rerun without
`--page-only`. For a declared ledgerless satellite, load vault-modes and use
its explicit `--ledgerless`; never use it to hide a damaged main-brain ledger.
Offline mode checks structure only and cannot waive a failed online identity
check. The helper does not validate external URLs as filesystem links.

Run the platform `lint-frontmatter.py` with the target instance and exact
changed paths, from the brain root or with absolute `--paths`. Inspect its
output and exit code; passing the ingest helper is not schema validation.
Do not mask a failing exit in a pipeline or commit through it. A known wrong
author/source remains a hold even if mechanical checks pass. The converse
also occurs: a canonical-identity FAIL where DOI, venue, and authors all
match and only the title differs in one index is a metadata-variant
artifact (a publisher landing-page H1 against the proceedings title page);
record the variant and the authoritative source in the ingest log rather
than treating it as a wrong paper. Identity merges outside this ingest
route to entity-resolution with preserved evidence.

**Closeout:** use `skills/git-ops/SKILL.md`. The standalone primary/parent
closes the verified paper and required shared work as a coherent unit, not
merely a returned wave. Children return paths/obligations only. PAGE_READY is
not a completed ingest; no automatic amendment, force-push, or shared-file
restore is permitted.

## Shared-write discipline

One parent serializes ledger, inbox, people, concept, and merge writes.
Workers use unique PMID/slug-prefixed scratch names; the shared browser has
one controller. Re-read on concurrent-modification or patch-match warnings;
anchor edits on unique identity/context and verify the exact target afterward.
Never restore the entire ledger from Git to recover one failed edit. The
canonical ledger reference owns its lock, append/update, and validation rules.
