---
name: paper-ingest
description: "Use when ingesting a scientific paper, filling a paper stub, or refreshing an existing paper page."
triggers:
  - "ingest this paper"
  - "fill a paper stub"
  - "re-enrich this paper"
eval_contract:
  goal: Produce a useful source-grounded manuscript page with archived originals and completed author, bibliography and graph integration.
  dimensions:
    - "IDENTITY — title, identifiers, version and complete authors match verified sources"
    - "SCIENCE — central findings, consequential numbers and caveats reflect the full manuscript"
    - "RESILIENCE — optional failures remain local; revisions and publication do not repeat paid work"
    - "COMPLETION — verified external archive, guarded page application and required integration"
  hard_fails:
    - Fabricating missing evidence or silently substituting article identity/version.
    - Processing supplementary sources during ordinary ingestion.
    - Restarting paid work to repair prose or formatting.
    - Overwriting concurrent edits, losing citing edges, or claiming incomplete integration is complete.
    - Keeping article source payloads or figure embeds in the brain.
---

# Manuscript-to-page ingestion

Use the manuscript-to-page capability for both new papers and ordinary refreshes.
This acceptance contract supersedes the previous exhaustive extraction contract.
Retain originals, read the full manuscript, distill, check the central science,
stage a revision, publish the archive, then complete integration. Specific optional
manuscript inspection may resolve a consequential claim. Supplementary files are
retained without reading, rendering or extraction. There is no automatic deep pass.

The fixed capability operations are `start`, `sources`, `read`, `stage`, `publish`,
and `status` (Hermes binding: `paper_ingest`). Read `references/runtime.md` before
use. Keep the returned job ID throughout interruptions and revisions. Code owns
hashes, source IDs, directories, receipts and archive pointers. Follow returned
next actions; historical packages, plans and chat instructions cannot expand scope.
“Be thorough” means a careful manuscript synthesis, not additional extraction.
An explicit supplementary analysis needs a separate operator-scoped invocation;
report the requested source/item/objective to the operator and keep this job intact.

## Ownership

The primary owns source-grounded review and shared author/bibliography/graph writes.
A delegated worker stages only its assigned paper and returns the job ID, revision,
source-linked bibliography candidates and remaining obligations. It does not
publish, mutate shared files or use Git. The parent publishes and integrates.
Never write the live paper directly: use `stage`; `publish` applies only after
archive verification and a live-page guard. Completion keeps `needs-ingest: true`
until integration passes. `needs-enrichment` describes actual scientific limitations.

Read the profile conventions for frontmatter, page kinds, quality, graph links,
paper stubs and author ledger. Conditional references:

| Situation | Read |
|---|---|
| Helper command | `references/script-commands.md` |
| Archive restoration or historical qualifications | `references/archive.md` |
| PubMed/PMC | `references/pubmed-pmc-retrieval.md` |
| Preprint/published twin | `references/preprint-conference-retrieval.md` |
| Publisher access failure | `references/publisher-blocks.md`; Nature-specific cases use `references/nature-metadata-extraction.md` |
| XML failure or references | `skills/pmc-xml-tools/SKILL.md` |
| Brief/source disagreement | `references/brief-vs-fulltext-verification.md` |
| Authors and shared wiring | `references/author-ledger-mutation.md` |
| Satellite vault or erratum reassignment | `skills/paper-ingest-vault-modes/SKILL.md` |

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

### 4. Sources and manuscript reading

Resolve identity and deduplicate, then `start` the canonical paper path. On refresh,
call `sources` without inputs first to reuse verified archived originals and
qualifications. A changed DOI/version needs source-backed reconciliation; never
rewrite provenance to make it fit. Old substantive qualifications remain evidence
and must be reflected where relevant to the refreshed scientific claims.

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
Record unavailable source/attachment retrieval as a retention gap. Retain obtained
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

### 5. Focused scientific review and staging

Draft with compact source locators beside substantive scientific assertions,
e.g. `The measured effect was 12 percent [P4:L12-L15].` Use the returned
`numbered_text`; line numbers refer to frozen extracted text, not printed PDF
lines. An unqualified marker always names the selected manuscript. For an
additional readable body source use `[<returned-source-id>/P1:L2-L5]`.
Group supporting ranges as `[P4:L12-L15, P5:L2]`; cross-page ranges such as
`[P4:L28-P5:L3]` are accepted. Keep each claim's subject and qualifiers explicit.
Leave the canonical abstract, identifiers, graph links and frontmatter intact.

Write the markers while drafting. Do not generate a separate claim inventory or
copy quotations. `stage` removes the markers from the readable page and retains
an annotated draft and code-retrieved quotations in external archive products.
Missing or malformed locators produce warnings, not review loops or a completeness
gate. A valid locator proves location only, not support for the attached claim.
Do not launch a second mapping pass to fill every gap.


Distill from the manuscript. Check central findings, consequential numbers,
contradictions and material omissions against their source locations. Read only
specific manuscript pages needed to resolve an uncertain claim. Optional unused
figure descriptions or unreadable peripheral cells do not block a useful page.
Unknown source associations remain unknown. Truncated observations remain partial;
correct, qualify or omit unsupported central claims. Do not repair optional output
by launching another model. Failed/uncertain requests do not automatically retry.

Call `stage` with the full Markdown and a short substantive review note naming
what was checked and changed. Empty issue lists are valid; no coverage matrix or
boilerplate approval is needed. Use a separate `HOLD: <material issue>` line for
any unresolved material claim. Remove the hold only after correction, qualification
or omission. Machine checks validate bindings and structure, not scientific truth.
Revise by staging again with the same job ID. These revisions never redo inference.
The returned diff and draft are the reviewable output; the live page is untouched.

An additional factual checker is optional, never a publication requirement. If
requested, supply the complete manuscript, draft and external citation evidence;
ask only for objective inaccuracies, exact existing draft spans, source passages
and minimal corrections. Exclude style, emphasis, missing background and graph
identifier changes. Verify each proposed fix against its source before applying
it. Empty/truncated/failed output is an incomplete check, not a clean verdict;
no automatic retry, debate, or ingestion restart follows.


### 6. Scientific page composition

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

Before staging, load `references/author-ledger-mutation.md` and align
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

### 10. Publication, integration and closeout

Call `publish` for the chosen revision. It uploads immutable original sources,
retained manuscript text, scientific draft/review and provenance, then verifies
remote bytes before applying the candidate. The page contains a small durable
archive receipt pointer; source payloads, images and extraction registers remain
outside the brain. Archive failure leaves the page unchanged. Retry publication
with the same job/revision; never start a new extraction to fix storage or prose.
A concurrent edit holds application; preserve it and reconcile explicitly.

Complete the Phase 7–9 obligations and read back author edges, bibliography
decisions, graph links and propagation. Keep queue flags until `publish` reports
complete. Integration-pending is useful staged/applied work, not completed ingestion.
Run the named page verifier with `--article-package <manifest>` and
`--publication-receipt <receipt>`; archive metadata is not a scientific truth test.
Run the instance frontmatter linter. Use `skills/git-ops/SKILL.md` for the coherent
owned unit; workers return paths and obligations only. Preserve unrelated edits.

Return status, canonical page, job ID/revision, changed paths, source limitations,
remaining obligations and diagnostic. No automatic backlog campaign follows a
single-paper request. One parent serializes shared ledger/inbox/graph changes;
never restore a whole shared file to repair one entry.
