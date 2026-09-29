---
name: paper-ingest
description: "Use when ingesting a scientific paper, filling a paper stub, or refreshing an existing paper page."
triggers:
  - "ingest this paper"
  - "fill a paper stub"
  - "re-enrich this paper"
eval_contract:
  goal: Produce a fresh source-grounded manuscript page with verified external archiving and guarded publication; defer graph maintenance.
  dimensions:
    - "IDENTITY — title, identifiers, version and complete source author names match verified sources"
    - "SCIENCE — central findings, consequential numbers and caveats reflect the full manuscript"
    - "RESILIENCE — optional failures remain local; publication does not repeat manuscript work"
    - "COMPLETION — verified archive, guarded page application, propagation and explicit deferred graph work"
  hard_fails:
    - Fabricating evidence or silently substituting article identity/version.
    - Processing supplementary sources during ordinary ingestion.
    - Restarting manuscript generation to repair storage, formatting or graph edges.
    - Overwriting concurrent edits or claiming incomplete checks or attachments are complete.
    - Keeping article sources, figures or machine bookkeeping in the brain.
---

# Manuscript-to-page ingestion

One worker acquires, reads and drafts one manuscript. Code publishes the reviewed
page. There is no routine integration agent and no exhaustive/deep fallback.
Use only `start`, `sources`, `read`, `stage`, `publish`, `status` (Hermes:
`paper_ingest`). Read `references/runtime.md`; reuse the same job throughout.
Code owns source IDs, hashes, archives, revisions, pointers and edit guards.

## Fresh replacement contract

Generate a fresh page at the existing filename. Do not read the old page body,
`original.md`, preservation diff, or sibling pages to draft or check the science.
Do not merge old summaries, manual annotations, caveats, metadata or execution logs.
Use the resolved identity seed and verified sources; runtime snapshots and Git
history provide recovery. The runtime rebuilds citation backlinks from explicit
citation fields elsewhere; it does not force legacy `cited_by` into the draft.
Keep the filename so incoming links remain valid. A genuine rename/merge is a
separate source-backed decision with inbound-link repair before deletion.
Concurrent edits still hold publication; explicit reconciliation is separate work.

A delegated worker stages only: no live paper edits, shared graph/ledger writes,
Git, nested delegation, or publication. Standalone ingestion may call publish.
Campaign code publishes eligible staged jobs serially. Missing graph targets,
author associations and bibliography candidates are deferred, not publication
blockers. Never create another paper, method, concept or person to finish ingestion.
Keep candidates and diagnostic notes external. Do not browse runtime implementation
or change tools during an ingestion; report a specific failure and retain the job.

Read frontmatter and paper-kind conventions, using the fresh-replacement contract
above for ingestion. Conditional acquisition references:

| Situation | Read |
|---|---|
| Helper command | `references/script-commands.md` |
| Archive restoration | `references/archive.md` |
| PubMed/PMC | `references/pubmed-pmc-retrieval.md` |
| Preprint/published twin | `references/preprint-conference-retrieval.md` |
| Publisher access failure | `references/publisher-blocks.md`; Nature cases use `references/nature-metadata-extraction.md` |
| XML failure | `skills/pmc-xml-tools/SKILL.md` |
| Brief/source disagreement | `references/brief-vs-fulltext-verification.md` |

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
reduce collective-associated authorship to the corresponding author. Use `author_names` for the complete source author list, in order; `authors`
contains only independently verified people links and may be empty while graph
matching is deferred. An explicit `doi: null` requires evidence of no DOI. A wrong seed first author does not justify a wrong
citation or identity; flag any assigned-filename conflict to the parent.

Distinguish paper DOIs from dataset/structure DOIs. A `10.2210/pdb...` record
identifies a structure; look for the associated article rather than using
its DOI as an unverified article identity. When no article DOI exists,
record that absence and preserve the structure identifier separately.


### 2. Identity, dedup and integrity

Run `dedup_check.py` with resolved DOI/PMID/title and the explicit instance.
For an assigned existing filename, its own match is expected. A different target,
contradictory identity or requested rename requires a source-backed decision before
`start`. Never silently rebind an active job. Bulk dispatch uses validated identities
from `validate_identifiers.py --batch … --recover`; validation is not authorization.
Check primary records for retraction, withdrawal and corrections; distinguish a
commentary from an erratum. Keep a prominent scientific warning for retracted work.
A complete matching primary record can resolve a secondary-index outage; never
substitute a different version silently.

### 4. Sources and manuscript reading

Resolve identity and deduplicate, then `start` the canonical paper path. On refresh,
call `sources` without inputs first to reuse verified archived originals only. A changed DOI/version needs source-backed reconciliation; never
rewrite source identity to make it fit. Historical products remain archived and are
not drafting or review context.

