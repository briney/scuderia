# Author identity and ledger mutation

Load for `paper-ingest` Phase 8, including parent-owned wiring after a page-only
fill. `skills/conventions/author-ledger.md` owns ledger schema and promotion;
this reference owns the shared mutation procedure. It also serves queue drains
and dives; do not copy its algorithms into those callers.

## Resolve authors before writing

1. Obtain the complete individual-author list from the canonical source.
   Preserve display-name diacritics. Collectives are not individual person
   pages; record collective-only authorship when `authors: []` is warranted.
2. Run `skills/paper-ingest/scripts/check_authors.py --ledger
   <brain>/people/_ledger.yaml --people-dir <brain>/people <names...>`.
   The script parses the ledger and compares name-token sets; it does not
   search person-page names independently and is not a final identity verdict.
   Search existing person pages as well, including legacy or promoted authors
   absent from the ledger. Inspect all relevant surname candidates: the script
   displays only the first eight, and its last-token surname heuristic can
   miss particles or source names presented in family-first order.
3. Resolve abbreviated names, punctuation, name order, and same-name collisions
   using ORCID and source affiliations/citation history. A NEW result can miss
   an abbreviated legacy entry; surname equality alone can fuse different
   people. An affiliation change is a reason to investigate, not proof of a
   different identity. A contradictory verified ORCID is a hold/disambiguation
   signal. Never merge on the presence of an ORCID alone.
4. Reuse the exact existing slug for a confirmed identity, even if its spelling
   is nonstandard. Derive genuinely new slugs with `scripts/slugify_name.py`
   relative to paper-ingest. For a verified different person whose base slug
   is occupied, follow the convention's disambiguation rule; do not rename the
   incumbent during ingestion. Flag unresolved collisions for entity-resolution.
   Build `authors:` and the wiring table from the same resolved slug list.
5. Capture ORCIDs from PubMed XML, Europe PMC core author records, and Crossref
   when available. Handle string/object forms of author IDs; union agreeing
   records, hold conflicts, and use null when no verified ORCID is available.
   A junior author's ORCID may appear only in Crossref. Do not infer an ID.

Build parent wiring data from the saved canonical metadata or a re-fetch plus
the page's `authors:` list. Child summaries may be truncated; a log saying
'ORCIDs captured: N' does not contain the IDs. The page and source record are
required inputs, not the summary alone.

## Ownership and branches

One parent owns all shared-file writes during a parallel ingestion campaign.
Children in page-only mode do not edit the ledger, person pages, bibliography
stubs, concepts, or propagation inbox. A standalone ingest owns these writes
itself. Do not interpret a partial instruction such as 'no new ledger entries'
as permission to guess the remaining ownership; assign all branches explicitly.

For each resolved individual author:

- Existing person page: append the paper to `author_on`, preserving existing
  edges; reconcile a leftover ledger entry through the promotion procedure.
- Existing ledger entry: append the paper to `citations` if absent, preserving
  identity and prior citations. Use the existing-entry procedure below.
- New author: append a new ledger entry with slug, source name, verified ORCID
  or null, available affiliations, and the paper citation.
- At five distinct citations, call `enrich`'s promote-from-ledger mode; the
  person page receives all ledger citations and identity data before removal
  of the ledger entry. Verify the page and targeted removal together. Manual
  promotion/demotion and migration exceptions remain in the convention.

The paper citation has one representation: `papers/<slug>`. Use it in both
writer and verifier; the platform linter independently checks this shape.
Never count bibliography stubs as ingested author evidence.

## New-entry append

`skills/paper-ingest/scripts/ledger-append.py` implements new-entry append only.
It does not update citations on existing entries or perform promotion. Copy it
to a uniquely named temporary script, set the actual ledger path and explicit
per-author blocks, then invoke an interpreter with Python >=3.10 and PyYAML.
Do not invoke a heredoc or use `cat >>` on the shared ledger.

The helper locks the resolved ledger path through its deterministic `_lock_path`,
re-reads under the lock, rejects existing slugs, builds a plain-text candidate,
validates it, and publishes through a temporary sibling and `os.replace`.
Use `yaml.safe_load` for validation only; never `safe_dump` the entire ledger.
Validate each proposed slug is a string and every citation has the `papers/`
prefix before calling the helper. An unexpanded `{slug}` can parse as a mapping,
so parse success alone does not establish a valid entry.

The lock coordinates only cooperating local writers. It does not protect
against external editors or sync writes. Stop on detected concurrent changes;
re-read and rebuild from the current file rather than overwriting them.
The helper's printed success is not the final check: independently re-read
and verify the intended slugs and citations after it returns.

## Existing-entry updates and removal

For an individual update under exclusive writer ownership, use a targeted patch
anchored on the entry's unique slug plus distinguishing context. For batch
updates, use one temporary script that holds the same deterministic lock as
ledger-append throughout read, candidate construction, validation, publication,
and read-back. The append helper is not an existing-entry updater; do not claim
it performed this branch.

1. Read the current raw text and parse its top-level `entries` mapping. Support
   existing entry key order and indentation; do not serialize the whole file.
2. Bound the target at its list-item indentation, from that entry's `- ` start
   to the next same-indent entry or EOF. Existing files may use column-zero
   entries, while the convention permits indented entries. Never locate the
   start by walking back to `- name:`: an entry may start with `- citations:`.
3. Add within that entry's `citations` list, matching its indentation. A
   mismatched indent can still YAML-parse while changing the citation value.
   Handle an empty list explicitly rather than searching for a nonexistent
   last citation. Remove an entry only by its fully bounded unique block.
4. For multiple splices, compute offsets against the original string, sort
   descending, and apply once. Recomputing offsets against a changing string
   previously caused runaway growth; do not use a mutation loop with stale
   positions. Preserve all unaffected bytes and comments.
5. Validate the candidate before publication: schema, unique string slugs,
   expected membership for each targeted author, and unchanged citations for
   all untargeted entries. The same paper may legitimately appear under many
   coauthors; do not require it to be absent from every other ledger entry.
6. Publish only while writer ownership still holds, then re-read and repeat
   the checks. Never restore the entire shared ledger from Git after failure;
   preserve current bytes and recover only proven damaged entries after
   accounting for concurrent edits (`skills/git-ops/SKILL.md`).

## Final verification

Verify every paper-author pair against `author_on` or ledger `citations`, not
merely that its slug resolves. Check all touched entries for duplicate slugs,
string types, prefix shape, and identity consistency. Review potential
same-person duplicates under spelling/initial variants before merging.
Run scoped `lint-frontmatter.py` on the paper, ledger, and touched person pages;
read its output and respect the exit status. A command pipeline that hides the
linter failure is not validation. Full paper verification follows Phase 10.