For a new paper use existing acquisition helpers and applicable source references.
For an observed metadata, PDF, XML or HTML URL, use `fetch_source.py` from
`references/script-commands.md`; use `fetch_fulltext.py` for its supported discovery
routes. Run the named helper directly, then read its returned file with the file
reader (or the documented XML/PDF reader). Do not assemble routine retrieval from
inline Python, interpreter heredocs, dynamically executed code, or compound
shell/download/parser commands. Keep downloads and inspection as separate tool
calls. If no existing helper covers a needed operation, report the gap or use an
already-authorized browser/source tool; do not hide a rejected command in a new
script or broaden approval settings. A permission denial remains a denial.
Retain the original manuscript PDF when available; readable publisher XML/HTML
may assist reading. When using `fetch_fulltext.py`, supply `--evidence-dir`
outside the brain. Validate retrieved candidates against the article, not a
helper success label; do not redownload sources already retained and verified.
Record unavailable source/attachment retrieval as an external retention gap. Use
the shared 120-second attachment budget and at most two observed URLs per item;
prefer publisher-advertised links to guessed paths. Challenge HTML is not a PDF.
Once the budget ends, continue the manuscript page and report outstanding originals. Retain obtained
supplements and alternative/composite PDFs without processing. Choose exactly one
manuscript; when only a composite is available, supply explicitly verified physical
manuscript page boundaries. Filenames do not establish identity or boundaries.
A missing essential manuscript returns needs-input; do not fabricate a full ingest
from an abstract or silently replace an available source after a parsing failure.

Supply acquired paths, roles and source-backed identity basis to `sources`; safe
storage keys and hashes are generated. Read the manuscript using the returned
source ID and physical pages. Follow `next_start` for long pages until complete.
Scanned/deficient pages need specific inspection or an available faithful text
source. A short excerpt or prior page is not the full manuscript.


### 5. Draft and factual check

Write a complete fresh manuscript synthesis, then check central claims against
retained evidence: entities/classes, key numbers, denominators, units/exponents,
table columns, experimental conditions and causal claims versus hypotheses.
Do not introduce findings from other papers or later studies from memory; keep
Analysis grounded in this manuscript and clearly distinguish interpretation.
Publisher navigation, recommended/citing articles and page footers are not part of
the manuscript evidence even when retained in its HTML text.
Correct, qualify or omit unsupported claims. Preserve internal source discrepancies
explicitly when consequential. Ambiguous printed glyphs or implausible doses may
need a bounded visual inspection; another text model cannot verify a printed unit.

Use lightweight `[P4:L12-L15]` locators on consequential claims. They refer to the
numbered manuscript text, not truth certificates. For a body alias use the returned
source ID: `[s-<24-hex-digits>/P1:L2-L5]`. Put locators outside the Abstract section;
quote the abstract verbatim. Missing/unresolved locators warn, never trigger retries
or extra staging rounds. Once science is ready, leave optional locator warnings in
the external evidence; do not spend a revision making the warning count zero.

Write annotated Markdown externally and call `stage` with `markdown_path` and a
short substantive `review_note`. Use `HOLD: <material issue>` only for unresolved
material science. No coverage matrix or rigid scientific review schema.

A configured independent fast checker receives the manuscript and fresh draft,
without old pages or graph context. The runtime dispatches it once per job, retaining
free-text findings externally. On `factual-review-pending`, read those findings,
verify each proposed fix against the source, and stage once more with minimal
corrections or a reasoned disposition in the review note. No second checker call,
style debate, or regeneration. Remaining material uncertainty is qualified, omitted,
or held for that paper. A failed/empty/truncated check is explicitly incomplete,
not a clean verdict; useful partial findings can still be assessed. Do not retry it.

### 6. Scientific page composition

Use this structure, not a sibling or legacy page:

    # Exact verified paper title
    ## Abstract
    Verbatim canonical abstract, or an explicit statement that none is provided.
    ## Context
    Scientific question and motivation.
    ## Approach
    Study design and methods needed to understand the findings.
    ## Findings
    Specific manuscript-supported results; distinguish observation and interpretation.
    ## Limitations
    Scientific limitations and concise claim-relevant uncertainties.
    ## Analysis
    What the results establish and what they leave open.
    ## Citation
    Complete bibliographic citation with source author names and identifiers.

Regenerate frontmatter from the verified source and
`../../conventions/frontmatter.md` (not another page): stable `slug`,
`kind: paper`, title, DOI (explicit null only when verified absent), other verified
identifiers, year, venue, status, tags, `fulltext_source`, and complete
ordered `author_names`. Optional `importance` is a number from 0 to 1; omit it
when program relevance is uncalibrated, never use labels such as "minor". Start `authors: []` and `links: []` unless a relationship
is independently established from current evidence; name-only matches are unsafe.
Do not read the author ledger as a routine drafting step. Runtime owns `cited_by`
and `needs-ingest` transitions. Do not copy old provenance counters or stub metadata.

There is no Ingest log. No hashes, job IDs, request history, pending-task lists,
figures, source files, source-packages directory or JSON sidecars belong in the page.
Code appends one compact `Article archive:` locator. Sources, review notes, exact
URLs and machine records remain external. The Abstract and science should be useful
without reading execution history. No abstract-only success for this workflow.

### 7. Publication and follow-up

Fix page-owned structural omissions reported by stage. `graph_follow_up` is deferred;
do not repair the graph before publication. Call `publish` once for the chosen ready
revision. It verifies archive readback before guarded application, verifies canonical
identity, records one propagation event, and completes the page. Missing associations
and targets travel with the existing propagation event for later maintenance.

Archive or metadata outages retain the same revision for a later retry. Do not
sleep-loop, restart drafting, or manually append events. Concurrent edits hold the
item for explicit reconciliation. Complete means the scientific page and retained
archive bytes are published; it does not certify all advertised attachments were
acquired. Report `source_retention` and known gaps separately.

Run the frontmatter linter once for closeout and follow `skills/git-ops/SKILL.md`
for owned changes under repository authorization. Campaign publication does not
perform Git closeout itself. Preserve unrelated edits. Return page/job/revision,
changed paths, scientific/access limitations, factual-check status, attachment gaps,
and deferred graph/Git work. No automatic backlog drain follows a single request.
